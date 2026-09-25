import { useParams } from 'react-router'

export default function EventDetailPage() {
  const { slug } = useParams<{ slug: string }>()

  return (
    <section className="mx-auto w-full max-w-3xl grow px-4 py-12">
      <h1 className="mb-4 text-3xl font-bold">{slug}</h1>
      <p className="text-base-content/70">
        Event details coming soon. This page will fetch data for the{' '}
        <code className="kbd kbd-sm">{slug}</code> slug from the API.
      </p>
    </section>
  )
}
