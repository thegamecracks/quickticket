import { useInfiniteQuery } from '@tanstack/react-query';
import { useEffect } from 'react';
import { useSearchParams } from 'react-router';
import EventCard from '../../components/EventCard';
import EventCardSkeleton from '../../components/EventCardSkeleton';
import { LoadMoreButton } from '../../components/LoadMoreButton';
import PageLayout from '../../components/PageLayout';
import { api } from '../../lib/api.ts';
import { PAGE_SIZE, type Paged } from '../../lib/pagination.ts';
import type { EventResponse } from './types.ts';

// TODO: figure out how to bring back categories

export default function EventsPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Read search from URL
  const search = searchParams.get('search') ?? '';

  // Cursor-paginated fetch of all events, one batch per "Load more" click.
  // The backend is keyset-based (GET /events?limit=&next=), so pages can only
  // be fetched forward — see src/lib/pagination.ts.
  const { data, fetchNextPage, hasNextPage, isFetching, isFetchingNextPage, isLoading, isError, refetch } =
    useInfiniteQuery({
      queryKey: ['events'],
      queryFn: ({ pageParam }) =>
        api
          .get<Paged<EventResponse>>('/events', {
            params: { limit: PAGE_SIZE, next: pageParam },
          })
          .then((res) => res.data),
      initialPageParam: null as string | null,
      getNextPageParam: (lastPage) => lastPage.next,
    });

  const events = data?.pages.flatMap((page) => page.items);

  // TODO: auto-draining every remaining page while searching is a stopgap
  // until the backend grows a `search` query param on GET /events; move the
  // filter server-side then so it composes with pagination properly.
  useEffect(() => {
    if (search.trim() && hasNextPage && !isFetching && !isError) {
      void fetchNextPage();
    }
  }, [search, hasNextPage, isFetching, isError, fetchNextPage]);

  // Filter events by title, location and category
  const filteredEvents = events?.filter((event) => {
    const searchText = search.trim().toLowerCase();

    return (
      event.display_name.toLowerCase().includes(searchText) || event.description.toLowerCase().includes(searchText)
    );
  });

  const handleSearch = (value: string) => {
    const nextParams = new URLSearchParams(searchParams);

    if (value) {
      nextParams.set('search', value);
    } else {
      nextParams.delete('search');
    }

    setSearchParams(nextParams, { replace: true });
  };

  const isSearching = Boolean(search.trim());

  return (
    <PageLayout title="Events">
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
      </div>

      {/* First page is still loading */}
      {isLoading && (
        <div aria-live="polite">
          <span className="sr-only">Loading events...</span>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: PAGE_SIZE }, (_, i) => (
              <EventCardSkeleton key={i} />
            ))}
          </div>
        </div>
      )}

      {/* Loading failed */}
      {isError && (
        <div className="rounded-xl border border-base-300 bg-base-200 p-8 text-center">
          <p className="text-base-content/70">Failed to load events.</p>
          <button type="button" className="btn btn-primary mt-4" onClick={() => void refetch()}>
            Try again
          </button>
        </div>
      )}

      {/* Event cards */}
      {filteredEvents && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredEvents.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      )}

      {/* No matching events */}
      {filteredEvents && filteredEvents.length === 0 && !isLoading && (
        <p className="text-base-content/70">No events found.</p>
      )}

      {/* Load more (hidden while searching: the effect above drains every page) */}
      {filteredEvents && !isError && !isSearching && (
        <div className="mt-8">
          <LoadMoreButton
            hasMore={hasNextPage}
            loading={isFetchingNextPage}
            onClick={() => void fetchNextPage()}
            endLabel={filteredEvents.length > 0 ? "That's all the events" : undefined}
          />
        </div>
      )}
    </PageLayout>
  );
}
