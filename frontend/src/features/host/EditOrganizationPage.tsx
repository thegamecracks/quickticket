import { useParams } from 'react-router'
import OrganizationEditorPage from './OrganizationForm'

export default function EditOrganizationPage() {
  const { id } = useParams<{ id: string }>()

  return <OrganizationEditorPage organizationId={id ?? ''} />
}
