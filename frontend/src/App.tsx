import { Route, Routes } from 'react-router'

import RootLayout from './layouts/RootLayout'
import EventDetailPage from './pages/EventDetailPage'
import EventsPage from './pages/EventsPage'
import HomePage from './pages/HomePage'

export default function App() {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        <Route index element={<HomePage />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="events/:slug" element={<EventDetailPage />} />
      </Route>
    </Routes>
  )
}
