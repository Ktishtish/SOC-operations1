import { NavLink, Outlet } from 'react-router-dom'

export function Layout() {
  return (
    <div className="app-shell">
      <header className="topnav">
        <NavLink to="/" className="brand-mark">
          <div className="brand-glyph">◈</div>
          <div className="brand-word">
            SOCWatch
            <span>SOC Lab</span>
          </div>
        </NavLink>
        <nav className="nav-links">
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/scenarios">Scenarios</NavLink>
          <NavLink to="/knowledge">IR Playbook</NavLink>
        </nav>
      </header>
      <Outlet />
    </div>
  )
}
