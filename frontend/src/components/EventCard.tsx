import type { EventResponse } from "../features/events/types"
import { getMockTicketCount, getMockVenue } from "../lib/mocks"
import SkeletonImage from "./SkeletonImage"
import { calcTimeMediumRange, formatDateLong } from "../lib/general"
import { useNavigate } from "react-router"

type EventCardProps = {
  event: EventResponse
}

export default function EventCard({ event }: EventCardProps) {
  const navigate = useNavigate();

  const handleViewEvent = () => {
    navigate(`/events/${event.id}`)
  }

  return (
    <div className="card overflow-hidden border border-base-300 bg-base-200 shadow-sm">

      {/* Event image */}
      <figure>
        {/* TODO: resolve StorageObjectRef -> image URL once backend serves storage */}
        <SkeletonImage
          src={event.thumbnail ? `/storage/${event.thumbnail.id}` : 'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event'}
          alt={event.display_name}
          className="h-48 w-full object-cover"
        />
      </figure>

      <div className="card-body">

        {/* Event name */}
        <h2 className="card-title">{event.display_name}</h2>

        {/* Event information */}
        <p>📅 {formatDateLong(event.starts_at)}</p>
        <p>{calcTimeMediumRange(event.starts_at, event.ends_at)}</p>
        <p>📍 {event.venue.display_name}</p>

        {/* Price and availability */}
        <div className="mt-4 flex items-center justify-between gap-2">

          <div className="">
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
          </div>
          <button className="btn btn-primary justify-self-end" onClick={() => handleViewEvent()}>View Event</button>

        </div>
      </div>
    </div>
  )
}
