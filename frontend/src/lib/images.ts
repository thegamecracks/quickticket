import { API_URL } from './api'

type ImageEntity = 'events' | 'venues'

/**
 * URL of an event's or venue's image. The backend route 307-redirects to a
 * presigned storage URL (Garage/S3), which <img> tags follow directly.
 */
export const bannerUrl = (entity: ImageEntity, id: string): string =>
  `${API_URL}/${entity}/${id}/banner`

export const thumbnailUrl = (entity: ImageEntity, id: string): string =>
  `${API_URL}/${entity}/${id}/thumbnail`

/** Final fallbacks for SkeletonImage's source chain. */
export const EVENT_PLACEHOLDER =
  'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event'
export const VENUE_PLACEHOLDER =
  'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Venue'
