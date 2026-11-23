import { useParams } from 'react-router'

import PageLayout from '../../components/PageLayout'
import EventForm from './EventForm'

export default function EditEventPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <PageLayout title="Edit Event">
      <EventForm eventId={id ?? ''} />
    </PageLayout>
  )
}
