
import { useEffect, useState, type SubmitEvent } from 'react'
import { useNavigate, useParams } from 'react-router'
import { APIProvider, useMapsLibrary } from '@vis.gl/react-google-maps'
import axios from 'axios'
import PageLayout from '../../components/PageLayout'
import { api } from '../../lib/api'
import { useAuth } from '../../lib/auth'
import type { Point } from '../../lib/types'
import { isAdministrator } from '../account/types'
import type { VenueResponse } from '../events/types'

type VenueForm = {
  display_name: string
  description: string
  theme: string
  location_name: string
}

function EditVenueForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const geocodingLib = useMapsLibrary('geocoding')

  const [venue, setVenue] = useState<VenueResponse | null>(null)
  const [form, setForm] = useState<VenueForm>({
    display_name: '',
    description: '',
    theme: '',
    location_name: '',
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [feedback, setFeedback] = useState<{
    error: boolean
    text: string
  } | null>(null)

  useEffect(() => {
    if (!id) {
      setLoadError('No venue was selected.')
      setLoading(false)
      return
    }

    let active = true
    setLoading(true)
    setLoadError('')

    api.get<VenueResponse>(`/venues/${id}`)
      .then(response => {
        if (!active) return

        const details = response.data
        setVenue(details)
        setForm({
          display_name: details.display_name,
          description: details.description,
          theme: details.theme,
          location_name: details.location_name,
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
  }, [id])

  const canEdit = Boolean(
    venue && user?.organization_members.some(member =>
      member.organization_id === venue.organization.id &&
      isAdministrator(member)
    )
  )

  const updateField = (field: keyof VenueForm, value: string) => {
    setForm(previous => ({ ...previous, [field]: value }))
    setFeedback(null)
  }

  const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!id || !venue || !canEdit || saving) return

    const displayName = form.display_name.trim()
    const description = form.description.trim()
    const theme = form.theme.trim()
    const locationName = form.location_name.trim()

    if (!displayName || !description || !theme) {
      setFeedback({
        error: true,
        text: 'Please complete all required fields.',
      })
      return
    }

    if (locationName.length > 128) {
      setFeedback({
        error: true,
        text: 'Location must be 128 characters or fewer.',
      })
      return
    }

    setSaving(true)
    setFeedback(null)

    const locationChanged = locationName !== venue.location_name
    let locationCoords: Point | null = venue.location_coords

    if (locationChanged) {
      locationCoords = null

      if (locationName) {
        try {
          const lib = geocodingLib ??
            await google.maps.importLibrary('geocoding')

          const { results } = await new lib.Geocoder().geocode({
            address: locationName,
          })

          const position = results[0]?.geometry.location

          if (position) {
            locationCoords = {
              lat: position.lat(),
              long: position.lng(),
            }
          }
        } catch (error) {
          console.warn('Could not geocode venue location.', error)
        }
      }
    }

    const changes = {
      display_name: displayName,
      description,
      theme,
      location_name: locationName,
      ...(locationChanged
        ? { location_coords: locationCoords }
        : {}),
    }

    try {
      await api.patch(`/venues/${id}`, changes)

      setVenue(previous =>
        previous ? { ...previous, ...changes } : previous
      )

      setFeedback({
        error: false,
        text: 'Venue updated successfully.',
      })
    } catch (error) {
      let message = 'Could not save the venue. Please try again.'

      if (axios.isAxiosError(error)) {
        if (error.response?.status === 403) {
          message = 'You do not have permission to edit this venue.'
        }

        if (error.response?.status === 501) {
          message = 'Editing is not available yet. Backend update is needed.'
        }
      }

      setFeedback({ error: true, text: message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <PageLayout
      title="Edit Venue"
      back={{ to: id ? `/venue/${id}` : '/events' }}
    >
      {loading ? (
        <p className="text-base-content/70">
          Loading venue details...
        </p>
      ) : loadError ? (
        <div role="alert" className="alert alert-error">
          {loadError}
        </div>
      ) : user === undefined ? (
        <p className="text-base-content/70">
          Checking permissions...
        </p>
      ) : !canEdit ? (
        <div role="alert" className="alert alert-error">
          Only an administrator of this venue's organization can edit it.
        </div>
      ) : (
        <div className="space-y-6">
          <p className="text-base-content/70">
            Update your venue's details below.
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <section className="space-y-5 rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm sm:p-6">
              <div>
                <label
                  htmlFor="editVenueName"
                  className="mb-2 block text-sm font-medium"
                >
                  Venue Name <span className="text-error">*</span>
                </label>

                <input
                  id="editVenueName"
                  className="input input-bordered w-full"
                  value={form.display_name}
                  onChange={event =>
                    updateField('display_name', event.target.value)
                  }
                  required
                />
              </div>

              <div>
                <label
                  htmlFor="editVenueDescription"
                  className="mb-2 block text-sm font-medium"
                >
                  Description <span className="text-error">*</span>
                </label>

                <textarea
                  id="editVenueDescription"
                  className="textarea textarea-bordered h-32 w-full"
                  value={form.description}
                  onChange={event =>
                    updateField('description', event.target.value)
                  }
                  maxLength={4096}
                  required
                />

                <p className="mt-1 text-right text-xs text-base-content/60">
                  {form.description.length}/4096
                </p>
              </div>

              <div>
                <label
                  htmlFor="editVenueTheme"
                  className="mb-2 block text-sm font-medium"
                >
                  Theme <span className="text-error">*</span>
                </label>

                <input
                  id="editVenueTheme"
                  className="input input-bordered w-full"
                  value={form.theme}
                  onChange={event =>
                    updateField('theme', event.target.value)
                  }
                  maxLength={128}
                  required
                />
              </div>
            </section>

            <section className="space-y-4 rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm sm:p-6">
              <div>
                <h2 className="text-lg font-semibold">
                  Location Information
                </h2>
                <p className="mt-1 text-sm text-base-content/60">
                  Edit the full address. For virtual venues,
                  include online details in the description.
                </p>
              </div>

              <div>
                <label
                  htmlFor="editVenueLocation"
                  className="mb-2 block text-sm font-medium"
                >
                  Venue Location
                </label>

                <input
                  id="editVenueLocation"
                  className="input input-bordered w-full"
                  placeholder="e.g. 123 Yonge Street, Aurora, Ontario, Canada"
                  value={form.location_name}
                  onChange={event =>
                    updateField('location_name', event.target.value)
                  }
                  maxLength={128}
                />
              </div>
            </section>

            {feedback && (
              <div
                role={feedback.error ? 'alert' : 'status'}
                className={`alert ${
                  feedback.error ? 'alert-error' : 'alert-success'
                }`}
              >
                {feedback.text}
              </div>
            )}

            <div className="flex flex-wrap justify-end gap-3 border-t border-base-300 pt-5">
              <button
                type="button"
                className="btn btn-ghost"
                disabled={saving}
                onClick={() => navigate(`/venue/${id}`)}
              >
                Cancel
              </button>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      )}
    </PageLayout>
  )
}

export default function EditVenuePage() {
  return (
    <APIProvider
      apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? ''}
      libraries={['geocoding']}
      onError={error =>
        console.error('Google Maps failed to load:', error)
      }
    >
      <EditVenueForm />
    </APIProvider>
  )
}
