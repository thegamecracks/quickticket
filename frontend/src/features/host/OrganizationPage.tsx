import { useNavigate, useParams } from 'react-router'
import PageLayout from '../../components/PageLayout'
import { api } from '../../lib/api'
import { useEffect, useState } from 'react'
import type { OrganizationResponse } from '../organizations/types'
import SkeletonImage from '../../components/SkeletonImage'
import { SkeletonRows } from '../../components/Skeleton'

export default function OrganizationPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [org, setOrg] = useState<OrganizationResponse | undefined>(undefined)

  useEffect(() => {
    const getOrg = async (): Promise<void> => {
      const res = await api.get<OrganizationResponse>(`/organizations/${id}`);
      setOrg(res.data);
    }

    getOrg();
  }, [])

  const handleViewVenue = (id: string) => {
    navigate(`/venue/${id}`)
  }

  return (
    <PageLayout title={org?.display_name} back>
      {!org && <SkeletonRows rows={4} />}
      {org && (
        <ul className="list">
          {org.venues.map((venue) => (
            <li
              className="list-row max-sm:grid-cols-[auto_1fr]! max-sm:grid-flow-row!"
              key={venue.id}
            >
              <figure className="h-20 w-32 shrink-0 max-sm:row-span-2 max-sm:self-center overflow-hidden rounded-lg bg-base-300">

                <SkeletonImage
                  src={venue.thumbnail ? `/storage/${venue.thumbnail.id}` : 'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event'}
                  alt={venue.display_name}
                  className="h-full w-full object-cover"
                />
              </figure>
              <div className="max-sm:col-start-2">
                {venue.display_name}
              </div>
              <button className="btn btn-outline btn-primary max-sm:col-start-2! max-sm:row-start-2! self-start sm:self-center sm:justify-self-end" onClick={() => handleViewVenue(venue.id)}>View</button>
            </li>
          ))}
        </ul>
      )
      }
    </PageLayout >
  )
}
