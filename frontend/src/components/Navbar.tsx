import { Link, NavLink, useLocation } from 'react-router';
import { useAuth } from '../lib/auth';

export default function Navbar() {
  const { login, logout, user } = useAuth();
  const location = useLocation();

  const handleLogin = () => {
    login(`${window.location.origin}${location.pathname}`);
  };

  const handleLogout = () => {
    logout(`${window.location.origin}${location.pathname}`);
  };

  return (
    <header className="navbar bg-base-200 shadow-sm">
      <div className="navbar-start">
        <Link className="btn btn-ghost text-xl text-primary" to="/">
          QuickTicket
        </Link>
      </div>
      <nav className="navbar-center hidden gap-2 md:flex">
        <NavLink className="btn btn-ghost btn-md" to="/events">
          Events
        </NavLink>
        <NavLink className="btn btn-ghost btn-md" to="/createEvent">
          Host
        </NavLink>
        <NavLink className="btn btn-ghost btn-md" to="/about">
          About
        </NavLink>
      </nav>
      <div className="navbar-end">
        {user === undefined ? (
          <div className="skeleton h-8 rounded-field px-3">
            <span className="invisible text-xs font-semibold">Sign in</span>
          </div>
        ) : user ? (
          <div className="dropdown dropdown-end">
            <button type="button" tabIndex={0} className="avatar">
              <div className="w-10 rounded-full">
                <img alt="avatar" src={`https://ui-avatars.com/api/?name=${user?.first_name}+${user?.last_name}`} />
              </div>
            </button>
            <ul tabIndex={-1} className="menu dropdown-content bg-base-200 rounded-box z-1 w-52 shadow-sm">
              <li>
                <a href="/myEvents">My Events</a>
              </li>
              <li>
                <a href="/myOrganization">My Organization</a>
              </li>
              <li>
                <a href="/myTickets">My Tickets</a>
              </li>
              <li>
                <a href="/settings">Settings</a>
              </li>
              <li>
                <button type="button" onClick={handleLogout}>
                  Logout
                </button>
              </li>
            </ul>
          </div>
        ) : (
          <button type="button" className="btn btn-primary btn-sm" onClick={() => handleLogin()}>
            Sign in
          </button>
        )}
      </div>
    </header>
  );
}
