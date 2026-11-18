
import { useState, type SubmitEvent } from 'react'
import { APIProvider, useMapsLibrary } from '@vis.gl/react-google-maps'
import PageLayout from '../../components/PageLayout'
import type { Point } from '../../lib/types'
import { useAuth } from '../../lib/auth'
import { api } from '../../lib/api'

type VenueType = 'physical' | 'virtual'

type VenueFormState = {
  displayName: string
  description: string
  category: string
  venueType: VenueType
  streetAddress: string
  unit: string
  city: string
  province: string
  postalCode: string
  country: string
}

const initialVenueState: VenueFormState = {
  displayName: '',
  description: '',
  category: '',
  venueType: 'physical',
  streetAddress: '',
  unit: '',
  city: '',
  province: '',
  postalCode: '',
  country: 'Canada',
}

/** Returns an error message, or undefined when the form is valid. */
const validateVenueForm = (form: VenueFormState): string | undefined => {
  if (
    !form.displayName.trim() ||
    !form.description.trim() ||
    !form.category.trim()
  ) {
    return 'Please complete all required venue details.'
  }

  if (form.venueType === 'physical') {
    if (
      !form.streetAddress.trim() ||
      !form.city.trim() ||
      !form.province.trim() ||
      !form.postalCode.trim() ||
      !form.country.trim()
    ) {
      return 'Please complete the venue address.'
    }
  }

  return undefined
}

/** Combines the form fields into the backend's location_name field. */
const buildLocationName = (form: VenueFormState): string =>
  form.venueType === 'physical'
    ? [
      form.streetAddress,
      form.unit,
      form.city,
      form.province,
      form.postalCode,
      form.country,
    ]
      .map(field => field.trim())
      .filter(Boolean)
      .join(', ')
    : ""


export default function CreateVenuePage() {
  const { user } = useAuth();


  const geocodingLib = useMapsLibrary('geocoding')

  const [form, setForm] = useState<VenueFormState>(initialVenueState)

  // Form feedback
  const [message, setMessage] = useState('')
  const [isError, setIsError] = useState(false)

  const updateState = (partial: Partial<VenueFormState>) => {
    setForm(prev => ({ ...prev, ...partial }))
  }

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!user) {
      setIsError(true)
      setMessage('Not authenticated. Please log in.')
      return
    }

    const organization_id = user.organization_members[0]?.organization_id
    if (!organization_id) {
      setIsError(true)
      setMessage('You must belong to an organization to create a venue.')
      return
    }

    const error = validateVenueForm(form)
    if (error) {
      setIsError(true)
      setMessage(error)
      return
    }

    const locationName = buildLocationName(form)

    // The current API limits location_name to 128 characters.
    if (locationName.length > 128) {
      setIsError(true)
      setMessage(
        'The combined location details exceed 128 characters. Please shorten the address or platform name.'
      )
      return
    }

    // Physical venues are geocoded to a (lat, lng) pair; geocoding
    // failures fall back to null so the venue can still be saved.
    const location_coords =
      form.venueType === 'physical'
        ? await geocodeAddress(locationName)
        : null

    try {
      await api.post('/venues', {
        organization_id,
        display_name: form.displayName.trim(),
        description: form.description.trim(),
        category: form.category.trim(),
        location_name: locationName,
        location_coords,
      })

      setIsError(false)
      setMessage('Venue created successfully.')
      clearForm()
    } catch (e) {
      console.error(e)
      setIsError(true)
      setMessage('Failed to create the venue. Please try again.')
    }
  }

  // Reset all form fields
  const clearForm = () => { setForm(initialVenueState) }

  const geocodeAddress = async (address: string): Promise<Point | null> => {
    try {
      // The hook can miss libraries that finished loading outside this
      // provider's lifecycle, so fall back to the global loader.
      const lib = geocodingLib ?? await google.maps.importLibrary('geocoding')

      const { results } = await new lib.Geocoder().geocode({ address })
      const loc = results[0]?.geometry.location

      if (!loc) console.warn('Geocode returned no results for:', address)

      return loc
        ? { lat: loc.lat(), lng: loc.lng() }
        : null
    } catch (e) {
      console.error('Geocoding failed for:', address, e)
      return null
    }
  }

  return (
    <APIProvider
      apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? ''}
      libraries={['geocoding']}
      onError={e => console.error('Google Maps failed to load:', e)}
    >
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
                  value={form.displayName}
                  onChange={e => updateState({ displayName: e.target.value })}
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
                  value={form.description}
                  onChange={e => updateState({ description: e.target.value })}
                  maxLength={4096}
                  required
                />

                <p className="mt-1 text-right text-xs text-base-content/60">
                  {form.description.length}/4096
                </p>
              </div>

              {/* Category */}
              <div>
                <label
                  htmlFor="venueCategory"
                  className="mb-2 block text-sm font-medium"
                >
                  Category
                  <span className="text-error"> *</span>
                </label>

                <input
                  id="venueCategory"
                  type="text"
                  className="input input-bordered w-full"
                  placeholder="e.g. Music, Conference, Art"
                  value={form.category}
                  onChange={e => updateState({ category: e.target.value })}
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
                      checked={form.venueType === 'physical'}
                      onChange={() => {
                        updateState({ venueType: 'physical' })
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
                      checked={form.venueType === 'virtual'}
                      onChange={() => {
                        updateState({ venueType: 'virtual' })
                        setMessage('')
                      }}
                    />
                    Virtual Venue
                  </label>

                </div>
              </div>

              {/* PHYSICAL VENUE FIELDS */}
              {form.venueType === 'physical' && (
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
                      value={form.streetAddress}
                      onChange={e => updateState({ streetAddress: e.target.value })}
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
                      value={form.unit}
                      onChange={e => updateState({ unit: e.target.value })}
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
                        value={form.city}
                        onChange={e => updateState({ city: e.target.value })}
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
                        value={form.province}
                        onChange={e => updateState({ province: e.target.value })}
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
                        value={form.postalCode}
                        onChange={e => updateState({ postalCode: e.target.value })}
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
                        value={form.country}
                        onChange={e => updateState({ country: e.target.value })}
                        required
                      />
                    </div>

                  </div>

                </div>
              )}

              {/* VIRTUAL VENUE FIELDS */}
              {form.venueType === 'virtual' && (
                <div className="space-y-5">
                  <p className="text-sm text-base-content/60">
                    Virtual venues don't require a physical address. Please enter information into description.
                  </p>
                </div>
              )}

            </div>
          </section>

          {/* FORM FEEDBACK */}
          {message && (
            <div
              role={isError ? 'alert' : 'status'}
              className={`alert ${isError ? 'alert-error' : 'alert-info'
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
    </APIProvider>
  )
}
