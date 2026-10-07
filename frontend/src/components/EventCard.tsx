import type { Event } from "../features/events/types"
import { getMockTicketCount, getMockVenue } from "../lib/mocks"
import SkeletonImage from "./SkeletonImage"
import { calcDateLongTimeMediumRange } from "../lib/general"

type EventCardProps = {
  event: Event
}

export default function EventCard({ event }: EventCardProps) {
  return (
    <div className="card overflow-hidden border border-base-300 bg-base-200 shadow-sm">

      {/* Event image */}
      <figure>
        <SkeletonImage
          src={event.thumbnail_url ?? 'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event'}
          alt={event.display_name}
          className="h-48 w-full object-cover"
        />
      </figure>

      <div className="card-body">

        {/* Event name */}
        <h2 className="card-title">{event.display_name}</h2>

        {/* Event information */}
        <p>📅 {calcDateLongTimeMediumRange(event.starts_at, event.ends_at)}</p>
        <p>📍 {getMockVenue(event.venue_id)?.display_name}</p>

        {/* Price and availability */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2">

          <span className="badge badge-primary">
            ${event.ticket_price.amount} {event.ticket_price.currency}
          </span>

          {event.max_attendees >= getMockTicketCount(event.id) !== false ? (
            <span className="badge badge-success">
              Available
            </span>
          ) : (
            <span className="badge badge-error">
              Sold Out
            </span>
          )}

        </div>
      </div>
    </div>
  )
}
