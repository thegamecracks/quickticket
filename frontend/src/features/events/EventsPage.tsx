
import { useSearchParams } from 'react-router'
import EventCard from '../../components/EventCard'
import { useEffect, useState } from 'react'
import { Pagination, safePage } from '../../components/Pagination'
import type { Event } from './types.ts'
import { MockEvents } from '../../lib/mocks'

//  TODO: figure out how to bring back categories
// Available event categories
/*const categories = [
  'All',
  'Music',
  'Comedy',
  'Art',
  'Food',
  'Technology',
] as const
*/

/*
type EventCategory = Exclude<(typeof categories)[number], 'All'>

 type CategorizedEvent = EventInfo & {
  category: EventCategory
}
*/

export default function EventsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [currentPage, setCurrentPage] = useState(1)

  const [events, setEvents] = useState<Event[] | undefined>(undefined)

  useEffect(() => {
    // eventual const res = api.get("/events");
    const getEvents = (): void => {
      const res = MockEvents;
      setEvents(res);
    }

    getEvents();
  }, [])


  // Read search and category from URL
  const search = searchParams.get('search') ?? ''

  // TODO: figure out how to bring back categories
  //const selectedCategory = searchParams.get('category') ?? 'All'

  // Filter events by title, location and category
  const filteredEvents = events?.filter((event) => {
    const searchText = search.trim().toLowerCase()

    const matchesSearch =
      event.display_name.toLowerCase().includes(searchText) ||
      event.description.toLowerCase().includes(searchText)

    {/* TODO: figure out how to bring back categories
    const matchesCategory =
      selectedCategory === 'All' ||
      event.category === selectedCategory
      */}

    return matchesSearch; {/*&& matchesCategory*/ }
  })

  // Pagination
  const eventsPerPage = 6 // will be set to higher once we get more data in

  const totalPages = Math.ceil(
    filteredEvents ? filteredEvents.length / eventsPerPage : 0
  )

  const page = safePage(currentPage, totalPages)

  const paginatedEvents = filteredEvents?.slice(
    (page - 1) * eventsPerPage,
    page * eventsPerPage
  )

  // Update search and return to page 1
  const handleSearch = (value: string) => {
    const nextParams = new URLSearchParams(searchParams)

    if (value) {
      nextParams.set('search', value)
    } else {
      nextParams.delete('search')
    }

    setSearchParams(nextParams, { replace: true })
    setCurrentPage(1)
  }

  // Update category and return to page 1
  /* TODO: figure out how to handle categories
  const handleCategory = (value: string) => {
    const nextParams = new URLSearchParams(searchParams)

    if (value === 'All') {
      nextParams.delete('category')
    } else {
      nextParams.set('category', value)
    }

    setSearchParams(nextParams, { replace: true })
    setCurrentPage(1)
  }
  */

  return (
    <section className="mx-auto w-full max-w-5xl grow px-4 py-12">

      {/* Page heading */}
      <h1 className="mb-6 text-2xl font-semibold">
        Events
      </h1>

      {/* Search and category filter */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row">
        <input
          type="text"
          placeholder="Search events..."
          aria-label="Search events"
          className="input input-bordered w-full"
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
        />

        {/* TODO: figure out how to bring back categories
        <select
          aria-label="Filter by category"
          className="select select-bordered w-full sm:w-56"
          value={selectedCategory}
          onChange={(e) => handleCategory(e.target.value)}
        >
          {categories.map((category) => (
            <option key={category} value={category}>
              {category === 'All'
                ? 'All Categories'
                : category}
            </option>
          ))}
        </select>
        */}
      </div>

      {/* Event cards */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {paginatedEvents?.map((event) => (
          <EventCard
            key={event.id}
            event={event}
          />
        ))}
      </div>

      {/* No matching events */}
      {
        filteredEvents && filteredEvents.length === 0 && (
          <p className="text-base-content/70">
            No events found.
          </p>
        )
      }

      <Pagination currentPage={page} totalPages={totalPages} onChangePage={(page) => setCurrentPage(page)} />
    </section >
  )
}
