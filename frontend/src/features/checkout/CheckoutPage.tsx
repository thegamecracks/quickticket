import { useParams } from 'react-router'

export default function CheckoutPage() {
  const { slug } = useParams<{ slug: string }>()

  return (
    <section className="mx-auto w-full max-w-3xl grow px-4 py-12">
      <h1 className="mb-4 text-3xl font-bold">Checkout</h1>
      <p className="text-base-content/70">
        Checkout for <code className="kbd kbd-sm">{slug}</code> coming soon.
      </p>
    </section>
  )
}
