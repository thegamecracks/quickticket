import { Outlet } from 'react-router'

import Footer from '../components/Footer'
import Navbar from '../components/Navbar'

export default function RootLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-base-100 text-base-content">
      <Navbar />
      <main className="flex flex-1 flex-col">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
