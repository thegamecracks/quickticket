import { Route, Routes } from 'react-router'

import RootLayout from './layouts/RootLayout'
import AboutPage from './pages/AboutPage'
import HomePage from './pages/HomePage'
import CheckoutPage from './features/checkout/CheckoutPage'
import EventDetailPage from './features/events/EventDetailPage'
import EventsPage from './features/events/EventsPage'

export default function App() {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        <Route index element={<HomePage />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="events/:slug" element={<EventDetailPage />} />
        <Route path="events/:slug/checkout" element={<CheckoutPage />} />
        <Route path="about" element={<AboutPage />} />
      </Route>
    </Routes>
  )
}
