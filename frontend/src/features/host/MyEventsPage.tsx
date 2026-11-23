import { useEffect } from 'react'
import { Link, useSearchParams } from 'react-router'
import { useInfiniteQuery } from '@tanstack/react-query'

import PageLayout from '../../components/PageLayout'
import EventCard from '../../components/EventCard'
import { Pagination, safePage } from '../../components/Pagination'

import { useAuth } from '../../lib/auth'
import { api } from '../../lib/api'
import { PAGE_SIZE, type Paged } from '../../lib/pagination'
import type { EventResponse } from '../events/types'

export default function MyEventsPage() {
  const { user } = useAuth()

  const [searchParams, setSearchParams] = useSearchParams()
  const search = searchParams.get('search') ?? ''

  // have to get all organization_id by organization_members item's user_id = user.id
  // only want one organization_id though since we have 1-1 user to organization
  const orgId = user?.organization_members[0]?.organization_id

  // Cursor-paginated fetch of this organizer's events (GET /events?organization_id=).
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetching,
    isLoading,
    isError,
    refetch,
  } = useInfiniteQuery({
    queryKey: ['events', 'mine', orgId],
    enabled: orgId !== undefined,
    queryFn: ({ pageParam }) =>
      api
        .get<Paged<EventResponse>>('/events', {
          params: {
            limit: PAGE_SIZE,
            next: pageParam,
            organization_id: orgId,
          },
        })
        .then((res) => res.data),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next,
  })

  // The numbered Pagination UI below needs the full list, so drain every
  // page up front. safePage() clamps the URL page if the list shrinks.
  useEffect(() => {
    if (hasNextPage && !isFetching && !isError) {
      void fetchNextPage()
    }
  }, [hasNextPage, isFetching, isError, fetchNextPage])

  const events = data?.pages.flatMap((page) => page.items)

  const filteredEvents = events?.filter((event) => {
    const searchText = search.trim().toLowerCase()

    return (
      event.display_name.toLowerCase().includes(searchText) ||
      event.description.toLowerCase().includes(searchText)
    )
  })

  // Pagination: page number lives in the URL (?page=) so it survives
  // refreshes and the back button.
  const totalPages = Math.ceil(
    filteredEvents ? filteredEvents.length / PAGE_SIZE : 0
  )

  const rawPage = Number(searchParams.get('page') ?? '1')
  const page = safePage(Number.isFinite(rawPage) ? rawPage : 1, totalPages)

  const setPage = (nextPage: number) => {
    const nextParams = new URLSearchParams(searchParams)

    if (nextPage > 1) {
      nextParams.set('page', String(nextPage))
    } else {
      nextParams.delete('page')
    }

    setSearchParams(nextParams, { replace: true })
  }

  const handleSearch = (value: string) => {
    const nextParams = new URLSearchParams(searchParams)

    if (value) {
      nextParams.set('search', value)
    } else {
      nextParams.delete('search')
    }

    // Return to page 1 on a new search
    nextParams.delete('page')

    setSearchParams(nextParams, { replace: true })
  }

  const paginatedEvents = filteredEvents?.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE
  )

  return (
    <PageLayout title="My Events">

      {/* Authentication loading state */}
      {user === undefined && (
        <p className="text-base-content/70">
          Checking your account...
        </p>
      )}

      {/* Sign-in required */}
      {user === null && (
        <div className="rounded-lg bg-base-200 p-6">
          <h2 className="text-lg font-semibold">
            Sign In Required
          </h2>

          <p className="mt-2 text-base-content/70">
            Please sign in to view your organized events.
          </p>
        </div>
      )}

      {/* TODO: redirect user to the create-an-organization page if orgId is missing */}
      {user && orgId === undefined && (
        <div className="rounded-xl border border-base-300 bg-base-200 p-8 text-center">
          <p className="text-base-content/70">
            Create an organization to start hosting events.
          </p>
        </div>
      )}

      {/* Organizer's event listing */}
      {user && orgId !== undefined && (
        <div className="space-y-6">

          {/* Create Event action */}
          <div className="flex justify-end">
            <Link
              to="/createEvent"
              className="btn btn-primary"
            >
              + Create Event
            </Link>
          </div>

          {/* Search */}
          <input
            type="text"
            placeholder="Search my events..."
            aria-label="Search my events"
            className="input input-bordered w-full"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
          />

          {/* First page is still loading */}
          {isLoading && (
            <p className="text-base-content/70">
              Loading your events...
            </p>
          )}

          {/* Loading failed */}
          {isError && (
            <div className="rounded-xl border border-base-300 bg-base-200 p-8 text-center">
              <p className="text-base-content/70">
                Failed to load your events.
              </p>
              <button
                type="button"
                className="btn btn-primary mt-4"
                onClick={() => void refetch()}
              >
                Try again
              </button>
            </div>
          )}

          {/* Existing event cards */}
          {filteredEvents && filteredEvents.length > 0 && (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {paginatedEvents?.map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                />
              ))}
            </div>
          )}

          {/* No matching search results */}
          {filteredEvents && filteredEvents.length === 0 && search.trim() && (
            <div className="rounded-xl border border-base-300 bg-base-200 p-8 text-center">
              <p className="text-base-content/70">
                No matching events found.
              </p>
            </div>
          )}

          {/* No events created */}
          {events && events.length === 0 && !search.trim() && (
            <div className="rounded-xl border border-base-300 bg-base-200 px-6 py-12 text-center">
              <h2 className="text-xl font-semibold">
                No Events Yet
              </h2>

              <p className="mt-2 text-base-content/70">
                You haven't created any events yet.
              </p>

              <Link
                to="/createEvent"
                className="btn btn-primary mt-5"
              >
                Create Your First Event
              </Link>
            </div>
          )}

          {/* Pagination */}
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onChangePage={setPage}
          />

        </div>
      )}

    </PageLayout>
  )
}
