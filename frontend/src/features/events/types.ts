import type { Money, Point } from "../../lib/types";


export interface Organization {
  id: string;
  created_at: string;
  display_name: string;
}

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

export interface StorageObjectRef {
  id: string; // UUID -> storage object; TODO: URL scheme for serving images
}

export interface VenueBase {
  id: string;
  created_at: string; // ISO 8601 datetime
  display_name: string;
  description: string; // markdown
  theme: string;
  thumbnail: StorageObjectRef | null;
  banner: StorageObjectRef | null;
  location_name: string;
  location_coords: Point | null;
  organization: Organization;
}

export type EventResponse = {
  id: string; // UUID (event_id)
  created_at: string; // ISO 8601 datetime
  display_name: string;
  description: string; // markdown
  theme: string;
  thumbnail: StorageObjectRef | null;
  banner: StorageObjectRef | null;
  starts_at: string; // ISO 8601 datetime of event start
  ends_at: string; // ISO 8601 datetime of event end
  ticket_price: Money;
  max_attendees: number;
  tickets: { id: string }[]; // signed-in user's tickets for this event
  venue: VenueBase;
};

/**
 * Events embedded in a venue response: mirrors routers.venues `VenueReadEvent`,
 * which is a full event but without the nested `venue` (it is implied).
 */
export type VenueEventResponse = Omit<EventResponse, 'venue'>;

/** GET /venues/{id} — mirrors routers.venues VenueRead. */
export type VenueResponse = VenueBase & {
  events: VenueEventResponse[];
};

// Marker interfaces for events the user has interacted with.
// TODO: flesh out once backend supports RSVPs / ticket queries.
export interface RSVPEvent extends Event {
}

export interface TicketedEvent extends Event {
}
