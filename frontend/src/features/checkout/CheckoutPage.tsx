import { useParams } from 'react-router'
import PageLayout from '../../components/PageLayout'

export default function CheckoutPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <PageLayout title="Checkout" back={{ to: `/events/${id}` }}>
      <p className="text-base-content/70">
        Checkout for <code className="kbd kbd-sm">{id}</code> coming soon.
      </p>
    </PageLayout>
  )
}
