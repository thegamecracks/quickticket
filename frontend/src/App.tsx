import { Route, Routes } from 'react-router';
import AccountSettingsPage from './features/account/AccountSettingsPage';
import CheckoutPage from './features/checkout/CheckoutPage';
import EventDetailPage from './features/events/EventDetailPage';
import EventsPage from './features/events/EventsPage';
import EditEventPage from './features/host/EditEventPage';
import EditOrganizationPage from './features/host/EditOrganizationPage';
import EditVenuePage from './features/host/EditVenuePage';
import EventCreationPage from './features/host/EventCreationPage';
import MyEventsPage from './features/host/MyEventsPage';
import MyOrganizationPage from './features/host/MyOrganizationPage';
import OrganizationPage from './features/host/OrganizationPage';
import VenuePage from './features/host/VenuePage';
import MyTicketsPage from './features/tickets/MyTicketsPage';
import TicketDetailPage from './features/tickets/TicketDetailPage';
import RootLayout from './layouts/RootLayout';
import { AuthProvider } from './lib/auth';
import AboutPage from './pages/AboutPage';
import HomePage from './pages/HomePage';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<RootLayout />}>
          <Route index element={<HomePage />} />
          <Route path="events" element={<EventsPage />} />
          <Route path="events/:id" element={<EventDetailPage />} />
          <Route path="events/:id/edit" element={<EditEventPage />} />
          <Route path="events/:id/checkout" element={<CheckoutPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="myEvents" element={<MyEventsPage />} />
          <Route path="myOrganization" element={<MyOrganizationPage />} />
          <Route path="createEvent" element={<EventCreationPage />} />
          <Route path="venue/:id/edit" element={<EditVenuePage />} />
          <Route path="myTickets" element={<MyTicketsPage />} />
          <Route path="myTickets/:id" element={<TicketDetailPage />} />
          <Route path="venue/:id" element={<VenuePage />} />
          <Route path="venue/:id/edit" element={<EditVenuePage />} />
          <Route path="organization/:id" element={<OrganizationPage />} />
          <Route path="organization/:id/edit" element={<EditOrganizationPage />} />
          <Route path="settings" element={<AccountSettingsPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
