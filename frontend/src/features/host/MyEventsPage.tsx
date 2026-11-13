
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import PageLayout from '../../components/PageLayout'
import EventCard from '../../components/EventCard'
import { Pagination, safePage } from '../../components/Pagination'

import { useAuth } from '../../lib/auth'
import type { EventResponse } from '../events/types'

import {
  getMockAllEvents,
  getMockVenue,
  getMockOrganizationsForAccount,
} from '../../lib/mocks'

// Return events belonging to the logged-in user's organizations.
// Uses existing mock data until backend integration is completed.
function getOrganizerEvents(accountId: string): EventResponse[] {
  const organizations = getMockOrganizationsForAccount(accountId)

  const organizationMap = new Map(
    organizations.map(org => [org.id, org])
  )

  return getMockAllEvents().flatMap((event): EventResponse[] => {
    const venue = getMockVenue(event.venue_id)

    if (!venue) return []

    const organization = organizationMap.get(venue.organization_id)

    // Exclude events belonging to other organizers.
    if (!organization) return []

    return [{
      id: event.id,
      created_at: event.created_at,
      display_name: event.display_name,
      description: event.description,
      theme: event.theme,
      thumbnail: null,
      banner: null,
      starts_at: event.starts_at,
      ends_at: event.ends_at,
      ticket_price: event.ticket_price,
      max_attendees: event.max_attendees,
      tickets: [],
      venue: {
        id: venue.id,
        created_at: venue.created_at,
        display_name: venue.display_name,
        description: venue.description,
        theme: venue.theme,
        thumbnail: null,
        banner: null,
        location_name: venue.location_name,
        location_coords: venue.location_coords,
        organization: {
          id: organization.id,
          created_at: organization.created_at,
          display_name: organization.display_name,
        },
      },
    }]
  })
}

export default function MyEventsPage() {
  const { user } = useAuth()

  const [searchParams, setSearchParams] = useSearchParams()
  const [currentPage, setCurrentPage] = useState(1)

  // Reset pagination when the logged-in user changes.
  useEffect(() => {
    setCurrentPage(1)
  }, [user?.id])

  // Get events for the logged-in account only.
  const myEvents = user
    ? getOrganizerEvents(user.id)
    : []

  const search = searchParams.get('search') ?? ''

  const filteredEvents = myEvents.filter(event => {
    const searchText = search.trim().toLowerCase()

    return (
      event.display_name.toLowerCase().includes(searchText) ||
      event.description.toLowerCase().includes(searchText)
    )
  })

  // Pagination
  const eventsPerPage = 6
  const totalPages = Math.ceil(
    filteredEvents.length / eventsPerPage
  )

  const page = safePage(currentPage, totalPages)

  const paginatedEvents = filteredEvents.slice(
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
          {filteredEvents.length > 0 && (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {paginatedEvents.map(event => (
                <EventCard
                  key={event.id}
                  event={event}
                />
              ))}
            </div>
          )}

          {/* No matching search results */}
          {filteredEvents.length === 0 && search.trim() && (
            <div className="rounded-xl border border-base-300 bg-base-200 p-8 text-center">
              <p className="text-base-content/70">
                No matching events found.
              </p>
            </div>
          )}

          {/* No events created */}
          {myEvents.length === 0 && !search.trim() && (
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
