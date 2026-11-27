import { useInfiniteQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router';
import { LoadMoreButton } from '../../components/LoadMoreButton';
import PageLayout from '../../components/PageLayout';
import { SkeletonRows } from '../../components/Skeleton';
import { useAuth } from '../../lib/auth';
import { calcDateLongTimeMediumRange } from '../../lib/general';
import { getMockEvent, MockTickets } from '../../lib/mocks';
import { PAGE_SIZE, type Paged } from '../../lib/pagination';
import type { User } from '../account/types';
import type { Ticket } from './types';

// TODO: replace this mock fetcher with the real endpoint once a
// GET /tickets list endpoint exists:
//   api.get('/tickets', { params: { limit, next } })
// It mimics the backend's keyset pagination so only the queryFn changes.
const fetchMyTicketsPage = (user: User, next: string | null): Paged<Ticket> => {
  const mine = MockTickets.filter((ticket) => ticket.user_id === user.id);
  const offset = next === null ? 0 : Number(next);
  const items = mine.slice(offset, offset + PAGE_SIZE);

  return {
    items,
    next: offset + items.length < mine.length ? String(offset + items.length) : null,
    total: mine.length,
  };
};

export default function MyTicketsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ['tickets', 'mine', user?.id],
    enabled: user != null,
    queryFn: ({ pageParam }) => {
      if (user == null) {
        return Promise.reject(new Error('Tickets can only be fetched while signed in'));
      }
      return Promise.resolve(fetchMyTicketsPage(user, pageParam));
    },
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next,
  });

  const tickets = data?.pages.flatMap((page) => page.items);

  const goToTicketDetail = (id: Ticket['id']) => {
    navigate(`/myTickets/${id}`);
  };

  return (
    <PageLayout title="My Tickets">
      {user && (
        <div className="space-y-6">
          {tickets === undefined && <SkeletonRows rows={4} />}

          {tickets && tickets.length > 0 && (
            <ul className="list mx-auto space-y-2">
              {tickets.map((t: Ticket) => {
                const event = getMockEvent(t.event_id);
                return (
                  <li key={t.id}>
                    <button
                      type="button"
                      className="list-row w-full cursor-pointer items-center rounded-2xl bg-primary/10 text-left shadow-md transition-colors duration-300 hover:bg-primary/20"
                      onClick={() => goToTicketDetail(t.id)}
                    >
                      <div className="text-xl align-middle">
                        <span className="text-secondary">Ticket</span>
                      </div>
                      <div>{event?.display_name}</div>
                      <div>{event ? calcDateLongTimeMediumRange(event.starts_at, event.ends_at) : null}</div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}

          {tickets && tickets.length === 0 && <p className="text-base-content/70">You have no tickets yet.</p>}

          {tickets && (
            <LoadMoreButton
              hasMore={hasNextPage}
              loading={isFetchingNextPage}
              onClick={() => void fetchNextPage()}
              endLabel="That's all your tickets"
            />
          )}
        </div>
      )}
    </PageLayout>
  );
}
