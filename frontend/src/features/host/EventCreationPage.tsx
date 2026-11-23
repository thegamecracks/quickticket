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
import { SkeletonRows } from '../../components/Skeleton'

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
 * Create-event wizard. The organization (when missing) and a venue are
 * always resolved before the event details: the venue step offers every
 * existing venue in a dropdown or the venue form to create a new one, and
 * either choice continues to the event form. Going back to the venue step
 * is allowed (nothing is un-created by it) — the organization step is not,
 * since an organization cannot be un-created.
 */
export default function EventCreationPage() {
  const { user } = useAuth()

  // A user owns at most one organization; any administrator membership is it.
  const membershipOrgId = user?.organization_members.find(isAdministrator)?.organization_id

  const [org, setOrg] = useState<OrganizationResponse | null>(null)
  const [orgError, setOrgError] = useState(false)

  // Venue step presentation: choose an existing venue or open the form.
  // Defaults to the choice UI whenever venues exist (including a venue just
  // created in the flow), otherwise straight to the form; the buttons below
  // override that default until the organization changes again.
  const [venueModeOverride, setVenueModeOverride] = useState<'select' | 'create' | null>(null)
  const [venueChoice, setVenueChoice] = useState('')
  const [selectedVenueId, setSelectedVenueId] = useState<string | null>(null)

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
  const venueMode = venueModeOverride ?? (org && org.venues.length > 0 ? 'select' : 'create')
  const phase =
    needsOrg ? 'org'
    : selectedVenueId === null ? 'venue'
    : 'event'

  // The organization step only exists for organizers without one; venue and
  // event details always do.
  const totalSteps = (needsOrg ? 1 : 0) + 2
  const venueStepNumber = needsOrg ? 2 : 1
  const eventStepNumber = needsOrg ? 3 : 2

  const stepHeading = (step: number, title: string) => (
    <p className="-mt-2 mb-7 text-sm text-base-content/60">
      Step {step} of {totalSteps}: {title}
    </p>
  )

  const hostingAs = org && (
    <p className="-mt-2 mb-7 text-sm text-base-content/60">
      Hosting as{' '}
      <span className="font-semibold text-base-content">
        {org.display_name}
      </span>
    </p>
  )

  const selectedVenue = org?.venues.find(venue => venue.id === selectedVenueId)

  return (
    <PageLayout
      title="Create Event"
      actions={
        <>
          {phase === 'event' && (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setSelectedVenueId(null)}
            >
              Back
            </button>
          )}
          <Link to="/myEvents" className="btn btn-ghost btn-sm">
            Cancel
          </Link>
        </>
      }
    >
      {/* Authentication loading state */}
      {user === undefined && (
        <SkeletonRows rows={3} />
      )}

      {/* No sign-in gate: a signed-out visitor uses the navbar's Sign in
          button. */}

      {/* Organization still loading */}
      {user && membershipOrgId && !org && !orgError && (
        <SkeletonRows rows={4} />
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
          {stepHeading(1, 'create your organization')}

          <OrganizationForm embedded onCreated={setOrg} />
        </>
      )}

      {/* Step: choose an existing venue */}
      {org && phase === 'venue' && venueMode === 'select' && (
        <>
          {hostingAs}
          {stepHeading(venueStepNumber, 'choose a venue')}

          <div className="mb-5 rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm">
            <div className="mb-5 border-b border-base-300 pb-3">
              <h2 className="text-lg font-semibold">
                Venue
              </h2>
              <p className="mt-1 text-xs text-base-content/55">
                Pick one of your venues, or create a new one for this event.
              </p>
            </div>

            <select
              className="select select-bordered w-full"
              aria-label="Venue"
              value={venueChoice || org.venues[0]?.id || ''}
              onChange={event => setVenueChoice(event.target.value)}
            >
              {org.venues.map(venue => (
                <option key={venue.id} value={venue.id}>
                  {venue.display_name}
                </option>
              ))}
            </select>

            <div className="mt-4 flex flex-wrap justify-end gap-3">
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setVenueModeOverride('create')}
              >
                Create New Venue
              </button>

              <button
                type="button"
                className="btn btn-primary"
                disabled={!venueChoice && !org.venues[0]}
                onClick={() =>
                  setSelectedVenueId(venueChoice || org.venues[0]?.id || null)
                }
              >
                Continue
              </button>
            </div>
          </div>
        </>
      )}

      {/* Step: create a venue */}
      {org && phase === 'venue' && venueMode === 'create' && (
        <>
          {hostingAs}
          {stepHeading(
            venueStepNumber,
            org.venues.length > 0 ? 'create a new venue' : 'add your first venue',
          )}

          {org.venues.length > 0 && (
            <div className="mb-5">
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setVenueModeOverride('select')}
              >
                ← Back to venue selection
              </button>
            </div>
          )}

          <APIProvider
            apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? ''}
            libraries={['geocoding']}
            onError={error => console.error('Google Maps failed to load:', error)}
          >
            <VenueForm
              embedded
              fixedOrganizationId={org.id}
              onCreated={venue => {
                setOrg(previous =>
                  previous
                    ? { ...previous, venues: [toOrganizationVenue(venue), ...previous.venues] }
                    : previous,
                )
                setSelectedVenueId(venue.id)
              }}
            />
          </APIProvider>
        </>
      )}

      {/* Step: event details */}
      {org && phase === 'event' && selectedVenue && (
        <>
          {hostingAs}
          <p className="-mt-2 mb-7 text-sm text-base-content/60">
            Venue:{' '}
            <span className="font-semibold text-base-content">
              {selectedVenue.display_name}
            </span>
          </p>

          {stepHeading(eventStepNumber, 'event details')}

          <EventForm venue={selectedVenue} />
        </>
      )}
    </PageLayout>
  )
}

/** The event details form; the venue was already chosen in the wizard's
 * venue step and cannot be changed here — use Back to revisit that step. */
function EventForm({ venue }: { venue: OrganizationVenue }) {
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
      venue_id: venue.id,
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
      <div className="flex justify-end gap-3">
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
  )
}
