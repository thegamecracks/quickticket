import NavigateBackBtn from "../../components/NavigateBack.tsx";
import SkeletonImage from "../../components/SkeletonImage.tsx";
import { formatDateLongAndTimeShort } from "../../lib/general.ts";
import { getMockEvent, MockTickets } from "../../lib/mocks"
import type { Ticket } from './types.ts'
import { useParams } from 'react-router'

export default function TicketDetailPage() {
  const { id } = useParams<{ id: Ticket["id"] }>();
  const t = MockTickets.find((t: Ticket) => t.id === id);

  return (
    <section className="mx-auto h-full w-full max-w-3xl grow px-4 py-12">
      <NavigateBackBtn />
      <div className="flex h-100">
        {t && (
          <div className="mx-auto card card-border rounded-2xl bg-primary/20 shadow-md" key={t.id}>
            <figure className="px-10 pt-10">
              <SkeletonImage
                src="https://api.qrserver.com/v1/create-qr-code/?data=https://www.youtube.com/watch?v=j5a0jTc9S10&size=150x150"
                alt="Ticket"
                className="w-32 h-32 object-cover"
              />
            </figure>
            <div className="card-body items-center text-center">
              <h2 className="card-title text-xl">Ticket</h2>
              <h3 className="card-title text-lg mb-2">{getMockEvent(t.event_id)?.display_name}</h3>
              <ul className="leading-8">
                <li><span className="text-md font-bold">{formatDateLongAndTimeShort(t.created_at)}</span></li>
                <li><span className="badge badge-success"> ${t.paid_cost.amount} {t.paid_cost.currency}</span></li>
              </ul>
              <div className="card-actions">

              </div>
            </div>
          </div>
        )}
      </div>

    </section >
  )
}
