// Mirrors quickticket.models.accounts.

export interface User {
  id: string; // UUID (account_id)
  created_at: string; // ISO 8601 datetime
  display_name: string;
  first_name: string;
  last_name: string;
  email: string;
  addresses: Address[];
}

export interface Address {
  id: string; // UUID (address_id)
  account_id: string; // UUID FK -> account
  line_1: string;
  line_2: string;
  city: string;
  province: string;
  postal_code: string;
}

export interface Notification {
  id: string; // UUID (notification_id)
  account_id: string; // UUID FK -> account
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
  account_id: string; // UUID FK -> account
  id_token: string | null;
}
