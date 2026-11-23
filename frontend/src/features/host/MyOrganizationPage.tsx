import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import PageLayout from '../../components/PageLayout'
import SkeletonImage from '../../components/SkeletonImage'
import { api } from '../../lib/api'
import { useAuth } from '../../lib/auth'
import { isAdministrator } from '../account/types'
import type { OrganizationResponse } from '../organizations/types'

/**
 * The signed-in organizer's own organization: its venues (with a link to
 * edit each) and every event held at them.
 */
export default function MyOrganizationPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  // A user owns at most one organization; any administrator membership is it.
  const orgId = user?.organization_members.find(isAdministrator)?.organization_id

  const [org, setOrg] = useState<OrganizationResponse | undefined>(undefined)
  const [loadError, setLoadError] = useState(false)

  useEffect(() => {
    if (!orgId) return

    let active = true

    api
      .get<OrganizationResponse>(`/organizations/${orgId}`)
      .then(response => {
        if (active) setOrg(response.data)
      })
      .catch(() => {
        if (active) setLoadError(true)
      })

    return () => {
      active = false
    }
  }, [orgId])

  const events = org?.venues.flatMap(venue =>
    venue.events.map(event => ({ event, venue })),
  )

  const handleViewVenue = (id: string) => navigate(`/venue/${id}`)
  const handleViewEvent = (id: string) => navigate(`/events/${id}`)

  return (
    <PageLayout
      title={org?.display_name}
      fallbackTitle="My Organization"
      actions={
        org && (
          <Link
            to={`/organization/${org.id}/edit`}
            className="btn btn-primary"
          >
            Edit Organization
          </Link>
        )
      }
    >
      {/* Authentication loading state */}
      {user === undefined && (
        <p className="text-base-content/70">
          Checking your account...
        </p>
      )}

      {/* No sign-in gate: a signed-out visitor uses the navbar's Sign in
          button; losing auth mid-session raises the global toast instead. */}

      {/* No organization yet */}
      {user && !orgId && (
        <div className="rounded-xl border border-base-300 bg-base-200 px-6 py-12 text-center">
          <h2 className="text-xl font-semibold">
            No Organization Yet
          </h2>

          <p className="mt-2 text-base-content/70">
            You haven't created an organization yet.
          </p>

          {/* TODO: a later PR wires the creation flow (creating an event with
              no organization pops this form, then the venue form, then the
              event form). Until then, offer a direct link. */}
          <Link to="/createOrganization" className="btn btn-primary mt-5">
            Create Your Organization
          </Link>
        </div>
      )}

      {/* Loading failed */}
      {orgId && loadError && (
        <div role="alert" className="alert alert-error">
          Unable to load your organization. Please try again later.
        </div>
      )}

      {/* Loading */}
      {orgId && !org && !loadError && (
        <p className="text-base-content/70">
          Loading your organization...
        </p>
      )}

      {org && (
        <div className="space-y-10">
          {/* Venues */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Venues</h2>

            {org.venues.length === 0 ? (
              <p className="text-base-content/70">
                No venues have been added to this organization yet.
              </p>
            ) : (
              <ul className="list">
                {org.venues.map(venue => (
                  <li className="list-row" key={venue.id}>
                    <figure className="h-20 w-32 shrink-0 overflow-hidden rounded-lg bg-base-300">
                      <SkeletonImage
                        src={venue.thumbnail
                          ? `/storage/${venue.thumbnail.id}`
                          : 'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event'}
                        alt={venue.display_name}
                        className="h-full w-full object-cover"
                      />
                    </figure>

                    <div>
                      {venue.display_name}
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        className="btn btn-ghost"
                        onClick={() => handleViewVenue(venue.id)}
                      >
                        View
                      </button>
                      <Link
                        to={`/venue/${venue.id}/edit`}
                        className="btn btn-primary"
                      >
                        Edit
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Events */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Events</h2>

            {events && events.length === 0 ? (
              <p className="text-base-content/70">
                No events have been held at this organization's venues yet.
              </p>
            ) : (
              <ul className="list">
                {events?.map(({ event, venue }) => (
                  <li className="list-row" key={event.id}>
                    <figure className="h-20 w-32 shrink-0 overflow-hidden rounded-lg bg-base-300">
                      <SkeletonImage
                        src={event.thumbnail
                          ? `/storage/${event.thumbnail.id}`
                          : 'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event'}
                        alt={event.display_name}
                        className="h-full w-full object-cover"
                      />
                    </figure>

                    <div>
                      {event.display_name}
                      <p className="text-xs text-base-content/70">
                        {venue.display_name}
                      </p>
                    </div>

                    {/* TODO: event editing comes in a later PR */}
                    <button
                      className="btn btn-primary"
                      onClick={() => handleViewEvent(event.id)}
                    >
                      View
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </PageLayout>
  )
}
