import type { EventResponse } from "../features/events/types"
import { getMockTicketCount } from "../lib/mocks"
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
    <div className="card h-full flex flex-col overflow-hidden border border-base-300 bg-base-200 shadow-sm">

      {/* Event image */}
      <figure>
        {/* TODO: resolve StorageObjectRef -> image URL once backend serves storage */}
        <SkeletonImage
          src={event.thumbnail ? `/storage/${event.thumbnail.id}` : 'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event'}
          alt={event.display_name}
          className="h-48 w-full object-cover"
        />
      </figure>

      <div className="card-body flex flex-1 flex-col">

        {/* Event name, capped at two lines so every card's body line up */}
        <h2 className="card-title line-clamp-2 min-h-14">{event.display_name}</h2>

        <ul className="space-y-1">
          {/* Event information */}
          <li>{formatDateLong(event.starts_at)}</li>
          <li>{calcTimeMediumRange(event.starts_at, event.ends_at)}</li>
          <li className="line-clamp-1">{event.venue.display_name}</li>
        </ul>

        {/* Price and availability — pinned to the bottom of the card */}
        <div className="mt-auto flex items-center justify-between gap-2 pt-4">

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
          <div className="card-actions justify-end">
            <button className="btn btn-primary" onClick={() => handleViewEvent()}>View Event</button>
          </div>
        </div>
      </div>
    </div>
  )
}
