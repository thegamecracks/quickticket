
export type Event = {
  id: string;
  venue_id: string;
  created_at: string;
}

export interface RSVPEvent extends Event {

}

export interface TicketedEvent extends Event {
}
