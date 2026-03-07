import { Outlet, NavLink, useLocation } from 'react-router-dom'

const nav = [
  { to: '/', label: 'Dashboard' },
  { to: '/opportunities', label: 'Opportunities' },
  { to: '/product/new', label: 'Product Detail', hide: true },
  { to: '/cad', label: 'CAD Generator' },
  { to: '/simulator', label: 'Manufacturing Simulator' },
  { to: '/listings', label: 'Listing Studio' },
  { to: '/imports', label: 'Data Imports' },
  { to: '/settings', label: 'Settings' },
].filter((x) => !('hide' in x && x.hide))

export function AppLayout() {
  const location = useLocation()
  const isProductDetail = location.pathname.startsWith('/product/') && location.pathname !== '/product/new'

  return (
    <div className="flex min-h-screen bg-[var(--forge-bg)]">
      <aside className="w-56 shrink-0 border-r border-[var(--forge-border)] bg-[var(--forge-surface)] flex flex-col">
        <div className="p-4 border-b border-[var(--forge-border)]">
          <h1 className="text-lg font-semibold tracking-tight text-[var(--forge-text)]">
            ForgeFlow
          </h1>
          <p className="text-xs text-[var(--forge-text-muted)] mt-0.5">
            Product discovery engine
          </p>
        </div>
        <nav className="flex-1 p-2 space-y-0.5">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-[var(--forge-accent)]/20 text-[var(--forge-accent)]'
                    : 'text-[var(--forge-text-muted)] hover:bg-[var(--forge-border)] hover:text-[var(--forge-text)]'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
          {isProductDetail && (
            <NavLink
              to={location.pathname}
              className="block px-3 py-2 rounded-md text-sm font-medium bg-[var(--forge-accent)]/20 text-[var(--forge-accent)]"
            >
              Product Detail
            </NavLink>
          )}
        </nav>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
