
import { useSearchParams } from 'react-router'
import EventCard, { type EventInfo } from '../../components/EventCard'
import { useState } from 'react'
import { Pagination, safePage } from '../../components/Pagination'

// Available event categories
const categories = [
  'All',
  'Music',
  'Comedy',
  'Art',
  'Food',
  'Technology',
] as const

type EventCategory = Exclude<(typeof categories)[number], 'All'>

type CategorizedEvent = EventInfo & {
  category: EventCategory
}
// TODO: Change to Event type, using theme as the category
// TODO: Move into /lib/mocks.ts

// Temporary events until the backend is ready
const events: CategorizedEvent[] = [
  {
    id: 1,
    title: 'Toronto Music Festival',
    date: 'October 15, 2026',
    location: 'Toronto, ON',
    price: 50,
    category: 'Music',
    imageUrl: '/images/music.jpg',
    available: false,
  },
  {
    id: 2,
    title: 'Comedy Night',
    date: 'October 20, 2026',
    location: 'Mississauga, ON',
    price: 30,
    category: 'Comedy',
    imageUrl: '/images/comedy.jpg',
  },
  {
    id: 3,
    title: 'Art Exhibition',
    date: 'November 5, 2026',
    location: 'Toronto, ON',
    price: 20,
    category: 'Art',
    imageUrl: '/images/art.jpg',
  },
  {
    id: 4,
    title: 'Live Jazz Concert',
    date: 'November 12, 2026',
    location: 'Vaughan, ON',
    price: 45,
    category: 'Music',
    imageUrl: '/images/jazz.jpg',
  },
  {
    id: 5,
    title: 'Food & Culture Festival',
    date: 'November 18, 2026',
    location: 'Toronto, ON',
    price: 25,
    category: 'Food',
    imageUrl: '/images/food.jpg',
  },
  {
    id: 6,
    title: 'Tech Networking Event',
    date: 'December 5, 2026',
    location: 'Markham, ON',
    price: 15,
    category: 'Technology',
    imageUrl: '/images/tech.jpg',
    available: false,
  },
]

export default function EventsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [currentPage, setCurrentPage] = useState(1)

  // Read search and category from URL
  const search = searchParams.get('search') ?? ''
  const selectedCategory = searchParams.get('category') ?? 'All'

  // Filter events by title, location and category
  const filteredEvents = events.filter((event) => {
    const searchText = search.trim().toLowerCase()

    const matchesSearch =
      event.title.toLowerCase().includes(searchText) ||
      event.location.toLowerCase().includes(searchText)

    const matchesCategory =
      selectedCategory === 'All' ||
      event.category === selectedCategory

    return matchesSearch && matchesCategory
  })

  // Pagination
  const eventsPerPage = 3 // will be set to higher once we get more data in

  const totalPages = Math.ceil(
    filteredEvents.length / eventsPerPage
  )

  const page = safePage(currentPage, totalPages)

  const paginatedEvents = filteredEvents.slice(
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
      </div>

      {/* Event cards */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {paginatedEvents.map((event) => (
          <EventCard
            key={event.id}
            event={event}
          />
        ))}
      </div>

      {/* No matching events */}
      {filteredEvents.length === 0 && (
        <p className="text-base-content/70">
          No events found.
        </p>
      )}

      <Pagination currentPage={page} totalPages={totalPages} onChangePage={(page) => setCurrentPage(page)} />
    </section>
  )
}
