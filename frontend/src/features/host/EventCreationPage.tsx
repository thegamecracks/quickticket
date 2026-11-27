import { APIProvider } from '@vis.gl/react-google-maps';
import { useEffect, useState } from 'react';
import { Link } from 'react-router';

import PageLayout from '../../components/PageLayout';
import { SkeletonRows } from '../../components/Skeleton';
import { api } from '../../lib/api';
import { useAuth } from '../../lib/auth';
import { isAdministrator } from '../account/types';
import type { VenueResponse } from '../events/types';
import type { OrganizationResponse, OrganizationVenue } from '../organizations/types';
import EventForm from './EventForm';
import { OrganizationForm } from './OrganizationForm';
import { VenueForm } from './VenueForm';

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
});

/**
 * Create-event wizard. The organization (when missing) and a venue are
 * always resolved before the event details: the venue step offers every
 * existing venue in a dropdown or the venue form to create a new one, and
 * either choice continues to the event form. Going back to the venue step
 * is allowed (nothing is un-created by it) — the organization step is not,
 * since an organization cannot be un-created.
 */
export default function EventCreationPage() {
  const { user } = useAuth();

  // A user owns at most one organization; any administrator membership is it.
  const membershipOrgId = user?.organization_members.find(isAdministrator)?.organization_id;

  const [org, setOrg] = useState<OrganizationResponse | null>(null);
  const [orgError, setOrgError] = useState(false);

  // Venue step presentation: choose an existing venue or open the form.
  // Defaults to the choice UI whenever venues exist (including a venue just
  // created in the flow), otherwise straight to the form; the buttons below
  // override that default until the organization changes again.
  const [venueModeOverride, setVenueModeOverride] = useState<'select' | 'create' | null>(null);
  const [venueChoice, setVenueChoice] = useState('');
  const [selectedVenueId, setSelectedVenueId] = useState<string | null>(null);

  useEffect(() => {
    if (!membershipOrgId) return;

    let active = true;

    api
      .get<OrganizationResponse>(`/organizations/${membershipOrgId}`)
      .then((response) => {
        if (active) setOrg(response.data);
      })
      .catch(() => {
        if (active) setOrgError(true);
      });

    return () => {
      active = false;
    };
  }, [membershipOrgId]);

  const needsOrg = org === null;
  const venueMode = venueModeOverride ?? (org && org.venues.length > 0 ? 'select' : 'create');
  const phase = needsOrg ? 'org' : selectedVenueId === null ? 'venue' : 'event';

  // The organization step only exists for organizers without one; venue and
  // event details always do.
  const totalSteps = (needsOrg ? 1 : 0) + 2;
  const venueStepNumber = needsOrg ? 2 : 1;
  const eventStepNumber = needsOrg ? 3 : 2;

  const stepHeading = (step: number, title: string) => (
    <p className="-mt-2 mb-7 text-sm text-base-content/60">
      Step {step} of {totalSteps}: {title}
    </p>
  );

  const hostingAs = org && (
    <p className="-mt-2 mb-7 text-sm text-base-content/60">
      Hosting as <span className="font-semibold text-base-content">{org.display_name}</span>
    </p>
  );

  const selectedVenue = org?.venues.find((venue) => venue.id === selectedVenueId);

  return (
    <PageLayout
      title="Create Event"
      actions={
        <>
          {phase === 'event' && (
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setSelectedVenueId(null)}>
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
      {user === undefined && <SkeletonRows rows={3} />}

      {/* No sign-in gate: a signed-out visitor uses the navbar's Sign in
          button. */}

      {/* Organization still loading */}
      {user && membershipOrgId && !org && !orgError && <SkeletonRows rows={4} />}

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
              <h2 className="text-lg font-semibold">Venue</h2>
              <p className="mt-1 text-xs text-base-content/55">
                Pick one of your venues, or create a new one for this event.
              </p>
            </div>

            <select
              className="select select-bordered w-full"
              aria-label="Venue"
              value={venueChoice || org.venues[0]?.id || ''}
              onChange={(event) => setVenueChoice(event.target.value)}
            >
              {org.venues.map((venue) => (
                <option key={venue.id} value={venue.id}>
                  {venue.display_name}
                </option>
              ))}
            </select>

            <div className="mt-4 flex flex-wrap justify-end gap-3">
              <button type="button" className="btn btn-outline" onClick={() => setVenueModeOverride('create')}>
                Create New Venue
              </button>

              <button
                type="button"
                className="btn btn-primary"
                disabled={!venueChoice && !org.venues[0]}
                onClick={() => setSelectedVenueId(venueChoice || org.venues[0]?.id || null)}
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
          {stepHeading(venueStepNumber, org.venues.length > 0 ? 'create a new venue' : 'add your first venue')}

          {org.venues.length > 0 && (
            <div className="mb-5">
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setVenueModeOverride('select')}>
                ← Back to venue selection
              </button>
            </div>
          )}

          <APIProvider
            apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? ''}
            libraries={['geocoding']}
            onError={(error) => console.error('Google Maps failed to load:', error)}
          >
            <VenueForm
              embedded
              fixedOrganizationId={org.id}
              onCreated={(venue) => {
                setOrg((previous) =>
                  previous ? { ...previous, venues: [toOrganizationVenue(venue), ...previous.venues] } : previous,
                );
                setSelectedVenueId(venue.id);
              }}
            />
          </APIProvider>
        </>
      )}

      {/* Step: event details */}
      {org && phase === 'event' && selectedVenue && (
        <>
          {hostingAs}
          {stepHeading(eventStepNumber, 'event details')}

          <EventForm venue={selectedVenue} />
        </>
      )}
    </PageLayout>
  );
}
