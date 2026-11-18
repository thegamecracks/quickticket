import PageLayout from "../../components/PageLayout"
import { useRef, useState, type ChangeEvent, type SubmitEvent } from 'react'
import type { Event } from '../events/types'
import {
  MockUser,
  createMockEvent,
  getMockOrganizationsForAccount,
  getMockVenuesForOrganization,
} from '../../lib/mocks'

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

interface EventCreationPageProps {
  /**
   * Organization the event is created under. Eventually supplied by the
   * wizard flow (after org + venue creation); falls back to the mock
   * user's first organization for now.
   */
  organizationId?: string
  /** Preselected venue, e.g. the one just created in the wizard. */
  venueId?: string
}

export default function EventCreationPage({
  organizationId: wizardOrganizationId,
  venueId: wizardVenueId,
}: EventCreationPageProps) {
  // replace mock lookup with real wizard/router values later
  const organizations = getMockOrganizationsForAccount(MockUser.id)
  const organization = wizardOrganizationId
    ? organizations.find((o) => o.id === wizardOrganizationId)
    : organizations[0]

  const orgVenues = organization
    ? getMockVenuesForOrganization(organization.id)
    : []
  // TODO: consolidate useStates
  const [displayName, setDisplayName] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('')
  const [otherCategory, setOtherCategory] = useState('')
  const [venueId, setVenueId] = useState(wizardVenueId ?? '')
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
    setVenueId(wizardVenueId ?? '')
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

    const created = createMockEvent(mockEvent)
    console.log('Mock event submission:', created)

    setIsError(false)
    setMessage('Event information submitted successfully.')
  }

  return (
    <PageLayout title="Create Event">
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

                  {orgVenues.map((venue) => (
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
    </PageLayout>
  )
}
