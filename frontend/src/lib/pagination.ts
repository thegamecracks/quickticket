/**
 * Shared types and helpers for the backend's keyset pagination
 * (backend/src/quickticket/paging.py, `KeysetPagedResponse`).
 */

/** Mirrors `KeysetPagedResponse[E, K]`: one page of a cursor-paginated list. */
export type Paged<T> = {
  items: T[]
  /** Cursor for the next page; null means this is the last page. */
  next: string | null
  /** Total number of items matching the current filters. */
  total: number
}

/**
 * The backend caps `limit` at 10 (`KeysetPageParams.le`), so every list page
 * asks for the maximum batch size.
 */
export const PAGE_SIZE = 10
