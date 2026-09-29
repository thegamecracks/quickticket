import { Link, NavLink } from 'react-router'
import { MockUser } from '../lib/mocks'
import { useAuth } from '../lib/auth'

export default function Navbar() {
  const { login, logout, user } = useAuth();

  /* To be used when auth is figured out will replace inside of AuthProvider
   * const login = () => {
    window.location.assign(`${API_URL}/auth/login`);
  }*/

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
        {user ? (
          <div className="dropdown dropdown-end">
            <div tabIndex={0} role="button" className="avatar">
              <div className="w-10 rounded-full">
                <img alt='avatar' src={'https://ui-avatars.com/api/?name=' + user?.first_name + "+" + user?.last_name} />
              </div>
            </div>
            <ul tabIndex={-1}
              className="menu dropdown-content bg-base-200 rounded-box z-1 w-52 shadow-sm">
              <li><a>My Events</a></li>
              <li><a>My Tickets</a></li>
              <li><a href='/settings'>Settings</a></li>
              <li><a onClick={() => logout()}>Logout</a></li>
            </ul>
          </div>
        ) : (
          <button
            className="btn btn-primary btn-sm"
            onClick={() => login(MockUser)}
          >
            Sign in
          </button>
        )
        }
      </div>
    </header >
  )
}
