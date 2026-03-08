import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { ErrorBanner } from '../components/ErrorBanner'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { EmptyState } from '../components/EmptyState'
import type { DashboardSummary as DashboardSummaryType } from '../types'

export function Dashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardSummaryType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    setError(null)
    api.dashboard
      .summary()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  if (loading) {
    return (
      <div className="p-8">
        <LoadingSpinner message="Loading dashboard…" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <ErrorBanner message={error} onRetry={load} />
        <Link to="/imports" className="mt-4 inline-block text-[var(--forge-accent)] text-sm">
          Import data →
        </Link>
      </div>
    )
  }

  if (!data) return null

  const { pipeline_stage_counts: stages } = data

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--forge-text)]">Dashboard</h1>
        <p className="text-[var(--forge-text-muted)] mt-1">
          Pipeline status and top opportunities
        </p>
      </header>

      {data.total_products === 0 && (
        <div className="mb-8">
          <EmptyState
            title="No products yet"
            description="Import a CSV or add a product manually to get started."
            actionLabel="Go to Data Imports"
            onAction={() => navigate('/imports')}
          />
        </div>
      )}

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard label="Total products" value={String(data.total_products)} />
        <MetricCard
          label="Avg opportunity score"
          value={data.average_opportunity_score != null ? data.average_opportunity_score.toFixed(1) : '—'}
        />
        <MetricCard
          label="Avg estimated margin"
          value={
            data.average_estimated_margin != null
              ? `$${data.average_estimated_margin.toFixed(2)}`
              : '—'
          }
        />
        <MetricCard
          label="Avg print time (min)"
          value={
            data.average_estimated_print_time_minutes != null
              ? data.average_estimated_print_time_minutes.toFixed(0)
              : '—'
          }
        />
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-medium text-[var(--forge-text)] mb-4">Pipeline stages</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          <StageCard label="Research only" count={stages.research_only} />
          <StageCard label="Scored" count={stages.scored} />
          <StageCard label="CAD generated" count={stages.cad_generated} />
          <StageCard label="Manufacturing simulated" count={stages.manufacturing_simulated} />
          <StageCard label="Listing generated" count={stages.listing_generated} />
          <StageCard label="Prototype candidate" count={stages.prototype_candidate} />
          <StageCard label="Archived" count={stages.archived} />
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
          <h2 className="text-lg font-medium text-[var(--forge-text)] mb-3">Top opportunity</h2>
          {data.top_opportunity ? (
            <Link
              to={`/product/${data.top_opportunity.slug}`}
              className="block p-3 rounded-md bg-[var(--forge-bg)] border border-[var(--forge-border)] hover:border-[var(--forge-accent)]/50"
            >
              <span className="font-medium text-[var(--forge-text)]">
                {data.top_opportunity.name}
              </span>
              <span className="block text-sm text-[var(--forge-text-muted)] mt-1">
                Score: {data.top_opportunity.total_score.toFixed(1)} · {data.top_opportunity.category}
              </span>
            </Link>
          ) : (
            <p className="text-[var(--forge-text-muted)] text-sm">No scored products yet.</p>
          )}
        </div>
        <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
          <h2 className="text-lg font-medium text-[var(--forge-text)] mb-3">
            Fastest to manufacture
          </h2>
          {data.fastest_to_manufacture ? (
            <Link
              to={`/product/${data.fastest_to_manufacture.slug}`}
              className="block p-3 rounded-md bg-[var(--forge-bg)] border border-[var(--forge-border)]"
            >
              {data.fastest_to_manufacture.name}
            </Link>
          ) : (
            <p className="text-[var(--forge-text-muted)] text-sm">Run simulations to see results.</p>
          )}
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-medium text-[var(--forge-text)] mb-4">Top 10 opportunities</h2>
        {data.top_opportunities.length > 0 ? (
          <div className="rounded-lg border border-[var(--forge-border)] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--forge-border)] bg-[var(--forge-surface)]">
                  <th className="text-left p-3 font-medium text-[var(--forge-text-muted)]">Product</th>
                  <th className="text-left p-3 font-medium text-[var(--forge-text-muted)]">Category</th>
                  <th className="text-right p-3 font-medium text-[var(--forge-text-muted)]">Score</th>
                </tr>
              </thead>
              <tbody>
                {data.top_opportunities.map((o) => (
                  <tr
                    key={o.id}
                    className="border-b border-[var(--forge-border)] hover:bg-[var(--forge-surface)]/50"
                  >
                    <td className="p-3">
                      <Link to={`/product/${o.slug}`} className="text-[var(--forge-accent)]">
                        {o.name}
                      </Link>
                    </td>
                    <td className="p-3 text-[var(--forge-text-muted)]">{o.category}</td>
                    <td className="p-3 text-right font-medium">{o.total_score.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-[var(--forge-text-muted)]">No opportunities yet. Import or add products.</p>
        )}
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <RecentActivity title="Recent imports" items={data.recent_imports} />
        <RecentActivity title="Recent CAD" items={data.recent_cad_generations} />
        <RecentActivity title="Recent listings" items={data.recent_listing_generations} />
      </section>
    </div>
  )
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
      <p className="text-xs font-medium uppercase tracking-wider text-[var(--forge-text-muted)]">
        {label}
      </p>
      <p className="text-2xl font-semibold text-[var(--forge-text)] mt-1">{value}</p>
    </div>
  )
}

function StageCard({ label, count }: { label: string; count: number }) {
  return (
    <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-3 text-center">
      <p className="text-2xl font-semibold text-[var(--forge-text)]">{count}</p>
      <p className="text-xs text-[var(--forge-text-muted)] mt-1">{label}</p>
    </div>
  )
}

function RecentActivity({
  title,
  items,
}: {
  title: string
  items: { id: number; name: string; slug: string; at: string }[]
}) {
  return (
    <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
      <h3 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">{title}</h3>
      <ul className="space-y-1">
        {items.slice(0, 5).map((item) => (
          <li key={`${item.slug}-${item.at}`}>
            <Link to={`/product/${item.slug}`} className="text-sm text-[var(--forge-accent)]">
              {item.name}
            </Link>
            <span className="text-xs text-[var(--forge-text-muted)] ml-2">
              {new Date(item.at).toLocaleDateString()}
            </span>
          </li>
        ))}
        {items.length === 0 && (
          <li className="text-sm text-[var(--forge-text-muted)]">None yet</li>
        )}
      </ul>
    </div>
  )
}
