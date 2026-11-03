import { useParams } from 'react-router'
import { api } from '../../lib/api'
import { useEffect, useState } from 'react'
import type { VenueEventResponse, VenueResponse } from '../events/types'
import PageLayout from '../../components/PageLayout'
import GoogleMap from '../../components/GoogleMap'

import EventListItem from '../../components/EventListItem'
import Markdown from '../../components/Markdown'

export default function VenuePage() {
  const { id } = useParams<{ id: string }>()

  const [venue, setVenue] = useState<VenueResponse | undefined>(undefined)

  useEffect(() => {
    const getVenue = async (): Promise<void> => {
      const res = await api.get<VenueResponse>(`/venues/${id}`);
      setVenue(res.data);
    }

    getVenue();
  }, [])

  return (
    <PageLayout
      title={venue?.display_name}
      fallbackTitle="Venue"
      back={{ to: '/events' }}
    >
      {venue && (
        <div>
          <span className="text-2xl font-semibold block">Venue owned by{" "}<a className="link link-primary" href={`/organization/${venue?.organization.id}`}>{venue.organization.display_name}</a>
          </span>
          <div className="mt-2">
            <div className="flex lg:flex-row flex-col gap-8">
              <div className="flex-1">
                <h3 className="font-semibold text-xl text-secondary">Description</h3>
                <Markdown content={venue.description} />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-xl"><span className="text-secondary">Location:</span> {venue.location_name}</h3>
                {venue.location_coords ? (
                  <GoogleMap latitude={venue.location_coords.lat} longitude={venue.location_coords.long} />
                ) : (
                  <p>not valid location</p>
                )}
              </div>
            </div>

            <h3 className="mt-8 font-semibold text-xl text-secondary">Upcoming Events</h3>
            {venue.events.length > 0 ? (
              <div>
                <p className="text-base-content/70">{venue.events.length} event(s) at this venue.</p>

                <ul className="list">
                  {venue.events.map((event: VenueEventResponse) =>
                    <EventListItem event={event} />
                  )}
                </ul>
              </div>
            ) : (
              <p className="text-base-content/70">No upcoming events.</p>
            )}
          </div>
        </div>
      )
      }
    </PageLayout >
  )
}
