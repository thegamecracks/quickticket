import { useEffect, useMemo, useRef, useState, type SubmitEvent } from 'react'
import { useNavigate } from 'react-router'
import { APIProvider, useMapsLibrary } from '@vis.gl/react-google-maps'
import axios from 'axios'
import PageLayout from '../../components/PageLayout'
import { api } from '../../lib/api'
import { useAuth } from '../../lib/auth'
import {
  geocodeAddress,
  reverseGeocodeCoords,
  type GeocodedAddress,
} from '../../lib/geocode'
import type { Point } from '../../lib/types'
import { isAdministrator, isOrganizationAdministrator } from '../account/types'
import type { VenueResponse } from '../events/types'
type AddressFields = GeocodedAddress

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

const emptyForm: VenueFormState = {
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

const ADDRESS_FIELDS = [
  'streetAddress',
  'unit',
  'city',
  'province',
  'postalCode',
  'country',
] as const

/** Combines the structured fields into the backend's location_name field. */
const buildLocationName = (form: VenueFormState): string =>
  form.venueType === 'physical'
    ? ADDRESS_FIELDS.map(field => form[field].trim())
      .filter(Boolean)
      .join(', ')
    : ''

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

  // The current API limits location_name to 128 characters.
  if (buildLocationName(form).length > 128) {
    return 'The combined location details exceed 128 characters. Please shorten the address or platform name.'
  }

  return undefined
}

/**
 * Diff a (trimmed) form state against the loaded venue to build the PATCH
 * body. Only changed fields are included — the backend PATCH is partial.
 *
 * `seedAddress` is the address the form was seeded with (from reverse
 * geocoding the venue's stored coordinates). When the user changed the
 * address, the returned `addressChanged` flag is set, `location_name` is
 * recomposed, and the caller must geocode to fill `location_coords`.
 */
const venueChanges = (
  form: VenueFormState,
  venue: VenueResponse,
  seedAddress: AddressFields,
): { changes: VenuePatch; addressChanged: boolean } => {
  const changes: VenuePatch = {}

  if (form.displayName !== venue.display_name) {
    changes.display_name = form.displayName
  }
  if (form.description !== venue.description) {
    changes.description = form.description
  }
  if (form.category !== venue.category) {
    changes.category = form.category
  }

  let addressChanged = false

  if (form.venueType === 'virtual') {
    if (venue.location_name !== '') changes.location_name = ''
    if (venue.location_coords !== null) changes.location_coords = null
  } else {
    addressChanged = ADDRESS_FIELDS.some(field => form[field] !== seedAddress[field])

    if (addressChanged) {
      changes.location_name = buildLocationName(form)
    }
  }

  return { changes, addressChanged }
}

/** Fields the venue PATCH endpoint accepts. */
type VenuePatch = Partial<
  Pick<
    VenueResponse,
    | 'display_name'
    | 'description'
    | 'category'
    | 'location_name'
    | 'location_coords'
  >
>

export function VenueForm({
  venueId,
  fixedOrganizationId,
  embedded,
  onCreated,
}: {
  venueId?: string
  /** Skip the organization picker and create in this organization (wizard). */
  fixedOrganizationId?: string
  /** Render the bare form (no page shell) for the create-event wizard. */
  embedded?: boolean
  /** Replaces the default post-create navigation (wizard advances a step). */
  onCreated?: (venue: VenueResponse) => void
}) {
  const isEdit = Boolean(venueId)
  const navigate = useNavigate()
  const { user } = useAuth()
  const geocodingLib = useMapsLibrary('geocoding')

  const [venue, setVenue] = useState<VenueResponse | null>(null)
  const [form, setForm] = useState<VenueFormState>(emptyForm)
  const [loading, setLoading] = useState(isEdit)
  const [loadError, setLoadError] = useState('')
  const [saving, setSaving] = useState(false)
  const [feedback, setFeedback] = useState<{
    error: boolean
    text: string
  } | null>(null)

  // Reverse-geocoded address the user started from; edits are detected
  // against this snapshot to decide whether to re-geocode on save.
  const seedAddressRef = useRef<AddressFields>(emptyForm)

  // True while stored coordinates are being reverse-geocoded into the
  // address fields; saving is blocked so edits are never compared against
  // an incomplete seed.
  const [addressSeeding, setAddressSeeding] = useState(false)

  // Only administrators of an organization can create venues in it.
  const adminMemberships = useMemo(
    () => user?.organization_members.filter(isAdministrator) ?? [],
    [user],
  )

  const [organizationId, setOrganizationId] = useState(fixedOrganizationId ?? '')
  const [adminOrgNames, setAdminOrgNames] = useState<
    Record<string, string>
  >({})

  useEffect(() => {
    if (isEdit || fixedOrganizationId || adminMemberships.length < 2) {
      if (!fixedOrganizationId && adminMemberships.length === 1) {
        setOrganizationId(adminMemberships[0].organization_id)
      }
      return
    }

    let active = true
    Promise.all(
      adminMemberships.map(member =>
        api
          .get<{ id: string; display_name: string }>(
            `/organizations/${member.organization_id}`,
          )
          .then(response => response.data),
      ),
    ).then(organizations => {
      if (!active) return
      setAdminOrgNames(
        Object.fromEntries(
          organizations.map(org => [org.id, org.display_name]),
        ),
      )
      setOrganizationId(previous => previous || organizations[0].id)
    })

    return () => {
      active = false
    }
  }, [isEdit, fixedOrganizationId, adminMemberships])

  useEffect(() => {
    if (!isEdit) return

    if (!venueId) {
      setLoadError('No venue was selected.')
      setLoading(false)
      return
    }

    let active = true
    setLoading(true)
    setLoadError('')
    seedAddressRef.current = emptyForm

    api.get<VenueResponse>(`/venues/${venueId}`)
      .then(response => {
        if (!active) return

        const details = response.data
        setVenue(details)
        setForm({
          displayName: details.display_name,
          description: details.description,
          category: details.category,
          venueType: details.location_coords ? 'physical' : 'virtual',
          streetAddress: '',
          unit: '',
          city: '',
          province: '',
          postalCode: '',
          country: '',
        })
      })
      .catch(() => {
        if (active) {
          setLoadError('Unable to load this venue. Please try again.')
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [isEdit, venueId])

  // Seed the address fields from the stored coordinates once the
  // geocoding library is ready. The coordinates are the source of truth.
  useEffect(() => {
    if (!isEdit || !venue?.location_coords || !geocodingLib) return

    let active = true
    setAddressSeeding(true)

    reverseGeocodeCoords(geocodingLib, venue.location_coords)
      .then(address => {
        if (!active || !address) return
        seedAddressRef.current = address

        // Only fill fields the user hasn't started editing.
        setForm(previous => ({
          ...previous,
          streetAddress: previous.streetAddress || address.streetAddress,
          unit: previous.unit || address.unit,
          city: previous.city || address.city,
          province: previous.province || address.province,
          postalCode: previous.postalCode || address.postalCode,
          country: previous.country || address.country,
        }))
      })
      .finally(() => {
        if (active) setAddressSeeding(false)
      })

    return () => {
      active = false
    }
  }, [isEdit, venue, geocodingLib])

  const canEdit = isOrganizationAdministrator(user, venue?.organization.id ?? '')

  const updateField = (field: keyof VenueFormState, value: string) => {
    setForm(previous => ({ ...previous, [field]: value }))
    setFeedback(null)
  }

  const clearForm = () => {
    setForm(emptyForm)
    setFeedback(null)
  }

  const geocodeCurrentAddress = async (): Promise<Point | null> => {
    const locationName = buildLocationName(form)
    if (!locationName) return null

    const library = geocodingLib ??
      await google.maps.importLibrary('geocoding')

    return geocodeAddress(library, locationName)
  }

  const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!user || saving || addressSeeding) return
    if (isEdit && (!venueId || !venue || !canEdit)) return

    const formState = {
      ...form,
      displayName: form.displayName.trim(),
      description: form.description.trim(),
      category: form.category.trim(),
    }

    const error = validateVenueForm(formState)
    if (error) {
      setFeedback({ error: true, text: error })
      return
    }

    if (!isEdit && !organizationId) {
      setFeedback({
        error: true,
        text: 'You must be an administrator of an organization to create a venue.',
      })
      return
    }

    setSaving(true)
    setFeedback(null)

    try {
      if (isEdit && venue) {
        const { changes, addressChanged } = venueChanges(
          formState,
          venue,
          seedAddressRef.current,
        )

        if (addressChanged) {
          changes.location_coords = await geocodeCurrentAddress()
        }

        if (Object.keys(changes).length === 0) {
          setFeedback({ error: false, text: 'No changes to save.' })
          return
        }

        await api.patch(`/venues/${venueId}`, changes)

        setVenue(previous => (previous ? { ...previous, ...changes } : previous))

        setFeedback({ error: false, text: 'Venue updated successfully.' })
      } else {
        const response = await api.post<VenueResponse>('/venues', {
          organization_id: organizationId,
          display_name: formState.displayName,
          description: formState.description,
          category: formState.category,
          location_name: buildLocationName(formState),
          location_coords: formState.venueType === 'physical'
            ? await geocodeCurrentAddress()
            : null,
        })

        if (onCreated) {
          onCreated(response.data)
        } else {
          navigate(`/venue/${response.data.id}`)
        }
      }
    } catch (requestError) {
      let message = isEdit
        ? 'Could not save the venue. Please try again.'
        : 'Failed to create the venue. Please try again.'

      if (axios.isAxiosError(requestError)) {
        if (requestError.response?.status === 403) {
          message = 'You do not have permission to manage this venue.'
        }
      }

      setFeedback({ error: true, text: message })
    } finally {
      setSaving(false)
    }
  }

  const addressFieldsDisabled = saving || form.venueType === 'virtual'

  const renderTextField = (
    id: string,
    label: string,
    field: keyof VenueFormState,
    placeholder?: string,
    required?: boolean,
  ) => (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm font-medium">
        {label}
        {required && <span className="text-error"> *</span>}
      </label>

      <input
        id={id}
        type="text"
        className="input input-bordered w-full"
        placeholder={placeholder}
        value={form[field] as string}
        onChange={event => updateField(field, event.target.value)}
        required={required && !addressFieldsDisabled}
        disabled={addressFieldsDisabled}
      />
    </div>
  )

  const content = (
    <>
      {isEdit && loading ? (
        <p className="text-base-content/70">Loading venue details...</p>
      ) : isEdit && loadError ? (
        <div role="alert" className="alert alert-error">
          {loadError}
        </div>
      ) : user === undefined ? (
        <p className="text-base-content/70">Checking permissions...</p>
      ) : isEdit && !canEdit ? (
        <div role="alert" className="alert alert-error">
          Only an administrator of this venue's organization can edit it.
        </div>
      ) : !isEdit && adminMemberships.length === 0 ? (
        <div role="alert" className="alert alert-error">
          You must be an administrator of an organization to create a venue.
        </div>
      ) : (
        <div className="space-y-6">
          <p className="text-base-content/70">
            {isEdit
              ? "Update your venue's details below."
              : 'Add a venue to your organization to start hosting events.'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* BASIC INFORMATION */}
            <section className="space-y-5 rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm sm:p-6">
              <div>
                <label htmlFor="venueName" className="mb-2 block text-sm font-medium">
                  Venue Name <span className="text-error">*</span>
                </label>

                <input
                  id="venueName"
                  type="text"
                  className="input input-bordered w-full"
                  placeholder="e.g. Aurora Event Hall"
                  value={form.displayName}
                  onChange={event => updateField('displayName', event.target.value)}
                  required
                />
              </div>

              <div>
                <label
                  htmlFor="venueDescription"
                  className="mb-2 block text-sm font-medium"
                >
                  Description <span className="text-error">*</span>
                </label>

                <textarea
                  id="venueDescription"
                  className="textarea textarea-bordered h-32 w-full"
                  placeholder="Describe your venue, its atmosphere, and the types of events it can host..."
                  value={form.description}
                  onChange={event => updateField('description', event.target.value)}
                  maxLength={4096}
                  required
                />

                <p className="mt-1 text-right text-xs text-base-content/60">
                  {form.description.length}/4096
                </p>
              </div>

              <div>
                <label
                  htmlFor="venueCategory"
                  className="mb-2 block text-sm font-medium"
                >
                  Category <span className="text-error">*</span>
                </label>

                <input
                  id="venueCategory"
                  type="text"
                  className="input input-bordered w-full"
                  placeholder="e.g. Music, Conference, Art"
                  value={form.category}
                  onChange={event => updateField('category', event.target.value)}
                  maxLength={128}
                  required
                />
              </div>
            </section>

            {/* LOCATION INFORMATION */}
            <section className="space-y-4 rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm sm:p-6">
              <div>
                <h2 className="text-lg font-semibold">Location Information</h2>
                <p className="mt-1 text-sm text-base-content/60">
                  {isEdit
                    ? 'Coordinates from the saved venue are filled in below. Editing the address re-geocodes the venue.'
                    : 'Help attendees find your venue.'}
                </p>
              </div>

              {/* Venue Type */}
              <div>
                <label className="mb-3 block text-sm font-medium">Venue Type</label>

                <div className="flex flex-wrap gap-6">
                  <label className="flex cursor-pointer items-center gap-2">
                    <input
                      type="radio"
                      name="venueType"
                      className="radio radio-primary radio-sm"
                      checked={form.venueType === 'physical'}
                      onChange={() => {
                        updateField('venueType', 'physical')
                        if (form.country === '') updateField('country', 'Canada')
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
                      onChange={() => updateField('venueType', 'virtual')}
                    />
                    Virtual Venue
                  </label>
                </div>
              </div>

              {form.venueType === 'virtual' ? (
                <p className="text-sm text-base-content/60">
                  Virtual venues don't require a physical address. Please enter
                  information into the description.
                </p>
              ) : (
                <div className="space-y-5">
                  {renderTextField('streetAddress', 'Street Address', 'streetAddress', 'e.g. 123 Yonge Street', true)}
                  {renderTextField('unit', 'Unit / Suite', 'unit', 'e.g. Unit 200')}

                  <div className="grid gap-4 sm:grid-cols-2">
                    {renderTextField('city', 'City', 'city', 'e.g. Aurora', true)}
                    {renderTextField('province', 'Province / State', 'province', 'e.g. Ontario', true)}
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    {renderTextField('postalCode', 'Postal / ZIP Code', 'postalCode', 'e.g. L4G 1N2', true)}
                    {renderTextField('country', 'Country', 'country', 'e.g. Canada', true)}
                  </div>
                </div>
              )}
            </section>

            {/* Organization picker (create mode, multiple admin orgs only) */}
            {!isEdit && !fixedOrganizationId && adminMemberships.length > 1 && (
              <section className="rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm sm:p-6">
                <div>
                  <label htmlFor="venueOrganization" className="mb-2 block text-sm font-medium">
                    Organization <span className="text-error">*</span>
                  </label>

                  <select
                    id="venueOrganization"
                    className="select select-bordered w-full"
                    value={organizationId}
                    onChange={event => setOrganizationId(event.target.value)}
                  >
                    {adminMemberships.map(member => (
                      <option key={member.organization_id} value={member.organization_id}>
                        {adminOrgNames[member.organization_id] ?? member.organization_id}
                      </option>
                    ))}
                  </select>
                </div>
              </section>
            )}

            {/* FORM FEEDBACK */}
            {feedback && (
              <div
                role={feedback.error ? 'alert' : 'status'}
                className={`alert ${feedback.error ? 'alert-error' : 'alert-success'}`}
              >
                <span>{feedback.text}</span>
              </div>
            )}

            {/* FORM ACTIONS */}
            <div className="flex flex-wrap justify-end gap-3 border-t border-base-300 pt-5">
              {isEdit ? (
                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={saving}
                  onClick={() => navigate(`/venue/${venueId}`)}
                >
                  Cancel
                </button>
              ) : (
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={clearForm}
                >
                  Clear
                </button>
              )}

              <button
                type="submit"
                className="btn btn-primary"
                disabled={saving || addressSeeding}
              >
                {addressSeeding
                  ? 'Preparing address...'
                  : saving
                    ? isEdit ? 'Saving...' : 'Creating...'
                    : isEdit ? 'Save Changes' : 'Create Venue'}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  )

  if (embedded) return content

  return (
    <PageLayout
      title={isEdit ? 'Edit Venue' : 'Create Venue'}
      back={isEdit && venueId ? { to: `/venue/${venueId}` } : undefined}
    >
      {content}
    </PageLayout>
  )
}

/**
 * Create/edit venue page. Renders the full page shell around the shared
 * {@link VenueForm}; pass `venueId` to edit an existing venue.
 */
export default function VenueEditorPage({ venueId }: { venueId?: string }) {
  return (
    <APIProvider
      apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? ''}
      libraries={['geocoding']}
      onError={error => console.error('Google Maps failed to load:', error)}
    >
      <VenueForm venueId={venueId} />
    </APIProvider>
  )
}
