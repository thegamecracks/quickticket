import { Link, useNavigate, useParams } from 'react-router'
import { useState, useEffect } from 'react'
import type { EventResponse } from './types'
import { formatDateLong, calcTimeMediumRange } from '../../lib/general'
import { getMockTicketCount } from '../../lib/mocks'
import { api } from '../../lib/api'
import PageLayout from '../../components/PageLayout'
import Markdown from '../../components/Markdown'
import SkeletonImage from '../../components/SkeletonImage'

import GoogleMap from '../../components/GoogleMap'

export default function EventDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [event, setEvent] = useState<EventResponse | undefined>(undefined)
  const navigate = useNavigate();

  useEffect(() => {
    const getEvent = async (): Promise<void> => {
      const res = await api.get<EventResponse>(`/events/${id}`);
      console.log(res.data);
      setEvent(res.data);
    }

    getEvent();
  }, [])

  const handleCheckoutClick = () => {
    navigate(`/events/${id}/checkout`)
  }

  return (
    <PageLayout
      title={event?.display_name}
      fallbackTitle="Event"
      back={{ to: '/events' }}

    >
      {event && (
        <div className="mt-2">
          <figure>
            <SkeletonImage
              src={event.thumbnail ? `/storage/${event.thumbnail.id}` : 'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event'}
              alt={event.display_name}
              className="h-48 w-full object-cover"
            />
          </figure>

          <div className="flex lg:flex-row flex-col mt-4">
            <div className="flex-1 space-y-4">
              <h3 className="font-semibold text-xl">Description</h3>
              <Markdown content={event.description} />
            </div>
            <div className="flex-1 space-y-4">
              <h3 className="font-semibold text-xl">
                <span className="text-2xl font-semibold block">
                  Location{" "}
                  <Link className="link link-primary" to={`/venue/${event.venue.id}`}>{event.venue.location_name}</Link>
                </span>
              </h3>
              {event.venue.location_coords ? (
                <GoogleMap latitude={event.venue.location_coords?.lat} longitude={event.venue.location_coords?.long} />
              ) : (
                <p>not valid location</p>
              )}
            </div>

          </div>
          {/* Event information */}
          <p>{formatDateLong(event.starts_at)}</p>
          <p>{calcTimeMediumRange(event.starts_at, event.ends_at)}</p>

          {/* Price and availability */}
          <div className="mt-4 flex flex-wrap items-center justify-end gap-2">

            {/* TODO: replace with actual ticket count to check against max attendees */}
            {event.max_attendees >= getMockTicketCount(event.id) !== false ? (
              <span className="badge badge-primary">
                ${event.ticket_price.amount} {event.ticket_price.currency}
              </span>
            ) : (
              <span className="badge badge-error">
                Sold Out
              </span>
            )}
            <button className="btn btn-primary" onClick={() => handleCheckoutClick()}>Checkout</button>
          </div>
        </div>
      )
      }

    </PageLayout>
  )
}
