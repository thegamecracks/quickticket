// Mirrors quickticket.models.accounts + routers.profile.

/** routers.profile `ProfileAddress`. Note: no `user_id` on the wire. */
export interface ProfileAddress {
  id: string; // UUID (address_id)
  line_1: string;
  line_2: string;
  city: string;
  province: string;
  postal_code: string;
}

/** routers.profile `ProfileOrganizationMember`. */
export interface ProfileOrganizationMember {
  organization_id: string; // UUID FK -> organization
  user_id: string; // UUID FK -> account
  permissions: number; // IntFlag: 1 = ADMINISTRATOR
  joined_at: string; // ISO 8601 datetime
}

/** GET /profile/@me — routers.profile `Profile`. */
export interface User {
  id: string; // UUID (user_id)
  created_at: string; // ISO 8601 datetime
  display_name: string;
  first_name: string;
  last_name: string;
  email: string;
  addresses: ProfileAddress[];
  organization_members: ProfileOrganizationMember[];
}

/** Membership flag values from models.organizations `OrganizationMemberPermissions`. */
export const OrganizationMemberPermissions = {
  // Mirrors backend OrganizationMemberPermissions.OWNER (1) — the backend
  // itself notes the "owner" name is provisional, so we call it ADMINISTRATOR.
  ADMINISTRATOR: 1,
} as const;

/** True when the membership carries the ADMINISTRATOR flag. */
export function isAdministrator(member: ProfileOrganizationMember): boolean {
  return (member.permissions & OrganizationMemberPermissions.ADMINISTRATOR) !== 0;
}

/** True when the user is an administrator of the given organization. */
export function isOrganizationAdministrator(
  user: Pick<User, 'organization_members'> | null | undefined,
  organizationId: string,
): boolean {
  return Boolean(user?.organization_members.some(
    member =>
      member.organization_id === organizationId && isAdministrator(member),
  ));
}

/** Mirrors quickticket.models.accounts.Address — the ORM row, includes `user_id`. */
export interface Address extends ProfileAddress {
  user_id: string; // UUID FK -> account
}

export interface Notification {
  id: string; // UUID (notification_id)
  user_id: string; // UUID FK -> account
  created_at: string; // ISO 8601 datetime
  expires_at: string; // ISO 8601 datetime
  email_at: string | null; // ISO 8601 datetime
  is_read: boolean;
  content_short: string;
  content_full: string;
}

/** A third-party identity linked to an account (e.g. Google). */
export interface OpenIDAccount {
  issuer: string;
  sub: string;
  user_id: string; // UUID FK -> account
  id_token: string | null;
}
