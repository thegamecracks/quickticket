import PageLayout from "../../components/PageLayout"
import { useAuth } from '../../lib/auth';
export default function AccountSettingsPage() {
  const { user } = useAuth();
  return (
    <PageLayout title="Account Settings">
      <div className='flex flex-col text-accent space-y-5'>
        <p>Id: {user?.account_id}</p>
        <p>Joined: {user?.created_at}</p>
        <p>Display Name: {user?.display_name}</p>
        <p>Email: {user?.email}</p>
        <p>Full Name: {user?.first_name} {user?.last_name}</p>
        <p>Addresses: {user?.addresses.join(" ")}</p>
      </div>
    </PageLayout>
  )
}
