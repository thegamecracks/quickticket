import { useNavigate, useParams } from 'react-router'
import { useState, useEffect } from 'react'
import type { EventResponse } from './types'
import { formatDateLong, calcTimeMediumRange } from '../../lib/general'
import { getMockTicketCount } from '../../lib/mocks'
import { api } from '../../lib/api'
import NavigateBackBtn from '../../components/NavigateBack'
import SkeletonImage from '../../components/SkeletonImage'

import MarkdownIt from 'markdown-it'
import GoogleMap from '../../components/GoogleMap'

export default function EventDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [event, setEvent] = useState<EventResponse | undefined>(undefined)
  const navigate = useNavigate();
  const md = new MarkdownIt();

  useEffect(() => {
    const getEvents = async (): Promise<void> => {
      const res = await api.get<EventResponse>(`/events/${id}`);
      console.log(res.data);
      setEvent(res.data);
    }

    getEvents();
  }, [])

  const handleCheckoutClick = () => {
    navigate(`/events/${id}/checkout`)
  }

  const handleVenueClick = () => {
    navigate(`/venue/${event?.venue.id}`)
  }


  return (
    <section className="mx-auto w-full max-w-7xl grow px-4 py-12">
      <NavigateBackBtn />
      {event && (
        <div className="mx-auto max-w-6xl mt-2">
          <figure>
            {/* TODO: resolve StorageObjectRef -> image URL once backend serves storage */}
            <SkeletonImage
              src={event.thumbnail ? `/storage/${event.thumbnail.id}` : 'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event'}
              alt={event.display_name}
              className="h-48 w-full object-cover"
            />
          </figure>

          <h1 className="mb-4 text-3xl font-bold mt-2">{event.display_name}</h1>

          <div className="flex lg:flex-row flex-col">
            <div className="flex-1">
              <h3 className="font-semibold text-xl">Description</h3>
              <div dangerouslySetInnerHTML={{ __html: md.render(event.description) }} />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-xl">
                <button className="btn btn-primary" onClick={() => handleVenueClick()}>Venue</button> Location: {event.venue.location_name}
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

    </section >
  )
}
