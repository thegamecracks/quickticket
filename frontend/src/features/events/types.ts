
export type Event = {
  id: string;
  venue_id: string; // TODO: Replace with venue type?
  created_at: string;
  display_name: string;
  description: string;
  theme: string; // TODO: review to see if we want to keep theme or replace with category? maybe we can just make them the same thing.
  thumbnail_url: string;
  banner_url: string;
  starts_at: string; // date time of event start
  ends_at: string;  // date time of event end
  ticket_price: number;
  max_attendees: number;
}

export interface RSVPEvent extends Event {

}

export interface TicketedEvent extends Event {
}
