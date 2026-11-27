import type { Money } from '../../lib/types';
import type { User } from '../account/types';
import type { Event } from '../events/types';

export type Ticket = {
  id: string; // UUID (ticket_id)
  event_id: Event['id'];
  user_id: User['id'];
  created_at: string; // ISO 8601 datetime
  paid_cost: Money;
};
