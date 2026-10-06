import SkeletonImage from "../../components/SkeletonImage.tsx";
import { formatDateLong } from "../../lib/general.ts";
import { MockTickets } from "../../lib/mocks"
import type { Ticket } from './types.ts'
import { useParams } from 'react-router'

export default function TicketDetailPage() {
  const { id } = useParams<{ id: Ticket["id"] }>();
  const t = MockTickets.find((t: Ticket) => t.id === id);

  return (
    <section className="mx-auto w-full max-w-3xl grow px-4 py-12">
      <h1 className="mb-4 text-3xl font-bold">Ticket</h1>
      <div className="flex">
        {t && (
          <div className="mx-auto card card-border rounded-2xl bg-primary/50 shadow-md" key={t.id}>
            <figure className="px-10 pt-10">
              <SkeletonImage
                src="https://api.qrserver.com/v1/create-qr-code/?data=https://www.youtube.com/watch?v=j5a0jTc9S10&size=150x150"
                alt="Ticket"
                className="w-32 h-32 object-cover"
              />
            </figure>
            <div className="card-body items-center text-center">
              <h2 className="card-title">{t.id}</h2>
              <ul>
                <li>Event Id: {t.event_id}</li>
                <li>Date Bought: {formatDateLong(t.created_at)}</li>
                <li>Cost: ${t.paid_cost.amount} {t.paid_cost.currency}</li>
              </ul>
              <div className="card-actions">

              </div>
            </div>
          </div>
        )}
      </div>


    </section>
  )
}
