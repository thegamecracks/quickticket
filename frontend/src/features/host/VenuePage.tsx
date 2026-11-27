import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import EventListItem from '../../components/EventListItem';
import GoogleMap from '../../components/GoogleMap';
import Markdown from '../../components/Markdown';
import PageLayout from '../../components/PageLayout';
import { SkeletonText } from '../../components/Skeleton';
import SkeletonImage from '../../components/SkeletonImage';
import { api } from '../../lib/api';
import { bannerUrl, thumbnailUrl, VENUE_PLACEHOLDER } from '../../lib/images';
import type { VenueEventResponse, VenueResponse } from '../events/types';

export default function VenuePage() {
  const { id } = useParams<{ id: string }>();

  const [venue, setVenue] = useState<VenueResponse | undefined>(undefined);

  useEffect(() => {
    const getVenue = async (): Promise<void> => {
      const res = await api.get<VenueResponse>(`/venues/${id}`);
      setVenue(res.data);
    };

    getVenue();
  }, []);

  return (
    <PageLayout title={venue?.display_name} fallbackTitle="Venue" back={{ to: '/events' }}>
      {!venue && <SkeletonText lines={6} />}
      {venue && (
        <div>
          <figure className="mb-4">
            <SkeletonImage
              key={venue.id}
              sources={[bannerUrl('venues', venue.id), thumbnailUrl('venues', venue.id), VENUE_PLACEHOLDER]}
              alt={venue.display_name}
              className="h-48 w-full rounded-xl object-cover"
            />
          </figure>
          <span className="text-2xl font-semibold block">
            Venue owned by{' '}
            <a className="link link-primary" href={`/organization/${venue?.organization.id}`}>
              {venue.organization.display_name}
            </a>
          </span>
          {/* Venue editing lives on the My Organization page now. */}
          <div className="mt-2">
            <div className="flex lg:flex-row flex-col gap-8">
              <div className="flex-1">
                <h3 className="font-semibold text-xl text-secondary">Description</h3>
                <Markdown content={venue.description} />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-xl">
                  <span className="text-secondary">Location:</span> {venue.location_name}
                </h3>
                {venue.location_coords ? (
                  <GoogleMap latitude={venue.location_coords.lat} longitude={venue.location_coords.lng} />
                ) : (
                  <p>not valid location</p>
                )}
              </div>
            </div>

            <h3 className="mt-8 font-semibold text-xl text-secondary">Upcoming Events</h3>
            {venue.events.length > 0 ? (
              <div>
                <p className="text-base-content/70">{venue.events.length} event(s) at this venue.</p>

                <ul className="list">
                  {venue.events.map((event: VenueEventResponse) => (
                    <EventListItem key={event.id} event={event} />
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-base-content/70">No upcoming events.</p>
            )}
          </div>
        </div>
      )}
    </PageLayout>
  );
}
