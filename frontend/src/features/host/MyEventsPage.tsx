
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import PageLayout from '../../components/PageLayout'
import EventCard from '../../components/EventCard'
import { Pagination, safePage } from '../../components/Pagination'

import { useAuth } from '../../lib/auth'
import { api } from '../../lib/api'
import type { EventResponse } from '../events/types'

export default function MyEventsPage() {
  const { user } = useAuth()

  const [searchParams, setSearchParams] = useSearchParams()
  const [currentPage, setCurrentPage] = useState(1)
  const [events, setEvents] = useState<EventResponse[] | undefined>(undefined)

  useEffect(() => {
    const getEvents = async (orgId: string | undefined): Promise<void> => {
      const res = await api.get<{ items: EventResponse[] }>(`/events?organization_id=${orgId}`)
      setEvents(res.data.items)
    }

    // Reset pagination when the logged-in user changes.
    setCurrentPage(1)
    // have to get all organization_id by organization_members item's account_id = user.id 
    // only want one organization_id though since we have 1-1 user to organization 
    const orgId = user?.organization_members[0].organization_id;
    getEvents(orgId);

  }, [user?.id])


  const search = searchParams.get('search') ?? ''

  const filteredEvents = events?.filter(event => {
    const searchText = search.trim().toLowerCase()

    return (
      event.display_name.toLowerCase().includes(searchText) ||
      event.description.toLowerCase().includes(searchText)
    )
  })

  // Pagination
  const eventsPerPage = 6
  const totalPages = Math.ceil(
    filteredEvents ? filteredEvents.length / eventsPerPage : 0
  )

  const page = safePage(currentPage, totalPages)

  const paginatedEvents = filteredEvents?.slice(
    (page - 1) * eventsPerPage,
    page * eventsPerPage
  )

  const handleSearch = (value: string) => {
    const nextParams = new URLSearchParams(searchParams)

    if (value) {
      nextParams.set('search', value)
    } else {
      nextParams.delete('search')
    }

    setSearchParams(nextParams, { replace: true })
    setCurrentPage(1)
  }

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

      {/* Organizer's event listing */}
      {user && (
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
            onChange={e => handleSearch(e.target.value)}
          />

          {/* Existing event cards */}
          {filteredEvents && filteredEvents.length > 0 && (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {paginatedEvents?.map(event => (
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
          {totalPages > 1 && (
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onChangePage={setCurrentPage}
            />
          )}

        </div>
      )}

    </PageLayout>
  )
}
