import PageLayout from "../../components/PageLayout"
import { useAuth } from '../../lib/auth';
import { isAdministrator } from './types';
export default function AccountSettingsPage() {
  const { user } = useAuth();
  return (
    <PageLayout title="Account Settings">
      <div className='flex flex-col text-accent space-y-5'>
        <p>Id: {user?.id}</p>
        <p>Joined: {user?.created_at}</p>
        <p>Display Name: {user?.display_name}</p>
        <p>Email: {user?.email}</p>
        <p>Full Name: {user?.first_name} {user?.last_name}</p>
        <p>
          Addresses:{' '}
          {user?.addresses.length
            ? user.addresses
                .map((a) => `${a.line_1}, ${a.city}, ${a.province} ${a.postal_code}`)
                .join(' | ')
            : 'none'}
        </p>
        <p>
          Organizations:{' '}
          {user?.organization_members.length
            ? user.organization_members
                .map((m) => (isAdministrator(m) ? `${m.organization_id} (admin)` : m.organization_id))
                .join(', ')
            : 'none'}
        </p>
      </div>
    </PageLayout>
  )
}
