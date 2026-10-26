import { useRef, useState, type ChangeEvent, type SubmitEvent } from 'react'
import type { Event } from '../events/types'
import {
  MockUser,
  createMockEvent,
  getMockOrganizationsForAccount,
  getMockVenuesForOrganization,
} from '../../lib/mocks'

const themes = [
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
  const [displayName, setDisplayName] = useState('')
  const [description, setDescription] = useState('')
  const [theme, setTheme] = useState('')
  const [otherTheme, setOtherTheme] = useState('')
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

  const clearForm = () => {
    setDisplayName('')
    setDescription('')
    setTheme('')
    setOtherTheme('')
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

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (theme === 'Other' && !otherTheme.trim()) {
      setIsError(true)
      setMessage('Please enter the event theme.')
      return
    }

    if (new Date(endsAt) <= new Date(startsAt)) {
      setIsError(true)
      setMessage('End date and time must be after the start date and time.')
      return
    }

    const finalTheme =
      theme === 'Other' ? otherTheme.trim() : theme

    const mockEvent = {
      venue_id: venueId,
      display_name: displayName,
      description,
      theme: finalTheme,
      thumbnail_url: thumbnailUrl,
      banner_url: bannerUrl,
      starts_at: startsAt,
      ends_at: endsAt,
      ticket_price: {
        amount: Number(ticketPrice),
        currency: 'CAD',
      },
      max_attendees: Number(maxAttendees),
    }

    console.log('Mock event submission:', mockEvent)

    setIsError(false)
    setMessage('Event information submitted successfully.')
  }

  return (
    <section className="mx-auto w-full max-w-4xl grow px-4 py-10">
      {/* Page header */}
      <div className="mb-7">
        <h1 className="text-3xl font-bold">Create Event</h1>
        <p className="mt-1 text-sm text-base-content/60">
          Enter the details guests will see when browsing your event.
        </p>
      </div>

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
                  htmlFor="theme"
                  className="mb-2 block text-sm font-medium"
                >
                  Theme
                </label>

                <select
                  id="theme"
                  className="select select-bordered w-full"
                  value={theme}
                  onChange={(e) => {
                    const selectedTheme = e.target.value
                    setTheme(selectedTheme)

                    if (selectedTheme !== 'Other') {
                      setOtherTheme('')
                    }
                  }}
                  required
                >
                  <option value="" disabled>
                    Select a theme
                  </option>

                  {themes.map((eventTheme) => (
                    <option key={eventTheme} value={eventTheme}>
                      {eventTheme}
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

            {theme === 'Other' && (
              <div>
                <label
                  htmlFor="otherTheme"
                  className="mb-2 block text-sm font-medium"
                >
                  Specify Theme
                </label>

                <input
                  id="otherTheme"
                  type="text"
                  className="input input-bordered w-full"
                  placeholder="Example: Fashion, Gaming, Education..."
                  value={otherTheme}
                  onChange={(e) => setOtherTheme(e.target.value)}
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
              <label
                htmlFor="thumbnailUrl"
                className="mb-2 block text-sm font-medium"
              >
                Thumbnail Image URL
              </label>

              <input
                id="thumbnailUrl"
                type="url"
                className="input input-bordered w-full"
                placeholder="https://example.com/thumbnail.jpg"
                value={thumbnailUrl}
                onChange={(e) => setThumbnailUrl(e.target.value)}
                maxLength={2000}
                required
              />

              <p className="mt-2 block text-xs text-base-content/50">
                Used on event cards and search results.
              </p>
            </div>

            <div>
              <label
                htmlFor="bannerUrl"
                className="mb-2 block text-sm font-medium"
              >
                Banner Image URL
              </label>

              <input
                id="bannerUrl"
                type="url"
                className="input input-bordered w-full"
                placeholder="https://example.com/banner.jpg"
                value={bannerUrl}
                onChange={(e) => setBannerUrl(e.target.value)}
                maxLength={2000}
                required
              />

              <p className="mt-2 block text-xs text-base-content/50">
                Used as the large image on the event detail page.
              </p>
            </div>
          </div>
        </div>

        {/* Form message */}
        {message && (
          <div
            className={`alert ${
              isError ? 'alert-error' : 'alert-success'
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
    </section>
  )
}