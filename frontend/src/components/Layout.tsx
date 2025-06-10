import { Link, Outlet, useLocation } from 'react-router-dom';

const menu = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/simulations', label: 'Simulations' },
  { to: '/templates', label: 'Templates' },
  { to: '/reports', label: 'Reports' },
  { to: '/settings', label: 'Settings' },
];

export default function Layout() {
  const location = useLocation();
  return (
    <div>
      <nav>
        {menu.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            style={{
              marginRight: 8,
              fontWeight: location.pathname === item.to ? 'bold' : 'normal',
            }}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
