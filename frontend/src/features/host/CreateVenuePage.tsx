
import { useState, type FormEvent } from 'react'
import PageLayout from '../../components/PageLayout'

type VenueType = 'physical' | 'virtual'

export default function CreateVenuePage() {
  // Basic venue information
  const [displayName, setDisplayName] = useState('')
  const [description, setDescription] = useState('')
  const [theme, setTheme] = useState('')

  // Venue type
  const [venueType, setVenueType] = useState<VenueType>('physical')

  // Physical location
  const [streetAddress, setStreetAddress] = useState('')
  const [unit, setUnit] = useState('')
  const [city, setCity] = useState('')
  const [province, setProvince] = useState('')
  const [postalCode, setPostalCode] = useState('')
  const [country, setCountry] = useState('Canada')

  // Virtual location
  const [platform, setPlatform] = useState('')
  const [otherPlatform, setOtherPlatform] = useState('')

  // Form feedback
  const [message, setMessage] = useState('')
  const [isError, setIsError] = useState(false)

  // Validate the form before future API integration
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    setMessage('')
    setIsError(false)

    if (
      !displayName.trim() ||
      !description.trim() ||
      !theme.trim()
    ) {
      setIsError(true)
      setMessage('Please complete all required venue details.')
      return
    }

    let locationName = ''

    if (venueType === 'physical') {
      if (
        !streetAddress.trim() ||
        !city.trim() ||
        !province.trim() ||
        !postalCode.trim() ||
        !country.trim()
      ) {
        setIsError(true)
        setMessage('Please complete the venue address.')
        return
      }

      // Combine address fields into the backend's
      // existing location_name field.
      locationName = [
        streetAddress.trim(),
        unit.trim(),
        city.trim(),
        province.trim(),
        postalCode.trim(),
        country.trim(),
      ]
        .filter(Boolean)
        .join(', ')
    } else {
      if (!platform) {
        setIsError(true)
        setMessage('Please select an online platform.')
        return
      }

      if (platform === 'Other' && !otherPlatform.trim()) {
        setIsError(true)
        setMessage('Please enter the online platform name.')
        return
      }

      locationName =
        platform === 'Other'
          ? otherPlatform.trim()
          : platform
    }

    // The current API limits location_name to 128 characters.
    if (locationName.length > 128) {
      setIsError(true)
      setMessage(
        'The combined location details exceed 128 characters. Please shorten the address or platform name.'
      )
      return
    }

    // Frontend-only implementation for Issue #111.
    // The organization ID and venue details will be
    // submitted to the backend during API integration.
    setIsError(false)
    setMessage(
      'Venue details validated successfully. This is a frontend preview; your venue has not been saved yet.'
    )
  }

  // Reset all form fields
  const clearForm = () => {
    setDisplayName('')
    setDescription('')
    setTheme('')
    setVenueType('physical')

    setStreetAddress('')
    setUnit('')
    setCity('')
    setProvince('')
    setPostalCode('')
    setCountry('Canada')

    setPlatform('')
    setOtherPlatform('')

    setMessage('')
    setIsError(false)
  }

  return (
    <PageLayout title="Create Venue">
      <div className="space-y-6">

        <p className="text-base-content/70">
          Add a venue to your organization to start hosting events.
        </p>

        <form
          onSubmit={handleSubmit}
          className="space-y-6"
        >

          {/* BASIC INFORMATION */}
          <section className="rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm sm:p-6">

            <div className="space-y-5">

              {/* Venue Name */}
              <div>
                <label
                  htmlFor="venueName"
                  className="mb-2 block text-sm font-medium"
                >
                  Venue Name
                  <span className="text-error"> *</span>
                </label>

                <input
                  id="venueName"
                  type="text"
                  className="input input-bordered w-full"
                  placeholder="e.g. Aurora Event Hall"
                  value={displayName}
                  onChange={e => setDisplayName(e.target.value)}
                  required
                />
              </div>

              {/* Description */}
              <div>
                <label
                  htmlFor="venueDescription"
                  className="mb-2 block text-sm font-medium"
                >
                  Description
                  <span className="text-error"> *</span>
                </label>

                <textarea
                  id="venueDescription"
                  className="textarea textarea-bordered h-32 w-full"
                  placeholder="Describe your venue, its atmosphere, and the types of events it can host..."
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  maxLength={4096}
                  required
                />

                <p className="mt-1 text-right text-xs text-base-content/60">
                  {description.length}/4096
                </p>
              </div>

              {/* Theme */}
              <div>
                <label
                  htmlFor="venueTheme"
                  className="mb-2 block text-sm font-medium"
                >
                  Theme
                  <span className="text-error"> *</span>
                </label>

                <input
                  id="venueTheme"
                  type="text"
                  className="input input-bordered w-full"
                  placeholder="e.g. Music, Conference, Art"
                  value={theme}
                  onChange={e => setTheme(e.target.value)}
                  maxLength={128}
                  required
                />
              </div>

            </div>
          </section>

          {/* LOCATION INFORMATION */}
          <section className="rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm sm:p-6">

            <h2 className="text-lg font-semibold">
              Location Information
            </h2>

            <p className="mt-1 text-sm text-base-content/60">
              Help attendees find your venue.
            </p>

            <div className="divider" />

            <div className="space-y-5">

              {/* Venue Type */}
              <div>
                <label className="mb-3 block text-sm font-medium">
                  Venue Type
                </label>

                <div className="flex flex-wrap gap-6">

                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="radio"
                      name="venueType"
                      className="radio radio-primary radio-sm"
                      checked={venueType === 'physical'}
                      onChange={() => {
                        setVenueType('physical')
                        setMessage('')
                      }}
                    />
                    Physical Venue
                  </label>

                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="radio"
                      name="venueType"
                      className="radio radio-primary radio-sm"
                      checked={venueType === 'virtual'}
                      onChange={() => {
                        setVenueType('virtual')
                        setMessage('')
                      }}
                    />
                    Virtual Venue
                  </label>

                </div>
              </div>

              {/* PHYSICAL VENUE FIELDS */}
              {venueType === 'physical' && (
                <div className="space-y-5">

                  {/* Street Address */}
                  <div>
                    <label
                      htmlFor="streetAddress"
                      className="mb-2 block text-sm font-medium"
                    >
                      Street Address
                      <span className="text-error"> *</span>
                    </label>

                    <input
                      id="streetAddress"
                      type="text"
                      className="input input-bordered w-full"
                      placeholder="e.g. 123 Yonge Street"
                      value={streetAddress}
                      onChange={e => setStreetAddress(e.target.value)}
                      required
                    />
                  </div>

                  {/* Unit */}
                  <div>
                    <label
                      htmlFor="unit"
                      className="mb-2 block text-sm font-medium"
                    >
                      Unit / Suite
                      <span className="ml-1 text-xs text-base-content/50">
                        (Optional)
                      </span>
                    </label>

                    <input
                      id="unit"
                      type="text"
                      className="input input-bordered w-full"
                      placeholder="e.g. Unit 200"
                      value={unit}
                      onChange={e => setUnit(e.target.value)}
                    />
                  </div>

                  {/* City and Province */}
                  <div className="grid gap-4 sm:grid-cols-2">

                    <div>
                      <label
                        htmlFor="city"
                        className="mb-2 block text-sm font-medium"
                      >
                        City
                        <span className="text-error"> *</span>
                      </label>

                      <input
                        id="city"
                        type="text"
                        className="input input-bordered w-full"
                        placeholder="e.g. Aurora"
                        value={city}
                        onChange={e => setCity(e.target.value)}
                        required
                      />
                    </div>

                    <div>
                      <label
                        htmlFor="province"
                        className="mb-2 block text-sm font-medium"
                      >
                        Province / State
                        <span className="text-error"> *</span>
                      </label>

                      <input
                        id="province"
                        type="text"
                        className="input input-bordered w-full"
                        placeholder="e.g. Ontario"
                        value={province}
                        onChange={e => setProvince(e.target.value)}
                        required
                      />
                    </div>

                  </div>

                  {/* Postal Code and Country */}
                  <div className="grid gap-4 sm:grid-cols-2">

                    <div>
                      <label
                        htmlFor="postalCode"
                        className="mb-2 block text-sm font-medium"
                      >
                        Postal / ZIP Code
                        <span className="text-error"> *</span>
                      </label>

                      <input
                        id="postalCode"
                        type="text"
                        className="input input-bordered w-full"
                        placeholder="e.g. L4G 1N2"
                        value={postalCode}
                        onChange={e => setPostalCode(e.target.value)}
                        required
                      />
                    </div>

                    <div>
                      <label
                        htmlFor="country"
                        className="mb-2 block text-sm font-medium"
                      >
                        Country
                        <span className="text-error"> *</span>
                      </label>

                      <input
                        id="country"
                        type="text"
                        className="input input-bordered w-full"
                        placeholder="e.g. Canada"
                        value={country}
                        onChange={e => setCountry(e.target.value)}
                        required
                      />
                    </div>

                  </div>

                </div>
              )}

              {/* VIRTUAL VENUE FIELDS */}
              {venueType === 'virtual' && (
                <div className="space-y-5">

                  <div>
                    <label
                      htmlFor="onlinePlatform"
                      className="mb-2 block text-sm font-medium"
                    >
                      Online Platform
                      <span className="text-error"> *</span>
                    </label>

                    <select
                      id="onlinePlatform"
                      className="select select-bordered w-full"
                      value={platform}
                      onChange={e => setPlatform(e.target.value)}
                      required
                    >
                      <option value="">
                        Select a platform
                      </option>
                      <option value="Zoom">
                        Zoom
                      </option>
                      <option value="Microsoft Teams">
                        Microsoft Teams
                      </option>
                      <option value="Google Meet">
                        Google Meet
                      </option>
                      <option value="Other">
                        Other
                      </option>
                    </select>
                  </div>

                  {platform === 'Other' && (
                    <div>
                      <label
                        htmlFor="otherPlatform"
                        className="mb-2 block text-sm font-medium"
                      >
                        Platform Name
                        <span className="text-error"> *</span>
                      </label>

                      <input
                        id="otherPlatform"
                        type="text"
                        className="input input-bordered w-full"
                        placeholder="Enter the platform name"
                        value={otherPlatform}
                        onChange={e => setOtherPlatform(e.target.value)}
                        maxLength={128}
                        required
                      />
                    </div>
                  )}

                  <p className="text-sm text-base-content/60">
                    Virtual venues don't require a physical address.
                  </p>

                </div>
              )}

            </div>
          </section>

          {/* FORM FEEDBACK */}
          {message && (
            <div
              role={isError ? 'alert' : 'status'}
              className={`alert ${
                isError ? 'alert-error' : 'alert-info'
              }`}
            >
              <span>{message}</span>
            </div>
          )}

          {/* FORM ACTIONS */}
          <div className="flex flex-wrap justify-end gap-3 border-t border-base-300 pt-5">

            <button
              type="button"
              className="btn btn-ghost"
              onClick={clearForm}
            >
              Clear
            </button>

            <button
              type="submit"
              className="btn btn-primary"
            >
              Create Venue
            </button>

          </div>

        </form>
      </div>
    </PageLayout>
  )
}
