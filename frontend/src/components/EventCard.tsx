
export type EventInfo = {
    id: number
    title: string
    date: string
    location: string
    price: number
  }
  
  type EventCardProps = {
    event: EventInfo
  }
  
  export default function EventCard({ event }: EventCardProps) {
    return (
      <div className="card bg-base-200 border border-base-300 shadow-sm">
        <div className="card-body">
          <h2 className="card-title">{event.title}</h2>
  
          <p>📅 {event.date}</p>
          <p>📍 {event.location}</p>
          <p className="font-semibold">${event.price}</p>
        </div>
      </div>
    )
  }
  