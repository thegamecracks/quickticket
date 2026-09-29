import { Route, Routes } from 'react-router'

import RootLayout from './layouts/RootLayout'
import AboutPage from './pages/AboutPage'
import HomePage from './pages/HomePage'
import CheckoutPage from './features/checkout/CheckoutPage'
import EventDetailPage from './features/events/EventDetailPage'
import EventsPage from './features/events/EventsPage'
import AccountSettingsPage from './features/account/AccountSettingsPage'
import { AuthProvider } from './lib/auth'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<RootLayout />}>
          <Route index element={<HomePage />} />
          <Route path="events" element={<EventsPage />} />
          <Route path="events/:slug" element={<EventDetailPage />} />
          <Route path="events/:slug/checkout" element={<CheckoutPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="settings" element={<AccountSettingsPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
