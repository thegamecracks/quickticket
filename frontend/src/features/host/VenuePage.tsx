import { useParams } from 'react-router'
import NavigateBackBtn from '../../components/NavigateBack'

export default function VenuePage() {
  const { id } = useParams<{ id: string }>()

  return (
    <section className="mx-auto w-full max-w-3xl grow px-4 py-12">
      <h1 className="mb-4 text-3xl font-bold">Venue</h1>
      <NavigateBackBtn />
      <p className="text-base-content/70">
        Checkout for <code className="kbd kbd-sm">{id}</code> coming soon.
      </p>
    </section>
  )
}
