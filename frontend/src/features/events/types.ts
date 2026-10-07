import type { Money, Point } from "../../lib/types";

// Mirrors quickticket.models.events.

export interface Venue {
  id: string; // UUID (venue_id)
  organization_id: string; // UUID FK -> organization
  created_at: string; // ISO 8601 datetime
  display_name: string;
  description: string; // markdown
  theme: string;
  thumbnail_url: string;
  banner_url: string;
  location_name: string;
  location_coords: Point | null;
}

export type Event = {
  id: string; // UUID (event_id)
  venue_id: string; // UUID FK -> venue
  created_at: string; // ISO 8601 datetime
  display_name: string;
  description: string; // markdown
  theme: string;
  thumbnail_url: string;
  banner_url: string;
  starts_at: string; // ISO 8601 datetime of event start
  ends_at: string; // ISO 8601 datetime of event end
  ticket_price: Money;
  max_attendees: number;
}

// Marker interfaces for events the user has interacted with.
// TODO: flesh out once backend supports RSVPs / ticket queries.
export interface RSVPEvent extends Event {
}

export interface TicketedEvent extends Event {
}
