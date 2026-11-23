import { useEffect, useRef, useState, type ChangeEvent, type SubmitEvent } from 'react'
import { useNavigate } from 'react-router'

import { SkeletonRows } from '../../components/Skeleton'
import { api } from '../../lib/api'
import axios from 'axios'
import type { EventResponse } from '../events/types'

const categories = [
  'Music',
  'Comedy',
  'Art',
  'Food',
  'Technology',
  'Sports',
  'Community',
  'Other',
]

/** The venue context an event form needs; satisfied by both the wizard's
 * organization venue and a loaded event's partial venue. */
export interface EventFormVenue {
  id: string
  display_name: string
}

/** Formats an ISO datetime as a `datetime-local` input value (local time). */
const toDatetimeLocal = (iso: string) => {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const MIN_EVENT_DURATION = 60 * 60 * 1000 // 1h, mirrors backend check_event_duration
const MAX_EVENT_DURATION = 7 * 24 * 60 * 60 * 1000 // 7d

/**
 * Shared event details form. Create mode (a wizard venue was already chosen)
 * POSTs /events; edit mode (an eventId was given) loads the event, prefills
 * every field, and PATCHes /events/{id}. Images are preview-only here —
 * banners/thumbnails upload through their own routes.
 */
export default function EventForm({
  venue,
  eventId,
}: {
  venue?: EventFormVenue
  eventId?: string
}) {
  const isEdit = Boolean(eventId)
  const navigate = useNavigate()

  // Edit-mode loading state; create mode starts with the wizard's venue.
  const [loadedVenue, setLoadedVenue] = useState<EventFormVenue | null>(venue ?? null)
  const [loading, setLoading] = useState(isEdit)
  const [loadError, setLoadError] = useState(false)

  // TODO: consolidate useStates
  const [displayName, setDisplayName] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('')
  const [otherCategory, setOtherCategory] = useState('')
  const [startsAt, setStartsAt] = useState('')
  const [endsAt, setEndsAt] = useState('')
  const [ticketPrice, setTicketPrice] = useState('')
  const [isFree, setIsFree] = useState(false)
  const [maxAttendees, setMaxAttendees] = useState('')
  const [thumbnailUrl, setThumbnailUrl] = useState('')
  const [bannerUrl, setBannerUrl] = useState('')
  // Set only when the user picks a new image: in edit mode this doubles as
  // the dirty flag (loaded previews leave it null, so saves don't re-upload).
  const [thumbnailFile, setThumbnailFile] = useState<File | null>(null)
  const [bannerFile, setBannerFile] = useState<File | null>(null)
  const [message, setMessage] = useState('')
  const [isError, setIsError] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!eventId) return

    let active = true

    api
      .get<EventResponse>(`/events/${eventId}`)
      .then(response => {
        if (!active) return
        const event = response.data

        setLoadedVenue({ id: event.venue.id, display_name: event.venue.display_name })
        setDisplayName(event.display_name)
        setDescription(event.description)
        if (categories.includes(event.category)) {
          setCategory(event.category)
        } else {
          setCategory('Other')
          setOtherCategory(event.category)
        }
        setStartsAt(toDatetimeLocal(event.starts_at))
        setEndsAt(toDatetimeLocal(event.ends_at))
        setTicketPrice((event.ticket_price.amount / 100).toFixed(2))
        setIsFree(event.ticket_price.amount === 0)
        setMaxAttendees(String(event.max_attendees))
        if (event.thumbnail) setThumbnailUrl(`/storage/${event.thumbnail.id}`)
        if (event.banner) setBannerUrl(`/storage/${event.banner.id}`)
      })
      .catch(() => {
        if (active) setLoadError(true)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [eventId])

  const thumbnailInputRef = useRef<HTMLInputElement>(null)
  const bannerInputRef = useRef<HTMLInputElement>(null)

  const readImage = (
    e: ChangeEvent<HTMLInputElement>,
    setUrl: (url: string) => void,
    setFile: (file: File | null) => void,
  ) => {
    const file = e.target.files?.[0]
    if (!file) return

    setFile(file)
    const reader = new FileReader()
    reader.onload = () => setUrl(reader.result as string)
    reader.readAsDataURL(file)
  }

  /** Associates a picked image with an event via its banner/thumbnail routes.
   * Uploads happen after the event exists — EventCreate/EventUpdate don't
   * accept image fields. Client-side dimension/filesize checks are deferred
   * until the backend's image hardening lands; the API rejects bad files. */
  const uploadImage = (eventId: string, kind: 'thumbnail' | 'banner', file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.putForm(`/events/${eventId}/${kind}`, form)
  }

  const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (displayName.trim().length < 3) {
      setIsError(true)
      setMessage('Event name must be at least 3 characters.')
      return
    }

    if (category === 'Other' && !otherCategory.trim()) {
      setIsError(true)
      setMessage('Please enter the event category.')
      return
    }

    const duration = new Date(endsAt).getTime() - new Date(startsAt).getTime()
    if (duration < MIN_EVENT_DURATION || duration > MAX_EVENT_DURATION) {
      setIsError(true)
      setMessage('Events must last between 1 hour and 7 days.')
      return
    }

    if (Number(maxAttendees) > 10000) {
      setIsError(true)
      setMessage('Maximum attendees cannot exceed 10,000.')
      return
    }

    const finalCategory =
      category === 'Other' ? otherCategory.trim() : category

    // Mirrors the backend DTOs (which forbid unknown fields): venue_id is
    // only part of EventCreate — EventUpdate has no such field.
    const payload = {
      display_name: displayName.trim(),
      description,
      category: finalCategory,
      starts_at: new Date(startsAt).toISOString(),
      ends_at: new Date(endsAt).toISOString(),
      ticket_price: {
        amount: isFree ? 0 : Math.round(Number(ticketPrice) * 100),
        currency: 'CAD',
      },
      max_attendees: Number(maxAttendees),
    }

    setIsSubmitting(true)
    try {
      const response = isEdit
        ? await api.patch<EventResponse>(`/events/${eventId}`, payload)
        : await api.post<EventResponse>('/events', { ...payload, venue_id: venue?.id })

      // Images attach after the event exists. Failures never re-submit the
      // event itself (create succeeded — a retry would duplicate it); the
      // user can re-upload from the edit page instead.
      for (const [kind, file] of [
        ['thumbnail', thumbnailFile] as const,
        ['banner', bannerFile] as const,
      ]) {
        if (!file) continue
        try {
          await uploadImage(response.data.id, kind, file)
        } catch (err) {
          console.warn(`${kind} upload failed (event was saved)`, err)
        }
      }

      navigate(`/events/${response.data.id}`)
    } catch (err) {
      setIsError(true)
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail
        setMessage(
          typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((issue: { msg?: string }) => issue.msg).join('; ')
              : 'Failed to save the event. Please try again.',
        )
      } else {
        setMessage('Failed to save the event. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (loading) {
    return <SkeletonRows rows={4} />
  }

  if (loadError) {
    return (
      <div role="alert" className="alert alert-error">
        Unable to load the event. Please try again later.
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {loadedVenue && (
        <p className="-mt-2 mb-7 text-sm text-base-content/60">
          Venue:{' '}
          <span className="font-semibold text-base-content">
            {loadedVenue.display_name}
          </span>
        </p>
      )}

      {/* Basic information */}
      <div className="rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm">
        <div className="mb-5 border-b border-base-300 pb-3">
          <h2 className="text-lg font-semibold">
            Basic Information
          </h2>
          <p className="mt-1 text-xs text-base-content/55">
            Add the main information about your event.
          </p>
        </div>

        <div className="space-y-5">
          <div>
            <label
              htmlFor="eventName"
              className="mb-2 block text-sm font-medium"
            >
              Event Name
            </label>

            <input
              id="eventName"
              type="text"
              className="input input-bordered w-full"
              placeholder="Toronto Summer Music Festival"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              maxLength={128}
              required
            />
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label
                htmlFor="description"
                className="text-sm font-medium"
              >
                Description
              </label>

              <span className="text-xs text-base-content/45">
                {description.length}/4096
              </span>
            </div>

            <textarea
              id="description"
              className="textarea textarea-bordered min-h-28 w-full resize-y"
              placeholder="Tell guests what they can expect..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={4096}
              required
            />
          </div>

          <div>
            <label
              htmlFor="category"
              className="mb-2 block text-sm font-medium"
            >
              Category
            </label>

            <select
              id="category"
              className="select select-bordered w-full"
              value={category}
              onChange={(e) => {
                const selectedCategory = e.target.value
                setCategory(selectedCategory)

                if (selectedCategory !== 'Other') {
                  setOtherCategory('')
                }
              }}
              required
            >
              <option value="" disabled>
                Select a category
              </option>

              {categories.map((eventCategory) => (
                <option key={eventCategory} value={eventCategory}>
                  {eventCategory}
                </option>
              ))}
            </select>
          </div>

          {category === 'Other' && (
            <div>
              <label
                htmlFor="otherCategory"
                className="mb-2 block text-sm font-medium"
              >
                Specify Category
              </label>

              <input
                id="otherCategory"
                type="text"
                className="input input-bordered w-full"
                placeholder="Example: Fashion, Gaming, Education..."
                value={otherCategory}
                onChange={(e) => setOtherCategory(e.target.value)}
                maxLength={128}
                required
              />
            </div>
          )}
        </div>
      </div>

      {/* Schedule */}
      <div className="rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm">
        <div className="mb-5 border-b border-base-300 pb-3">
          <h2 className="text-lg font-semibold">Schedule</h2>
          <p className="mt-1 text-xs text-base-content/55">
            Choose when the event begins and ends.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <div>
            <label
              htmlFor="startsAt"
              className="mb-2 block text-sm font-medium"
            >
              Start Date & Time
            </label>

            <input
              id="startsAt"
              type="datetime-local"
              className="input input-bordered w-full"
              value={startsAt}
              onChange={(e) => setStartsAt(e.target.value)}
              required
            />
          </div>

          <div>
            <label
              htmlFor="endsAt"
              className="mb-2 block text-sm font-medium"
            >
              End Date & Time
            </label>

            <input
              id="endsAt"
              type="datetime-local"
              className="input input-bordered w-full"
              value={endsAt}
              onChange={(e) => setEndsAt(e.target.value)}
              required
            />
          </div>
        </div>
      </div>

      {/* Ticket details */}
      <div className="rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm">
        <div className="mb-5 border-b border-base-300 pb-3">
          <h2 className="text-lg font-semibold">
            Tickets & Capacity
          </h2>
          <p className="mt-1 text-xs text-base-content/55">
            Set the price and maximum number of guests.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <div>
            <label
              htmlFor="ticketPrice"
              className="mb-2 block text-sm font-medium"
            >
              Ticket Price
            </label>

            <div className="flex">
              <span className="flex items-center rounded-l-lg border border-r-0 border-base-300 bg-base-200 px-3 text-sm">
                $
              </span>

              <input
                id="ticketPrice"
                type="number"
                className="input input-bordered w-full rounded-none"
                placeholder="0.00"
                min="0"
                step="0.01"
                value={isFree ? '' : ticketPrice}
                onChange={(e) => setTicketPrice(e.target.value)}
                disabled={isFree}
                required={!isFree}
              />

              <span className="flex items-center rounded-r-lg border border-l-0 border-base-300 bg-base-200 px-3 text-xs">
                CAD
              </span>
            </div>

            <label className="mt-2 flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="checkbox checkbox-sm"
                checked={isFree}
                onChange={(e) => setIsFree(e.target.checked)}
              />

              This is a free event
            </label>
          </div>

          <div>
            <label
              htmlFor="maxAttendees"
              className="mb-2 block text-sm font-medium"
            >
              Maximum Attendees
            </label>

            <input
              id="maxAttendees"
              type="number"
              className="input input-bordered w-full"
              placeholder="100"
              min="1"
              max="10000"
              value={maxAttendees}
              onChange={(e) => setMaxAttendees(e.target.value)}
              required
            />
          </div>
        </div>
      </div>

      {/* Images */}
      <div className="rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm">
        <div className="mb-5 border-b border-base-300 pb-3">
          <h2 className="text-lg font-semibold">Images</h2>
          <p className="mt-1 text-xs text-base-content/55">
            Add images for the event listing and event page.
          </p>
        </div>

        <div className="space-y-6">
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="block text-sm font-medium">
                Thumbnail Image
              </span>

              <input
                ref={thumbnailInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => readImage(e, setThumbnailUrl, setThumbnailFile)}
              />

              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => thumbnailInputRef.current?.click()}
              >
                Upload Image
              </button>
            </div>

            <div className="flex min-h-32 items-center justify-center overflow-hidden rounded-lg border border-dashed border-base-300 bg-base-200">
              {thumbnailUrl ? (
                <img
                  src={thumbnailUrl}
                  alt="Thumbnail preview"
                  className="max-h-40 w-full object-contain"
                />
              ) : (
                <span className="text-sm text-base-content/50">
                  image preview
                </span>
              )}
            </div>

            <p className="mt-2 block text-xs text-base-content/50">
              Used on event cards and search results.
            </p>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="block text-sm font-medium">
                Banner Image
              </span>

              <input
                ref={bannerInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => readImage(e, setBannerUrl, setBannerFile)}
              />

              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => bannerInputRef.current?.click()}
              >
                Upload Image
              </button>
            </div>

            <div className="flex min-h-32 items-center justify-center overflow-hidden rounded-lg border border-dashed border-base-300 bg-base-200">
              {bannerUrl ? (
                <img
                  src={bannerUrl}
                  alt="Banner preview"
                  className="max-h-40 w-full object-contain"
                />
              ) : (
                <span className="text-sm text-base-content/50">
                  image preview
                </span>
              )}
            </div>

            <p className="mt-2 block text-xs text-base-content/50">
              Used as the large image on the event detail page.
            </p>
          </div>
        </div>
      </div>

      {/* Form message */}
      {message && (
        <div
          className={`alert ${isError ? 'alert-error' : 'alert-success'
            }`}
        >
          <span>{message}</span>
        </div>
      )}

      {/* Buttons */}
      <div className="flex justify-end gap-3">
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => navigate(-1)}
        >
          Cancel
        </button>

        <button
          type="submit"
          className="btn btn-primary min-w-36"
          disabled={isSubmitting}
        >
          {isSubmitting
            ? <span className="loading loading-spinner"></span>
            : isEdit ? 'Save Changes' : 'Create Event'}
        </button>
      </div>
    </form>
  )
}
