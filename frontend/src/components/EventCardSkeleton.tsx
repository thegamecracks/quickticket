/**
 * Loading placeholder for EventCard — mirrors its structure and sizing
 * (h-48 image, min-h-14 title, three info rows, badge + button footer)
 * so the grid doesn't shift when real cards arrive.
 */
export default function EventCardSkeleton() {
  return (
    <div
      className="card h-full flex flex-col overflow-hidden border border-base-300 bg-base-200 shadow-sm"
      aria-hidden="true"
    >
      {/* Event image */}
      <figure>
        <div className="skeleton h-48 w-full rounded-none" />
      </figure>

      <div className="card-body flex flex-1 flex-col">
        {/* Event name */}
        <div className="min-h-14">
          <div className="skeleton h-7 w-3/4" />
        </div>

        {/* Event information */}
        <ul className="space-y-2">
          <li><div className="skeleton h-4 w-2/3" /></li>
          <li><div className="skeleton h-4 w-1/2" /></li>
          <li><div className="skeleton h-4 w-1/3" /></li>
        </ul>

        {/* Price and availability */}
        <div className="mt-auto flex items-center justify-between gap-2 pt-4">
          <div className="skeleton h-6 w-20 rounded-full" />
          <div className="skeleton h-10 w-28 rounded-btn" />
        </div>
      </div>
    </div>
  )
}
