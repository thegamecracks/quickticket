import type { Organization, StorageObjectRef } from "../events/types";

/*
 * Wire types mirroring `quickticket.routers.organizations`.
 * Note these are its own local schemas, trimmed down relative to the events and
 * venues routers: an organization's venues carry no location, and its events
 * carry no dates, price, or capacity.
 */

/** routers.organizations `PartialEvent` — an event summary inside a venue summary. */
export interface OrganizationEvent {
  id: string; // UUID (event_id)
  created_at: string; // ISO 8601 datetime
  display_name: string;
  description: string; // markdown
  theme: string;
  thumbnail: StorageObjectRef | null;
  banner: StorageObjectRef | null;
}

/** routers.organizations `PartialVenue` — a venue summary inside an organization. */
export interface OrganizationVenue {
  id: string; // UUID (venue_id)
  created_at: string; // ISO 8601 datetime
  display_name: string;
  description: string; // markdown
  theme: string;
  thumbnail: StorageObjectRef | null;
  banner: StorageObjectRef | null;
  events: OrganizationEvent[];
}

/** routers.organizations `PartialOrganizationMember`. */
export interface OrganizationMember {
  account_id: string; // UUID FK -> account
}

/** GET /organizations/{id} — routers.organizations `OrganizationRead`. */
export interface OrganizationResponse extends Organization {
  venues: OrganizationVenue[];
  members: OrganizationMember[];
}
