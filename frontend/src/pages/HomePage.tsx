export default function HomePage() {
  return (
    <>
      <section className="hero bg-gradient-to-b from-primary/10 to-base-100 py-20">
        <div className="hero-content text-center">
          <div className="max-w-lg">
            <h1 className="text-4xl font-bold md:text-5xl">
              Find your next event
            </h1>
            <p className="py-6 text-base-content/70">
              Browse and buy tickets for concerts, meetups, and local shows
              from independent organizers.
            </p>
            <div className="flex justify-center gap-2">
              <button className="btn btn-primary">Browse events</button>
              <button className="btn btn-outline">Host an event</button>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-12">
        <h2 className="mb-6 text-2xl font-semibold">Upcoming events</h2>
        <p className="text-base-content/70">
          Event listing will live on the events page.
        </p>
      </section>
    </>
  )
}
