import { useParams } from 'react-router'
import NavigateBackBtn from '../../components/NavigateBack'
import PageLayout from '../../components/PageLayout'

export default function OrganizationPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <PageLayout title={org?.display_name} back>
    </PageLayout >
  )
}

