import { useEffect, useState, type SubmitEvent } from 'react'
import { useNavigate } from 'react-router'
import axios from 'axios'
import PageLayout from '../../components/PageLayout'
import { SkeletonText } from '../../components/Skeleton'
import { api } from '../../lib/api'
import { useAuth } from '../../lib/auth'
import { isAdministrator, isOrganizationAdministrator } from '../account/types'
import type { OrganizationResponse } from '../organizations/types'

// Mirrors backend validators.DisplayNameField (3–128 characters).
const DISPLAY_NAME_MIN = 3
const DISPLAY_NAME_MAX = 128

type OrganizationFormState = {
  displayName: string
}

const emptyForm: OrganizationFormState = {
  displayName: '',
}

/** Returns an error message, or undefined when the form is valid. */
const validateOrganizationForm = (
  form: OrganizationFormState,
): string | undefined => {
  const name = form.displayName.trim()

  if (!name) {
    return 'Please enter an organization name.'
  }
  if (name.length < DISPLAY_NAME_MIN || name.length > DISPLAY_NAME_MAX) {
    return `The organization name must be ${DISPLAY_NAME_MIN}–${DISPLAY_NAME_MAX} characters.`
  }

  return undefined
}

/**
 * Create/edit organization form. An organization is just a name, so this is
 * the VenueForm pattern with only the display-name field: pass `organizationId`
 * to edit an existing organization, or nothing to create one.
 *
 * `embedded` renders the bare form (no page shell) for the create-event
 * wizard; `onCreated` replaces the default post-create navigation.
 */
export function OrganizationForm({
  organizationId,
  embedded,
  onCreated,
}: {
  organizationId?: string
  embedded?: boolean
  onCreated?: (organization: OrganizationResponse) => void
}) {
  const isEdit = Boolean(organizationId)
  const navigate = useNavigate()
  const { user, refreshUser } = useAuth()

  const [organization, setOrganization] = useState<OrganizationResponse | null>(null)
  const [form, setForm] = useState<OrganizationFormState>(emptyForm)
  const [loading, setLoading] = useState(isEdit)
  const [loadError, setLoadError] = useState('')
  const [saving, setSaving] = useState(false)
  const [feedback, setFeedback] = useState<{
    error: boolean
    text: string
  } | null>(null)

  // A user can only ever own one organization (the backend rejects a second
  // with "Already owns an organization"), so any administrator membership
  // means the create form is off-limits.
  const adminMemberships = user?.organization_members.filter(isAdministrator) ?? []

  useEffect(() => {
    if (!isEdit) return

    let active = true
    // `loading` starts as `isEdit` and is only turned off in the callbacks
    // below, so no synchronous setState is needed here.

    api
      .get<OrganizationResponse>(`/organizations/${organizationId}`)
      .then(response => {
        if (!active) return

        setOrganization(response.data)
        setForm({ displayName: response.data.display_name })
      })
      .catch(() => {
        if (active) {
          setLoadError('Unable to load this organization. Please try again.')
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [isEdit, organizationId])

  // Only administrators of an organization (the backend OWNER flag) can edit it.
  const canEdit = isOrganizationAdministrator(user, organizationId ?? '')

  const updateField = (field: keyof OrganizationFormState, value: string) => {
    setForm(previous => ({ ...previous, [field]: value }))
    setFeedback(null)
  }

  const clearForm = () => {
    setForm(emptyForm)
    setFeedback(null)
  }

  const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!user || saving) return
    if (isEdit && (!organizationId || !organization || !canEdit)) return

    const formState = {
      ...form,
      displayName: form.displayName.trim(),
    }

    const error = validateOrganizationForm(formState)
    if (error) {
      setFeedback({ error: true, text: error })
      return
    }

    setSaving(true)
    setFeedback(null)

    try {
      if (isEdit && organization) {
        if (formState.displayName === organization.display_name) {
          setFeedback({ error: false, text: 'No changes to save.' })
          return
        }

        await api.patch(`/organizations/${organizationId}`, {
          display_name: formState.displayName,
        })

        setOrganization(previous =>
          previous ? { ...previous, display_name: formState.displayName } : previous,
        )

        setFeedback({ error: false, text: 'Organization updated successfully.' })
      } else {
        const response = await api.post<OrganizationResponse>('/organizations', {
          display_name: formState.displayName,
        })

        // The created membership only exists on the backend; refetch the
        // profile so membership-dependent UI (wizard gates, My Organization)
        // sees it without a page reload.
        await refreshUser()

        if (onCreated) {
          onCreated(response.data)
        } else {
          navigate('/myOrganization')
        }
      }
    } catch (requestError) {
      let message = isEdit
        ? 'Could not save the organization. Please try again.'
        : 'Failed to create the organization. Please try again.'

      if (axios.isAxiosError(requestError)) {
        const status = requestError.response?.status

        if (status === 403) {
          message = 'You do not have permission to manage this organization.'
        } else if (status === 400) {
          message = 'You already own an organization.'
        }
      }

      setFeedback({ error: true, text: message })
    } finally {
      setSaving(false)
    }
  }

  const content = (
    <>
      {isEdit && loading ? (
        <SkeletonText lines={2} />
      ) : isEdit && loadError ? (
        <div role="alert" className="alert alert-error">
          {loadError}
        </div>
      ) : user === undefined ? (
        <p className="text-base-content/70">Checking permissions...</p>
      ) : isEdit && !canEdit ? (
        <div role="alert" className="alert alert-error">
          Only an administrator of this organization can edit it.
        </div>
      ) : !isEdit && adminMemberships.length > 0 ? (
        <div role="alert" className="alert alert-error">
          You already own an organization.
        </div>
      ) : (
        <div className="space-y-6">
          <p className="text-base-content/70">
            {isEdit
              ? "Update your organization's name below."
              : 'Create an organization to start hosting venues and events.'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* BASIC INFORMATION */}
            <section className="space-y-5 rounded-xl border border-base-300 bg-base-100 p-5 shadow-sm sm:p-6">
              <div>
                <label
                  htmlFor="organizationName"
                  className="mb-2 block text-sm font-medium"
                >
                  Organization Name <span className="text-error">*</span>
                </label>

                <input
                  id="organizationName"
                  type="text"
                  className="input input-bordered w-full"
                  placeholder="e.g. Aurora Community Events"
                  value={form.displayName}
                  onChange={event => updateField('displayName', event.target.value)}
                  minLength={DISPLAY_NAME_MIN}
                  maxLength={DISPLAY_NAME_MAX}
                  required
                />

                <p className="mt-1 text-right text-xs text-base-content/60">
                  {form.displayName.length}/{DISPLAY_NAME_MAX}
                </p>
              </div>
            </section>

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
            <div className="flex flex-wrap justify-end gap-3">
              {isEdit ? (
                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={saving}
                  onClick={() => navigate('/myOrganization')}
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

              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving
                  ? isEdit ? 'Saving...' : 'Creating...'
                  : isEdit ? 'Save Changes' : 'Create Organization'}
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
      title={isEdit ? 'Edit Organization' : 'Create Organization'}
      back={isEdit ? { to: '/myOrganization' } : undefined}
    >
      {content}
    </PageLayout>
  )
}

/**
 * Create/edit organization page. Renders the form; pass `organizationId` to
 * edit an existing organization.
 */
export default function OrganizationEditorPage({
  organizationId,
}: {
  organizationId?: string
}) {
  return <OrganizationForm organizationId={organizationId} />
}
