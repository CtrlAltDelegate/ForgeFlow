import { useLocation } from 'react-router-dom'

const titles: Record<string, string> = {
  '/cad': 'CAD Generator',
  '/simulator': 'Manufacturing Simulator',
  '/listings': 'Listing Studio',
  '/imports': 'Data Imports',
  '/settings': 'Settings',
}

export function Placeholder() {
  const { pathname } = useLocation()
  const title = titles[pathname] ?? 'Page'

  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold text-[var(--forge-text)]">{title}</h1>
      <p className="text-[var(--forge-text-muted)] mt-2">
        This section will be implemented in a later phase.
      </p>
    </div>
  )
}
