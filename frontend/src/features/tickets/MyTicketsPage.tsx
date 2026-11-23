import PageLayout from "../../components/PageLayout"
import { getMockEvent, MockTickets } from "../../lib/mocks"
import { useAuth } from "../../lib/auth";
import { useInfiniteQuery } from "@tanstack/react-query";
import { LoadMoreButton } from "../../components/LoadMoreButton";
import type { User } from "../account/types";
import type { Ticket } from "./types";
import { useNavigate } from "react-router";
import { calcDateLongTimeMediumRange } from "../../lib/general";
import { SkeletonRows } from "../../components/Skeleton";
import { PAGE_SIZE, type Paged } from "../../lib/pagination";

// TODO: replace this mock fetcher with the real endpoint once a
// GET /tickets list endpoint exists:
//   api.get('/tickets', { params: { limit, next } })
// It mimics the backend's keyset pagination so only the queryFn changes.
const fetchMyTicketsPage = (user: User, next: string | null): Paged<Ticket> => {
  const mine = MockTickets.filter((ticket) => ticket.user_id === user.id)
  const offset = next === null ? 0 : Number(next)
  const items = mine.slice(offset, offset + PAGE_SIZE)

  return {
    items,
    next:
      offset + items.length < mine.length
        ? String(offset + items.length)
        : null,
    total: mine.length,
  }
}

export default function MyTicketsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["tickets", "mine", user?.id],
    enabled: user != null,
    queryFn: ({ pageParam }) =>
      Promise.resolve(fetchMyTicketsPage(user!, pageParam)),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next,
  })

  const tickets = data?.pages.flatMap((page) => page.items)

  const goToTicketDetail = (id: Ticket["id"]) => {
    navigate(`/myTickets/${id}`);
  }

  return (
    <PageLayout title="My Tickets">
      {user && (
        <div className="space-y-6">
          {tickets === undefined && (
            <SkeletonRows rows={4} />
          )}

          {tickets && tickets.length > 0 && (
            <ul className="list mx-auto space-y-2">
              {
                tickets.map((t: Ticket) => (
                  <li className="list-row items-center rounded-2xl bg-primary/10 shadow-md hover:bg-primary/20 transition-colors duration-300  cursor-pointer" key={t.id} onClick={() => goToTicketDetail(t.id)}>
                    <div className="text-xl align-middle"><span className="text-secondary">Ticket</span>
                    </div>
                    <div>
                      {getMockEvent(t.event_id)?.display_name}
                    </div>
                    <div>
                      {calcDateLongTimeMediumRange(getMockEvent(t.event_id)!.starts_at, getMockEvent(t.event_id)!.ends_at)}
                    </div>
                  </li>
                ))
              }
            </ul>
          )}

          {tickets && tickets.length === 0 && (
            <p className="text-base-content/70">
              You have no tickets yet.
            </p>
          )}

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
  )
}
