import { useState } from 'react'
import { Link, NavLink } from 'react-router'
import AuthModal from './AuthModal'

export default function Navbar() {
  const [authOpen, setAuthOpen] = useState(false)

  return (
    <header className="navbar bg-base-200 shadow-sm">
      <div className="navbar-start">
        <Link className="btn btn-ghost text-xl text-primary" to="/">
          QuickTicket
        </Link>
      </div>
      <nav className="navbar-center hidden gap-2 md:flex">
        <NavLink className="btn btn-ghost btn-sm" to="/events">
          Events
        </NavLink>
        <NavLink className="btn btn-ghost btn-sm" to="/about">
          About
        </NavLink>
      </nav>
      <div className="navbar-end">
        <button
          className="btn btn-primary btn-sm"
          onClick={() => setAuthOpen(true)}
        >
          Sign in
        </button>
        <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
      </div>
    </header>
  )
}
