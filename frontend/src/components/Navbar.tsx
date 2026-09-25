import { Link, NavLink } from 'react-router'

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
        <a className="btn btn-ghost btn-sm">About</a>
      </nav>
      <div className="navbar-end">
        <a className="btn btn-primary btn-sm">Sign in</a>
      </div>
    </header>
  )
}
