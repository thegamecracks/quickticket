// Shared types that mirror backend types in backend/src/quickticket/models.

/** Mirrors quickticket.models.money.Money. `amount` is in the currency's smallest unit (e.g. cents). */
export type Money = {
  amount: number;
  currency: string; // ISO 4217 / Stripe currency code, e.g. "CAD"
};

/** Mirrors quickticket.models.types.Point. */
export type Point = {
  lat: number;
  long: number;
};
