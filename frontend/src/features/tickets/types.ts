import type { User } from "../account/types";
import type { Event } from "../events/types";

export type Ticket = {
  id: string;
  event: Event
  account_id: User["id"]
  created_at: string;
  paid_cost: number;
}
