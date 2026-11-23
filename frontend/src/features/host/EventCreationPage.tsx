import { useEffect, useRef, useState, type ChangeEvent, type SubmitEvent } from 'react'
import { Link } from 'react-router'
import { APIProvider } from '@vis.gl/react-google-maps'

import PageLayout from "../../components/PageLayout"
import { api } from '../../lib/api'
import { useAuth } from '../../lib/auth'
import { isAdministrator } from '../account/types'
import type { Event } from '../events/types'
import type { VenueResponse } from '../events/types'
import type { OrganizationResponse, OrganizationVenue } from '../organizations/types'
import { createMockEvent } from '../../lib/mocks'
import { OrganizationForm } from './OrganizationForm'
import { VenueForm } from './VenueForm'

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

/** Maps a freshly created venue onto the organization response's venue shape. */
const toOrganizationVenue = (venue: VenueResponse): OrganizationVenue => ({
  id: venue.id,
  created_at: venue.created_at,
  display_name: venue.display_name,
  description: venue.description,
  category: venue.category,
  thumbnail: venue.thumbnail,
  banner: venue.banner,
  events: [],
})

/**
 * Create-event wizard. Resolves the organizer's preconditions in order —
 * organization, then first venue, then the event itself — showing only the
 * steps that are still missing. Each step's form is the same one used by its
 * standalone page (embedded), so the wizard and pages can't drift apart.
 *
 * Steps cannot go backwards: an organization or venue created mid-flow
 * cannot be un-created, so a back button would mislead.
 */
export default function EventCreationPage() {
  const { user } = useAuth()

  // A user owns at most one organization; any administrator membership is it.
  const membershipOrgId = user?.organization_members.find(isAdministrator)?.organization_id

  const [org, setOrg] = useState<OrganizationResponse | null>(null)
  const [orgError, setOrgError] = useState(false)

  useEffect(() => {
    if (!membershipOrgId) return

    let active = true

    api
      .get<OrganizationResponse>(`/organizations/${membershipOrgId}`)
      .then(response => {
        if (active) setOrg(response.data)
      })
      .catch(() => {
        if (active) setOrgError(true)
      })

    return () => {
      active = false
    }
  }, [membershipOrgId])

  const needsOrg = org === null
  const needsVenue = org !== null && org.venues.length === 0
  // Only count the steps that still have to happen; a fully set-up organizer
  // sees "Step 1 of 1", a brand-new one sees "Step 1 of 3".
  const totalSteps = (needsOrg ? 1 : 0) + (needsVenue ? 1 : 0) + 1

  const stepHeading = (title: string) => (
    <p className="-mt-2 mb-7 text-sm text-base-content/60">
      Step 1 of {totalSteps} — {title}
    </p>
  )

  return (
    <PageLayout
      title="Create Event"
      actions={
        <Link to="/myEvents" className="btn btn-ghost btn-sm">
          Cancel
        </Link>
      }
    >
      {/* Authentication loading state */}
      {user === undefined && (
        <p className="text-base-content/70">Checking your account...</p>
      )}

      {/* No sign-in gate: a signed-out visitor uses the navbar's Sign in
          button. */}

      {/* Organization still loading */}
      {user && membershipOrgId && !org && !orgError && (
        <p className="text-base-content/70">Loading your organization...</p>
      )}

      {/* Organization failed to load */}
      {user && membershipOrgId && orgError && (
        <div role="alert" className="alert alert-error">
          Unable to load your organization. Please try again later.
        </div>
      )}

      {/* Step: create organization */}
      {user && !membershipOrgId && !org && (
        <>
          {stepHeading('create your organization')}

          <OrganizationForm embedded onCreated={setOrg} />
        </>
      )}

      {/* Step: create first venue */}
      {org && org.venues.length === 0 && (
        <>
          {stepHeading('add your first venue')}

          <APIProvider
            apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? ''}
            libraries={['geocoding']}
            onError={error => console.error('Google Maps failed to load:', error)}
          >
            <VenueForm
              embedded
              fixedOrganizationId={org.id}
              onCreated={venue =>
                setOrg(previous =>
                  previous
                    ? { ...previous, venues: [toOrganizationVenue(venue), ...previous.venues] }
                    : previous,
                )
              }
            />
          </APIProvider>
        </>
      )}

      {/* Step: event details */}
      {org && org.venues.length > 0 && (
        <>
          {stepHeading('event details')}

          <EventForm venues={org.venues} />
        </>
      )}
    </PageLayout>
  )
}

/** The event details form; mounted once venues are known so the first venue
 * can be auto-selected through the initial state. */
function EventForm({ venues }: { venues: OrganizationVenue[] }) {
  // TODO: consolidate useStates
  const [displayName, setDisplayName] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('')
  const [otherCategory, setOtherCategory] = useState('')
  const [venueId, setVenueId] = useState(venues[0]?.id ?? '')
  const [startsAt, setStartsAt] = useState('')
  const [endsAt, setEndsAt] = useState('')
  const [ticketPrice, setTicketPrice] = useState('')
  const [isFree, setIsFree] = useState(false)
  const [maxAttendees, setMaxAttendees] = useState('')
  const [thumbnailUrl, setThumbnailUrl] = useState('')
  const [bannerUrl, setBannerUrl] = useState('')
  const [message, setMessage] = useState('')
  const [isError, setIsError] = useState(false)

  const thumbnailInputRef = useRef<HTMLInputElement>(null)
  const bannerInputRef = useRef<HTMLInputElement>(null)

  const readImage = (
    e: ChangeEvent<HTMLInputElement>,
    setUrl: (url: string) => void,
  ) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = () => setUrl(reader.result as string)
    reader.readAsDataURL(file)
  }

  const clearForm = () => {
    setDisplayName('')
    setDescription('')
    setCategory('')
    setOtherCategory('')
    setVenueId(venues[0]?.id ?? '')
    setStartsAt('')
    setEndsAt('')
    setTicketPrice('')
    setIsFree(false)
    setMaxAttendees('')
    setThumbnailUrl('')
    setBannerUrl('')
    setMessage('')
    setIsError(false)
  }

  const handleSubmit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (category === 'Other' && !otherCategory.trim()) {
      setIsError(true)
      setMessage('Please enter the event category.')
      return
    }

    if (new Date(endsAt) <= new Date(startsAt)) {
      setIsError(true)
      setMessage('End date and time must be after the start date and time.')
      return
    }

    const finalCategory =
      category === 'Other' ? otherCategory.trim() : category

    const mockEvent: Omit<Event, 'id' | 'created_at'> = {
      venue_id: venueId,
      display_name: displayName,
      description,
      category: finalCategory,
      // Fall back to the shared placeholder so cards never render a broken image.
      thumbnail_url:
        thumbnailUrl ||
        'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event',
      banner_url: bannerUrl,
      starts_at: new Date(startsAt).toISOString(),
      ends_at: new Date(endsAt).toISOString(),
      ticket_price: {
        amount: isFree ? 0 : Math.round(Number(ticketPrice) * 100),
        currency: 'CAD',
      },
      max_attendees: Number(maxAttendees),
    }

    // TODO: replace the mock submission with POST /events, mirroring the
    // backend's EventCreate validation (name 3-128 chars, description <=4096,
    // category <=128, future-aware starts_at/ends_at with a 1h-7d duration,
    // max_attendees 0-10000, ticket_price in cents), then navigate to
    // /events/{id} on success. Images upload separately (storage objects +
    // banner/thumbnail association), not with the create call.
    const created = createMockEvent(mockEvent)
    console.log('Mock event submission:', created)

    setIsError(false)
    setMessage('Event information submitted successfully.')
  }

  return (
    <>
      <p className="-mt-2 mb-7 text-sm text-base-content/60">
        Enter the details guests will see when browsing your event.
      </p>

      <form onSubmit={handleSubmit} className="space-y-5">
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

            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
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

              <div>
                <label
                  htmlFor="venue"
                  className="mb-2 block text-sm font-medium"
                >
                  Venue
                </label>

                <select
                  id="venue"
                  className="select select-bordered w-full"
                  value={venueId}
                  onChange={(e) => setVenueId(e.target.value)}
                  required
                >
                  <option value="" disabled>
                    Select a venue
                  </option>

                  {venues.map((venue) => (
                    <option key={venue.id} value={venue.id}>
                      {venue.display_name}
                    </option>
                  ))}
                </select>
              </div>
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
                  onChange={(e) => readImage(e, setThumbnailUrl)}
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
                  onChange={(e) => readImage(e, setBannerUrl)}
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
        <div className="flex justify-end gap-3 border-t border-base-300 pt-5">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={clearForm}
          >
            Clear
          </button>

          <button
            type="submit"
            className="btn btn-primary min-w-36"
          >
            Create Event
          </button>
        </div>
      </form>
    </>
  )
}
