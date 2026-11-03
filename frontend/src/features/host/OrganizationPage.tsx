import { useNavigate, useParams } from 'react-router'
import PageLayout from '../../components/PageLayout'
import { api } from '../../lib/api'
import { useEffect, useState } from 'react'
import type { OrganizationResponse } from '../organizations/types'
import SkeletonImage from '../../components/SkeletonImage'

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
      {org && (
        <ul className="list">
          {org.venues.map((venue) => (
            <li className="list-row">
              <figure className="h-20 w-32 shrink-0 overflow-hidden rounded-lg bg-base-300">

                <SkeletonImage
                  src={venue.thumbnail ? `/storage/${venue.thumbnail.id}` : 'https://placehold.co/800x450/272c35/ffffff?text=QuickTicket+Event'}
                  alt={venue.display_name}
                  className="h-full w-full object-cover"
                />
              </figure>
              <div>
                {venue.display_name}
              </div>
              <button className="btn btn-primary" onClick={() => handleViewVenue(venue.id)}>View</button>
            </li>
          ))}
        </ul>
      )
      }
    </PageLayout >
  )
}
