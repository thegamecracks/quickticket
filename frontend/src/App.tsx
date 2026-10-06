import { Route, Routes } from 'react-router'

import RootLayout from './layouts/RootLayout'
import AboutPage from './pages/AboutPage'
import HomePage from './pages/HomePage'
import CheckoutPage from './features/checkout/CheckoutPage'
import EventDetailPage from './features/events/EventDetailPage'
import EventsPage from './features/events/EventsPage'
import AccountSettingsPage from './features/account/AccountSettingsPage'
import { AuthProvider } from './lib/auth'
import MyEventsPage from './features/host/MyEventsPage'
import MyTicketsPage from './features/tickets/MyTicketsPage'
import EventCreationPage from './features/host/EventCreationPage'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<RootLayout />}>
          <Route index element={<HomePage />} />
          <Route path="events" element={<EventsPage />} />
          <Route path="events/:id" element={<EventDetailPage />} />
          <Route path="events/:id/checkout" element={<CheckoutPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="myEvents" element={<MyEventsPage />} />
          <Route path="createEvent" element={<EventCreationPage />} />
          <Route path="myTickets" element={<MyTicketsPage />} />
          <Route path="settings" element={<AccountSettingsPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
