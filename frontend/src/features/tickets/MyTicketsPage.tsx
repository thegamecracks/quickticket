import { MockTickets } from "../../lib/mocks"
import { useAuth } from "../../lib/auth";
import { useEffect, useState } from "react";
import type { User } from "../account/types";
import type { Ticket } from "./types";
import { useNavigate } from "react-router";


export default function MyTicketsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tickets, setTickets] = useState<Ticket[] | undefined>(undefined);

  useEffect(() => {
    // eventual const res = api.get("/tickets");
    const getTickets = (user: User | null): void => {
      if (user) {
        const filteredTickets = MockTickets.filter((ticket: Ticket) => ticket.account_id === user.id)
        setTickets(filteredTickets);
      }
    }

    getTickets(user);
  }, [user])


  const goToTicketDetail = (id: Ticket["id"]) => {
    navigate(`/myTickets/${id}`);
  }

  return (
    <section className="mx-auto w-full max-w-5xl grow px-4 py-12">
      <h1 className="mb-4 text-3xl font-bold mx-auto">My Tickets</h1>
      {user && tickets && (
        <ul className="list mx-auto space-y-2">
          {
            tickets.map((t: Ticket) => (
              <li className="list-row rounded-2xl bg-neutral shadow-md" key={t.id}>
                <div className="text-xl align-middle"><span className="text-secondary">Ticket</span>
                </div>
                <div>
                  <span className="text-xs">Ticket id: {t.id} | <span className="text-secondary">Event id:</span> {t.event_id}</span>
                </div>
                <div>
                  <button className="btn btn-primary" onClick={() => goToTicketDetail(t.id)}>View</button>
                </div>
              </li>
            ))
          }
        </ul >


      )
      }
    </section >
  )
}
