import { useNavigate } from "react-router";
import type { VenueEventResponse } from "../features/events/types";
import { calcTimeMediumRange, formatDateLong } from "../lib/general";
import SkeletonImage from "./SkeletonImage";


type EventListItemProps = {
  event: VenueEventResponse
}

export default function EventListItem({ event }: EventListItemProps) {
  const navigate = useNavigate();

  const handleViewEvent = () => {
    navigate(`/events/${event.id}`)
  }

  return (
    <li className="list-row items-center gap-4">
      <figure className="h-20 w-32 shrink-0 overflow-hidden rounded-lg bg-base-300">
        <SkeletonImage
          src={event.thumbnail ? `/storage/${event.thumbnail.id}` : 'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event'}
          alt={event.display_name}
          className="h-full w-full object-cover"
        />
      </figure>
      <div>
        <div className="font-bold">{event.display_name}</div>
        <div>{formatDateLong(event.starts_at)}</div>
        <div>{calcTimeMediumRange(event.starts_at, event.ends_at)}</div>
      </div>
      <div>
        <button className="btn btn-primary" onClick={() => handleViewEvent()}>View</button>
      </div>
    </li>
  );
}
