import type { User } from "../account/types";
import type { Event } from "../events/types";
import type { Money } from "../../lib/types";

export type Ticket = {
  id: string; // UUID (ticket_id)
  event_id: Event["id"];
  account_id: User["id"];
  created_at: string; // ISO 8601 datetime
  paid_cost: Money;
}
