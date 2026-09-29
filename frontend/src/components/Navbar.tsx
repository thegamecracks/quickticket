import axios from 'axios'
import { Link, NavLink } from 'react-router'
import { API_URL } from '../lib/api'

export default function Navbar() {

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
          onClick={() => axios.post(`${API_URL}/auth/login`)}
        >
          Sign in
        </button>
      </div>
    </header>
  )
}
