import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { ErrorBanner } from '../components/ErrorBanner'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { EmptyState } from '../components/EmptyState'
import type { ProductListItem } from '../types'

const statusLabel: Record<string, string> = {
  research_only: 'Research only',
  scored: 'Scored',
  cad_generated: 'CAD generated',
  manufacturing_simulated: 'Manufacturing simulated',
  listing_generated: 'Listing generated',
  prototype_candidate: 'Prototype candidate',
  archived: 'Archived',
}

export function Opportunities() {
  const navigate = useNavigate()
  const [products, setProducts] = useState<ProductListItem[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sort, setSort] = useState('updated_at')
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    Promise.all([
      api.products.list({ search: search || undefined, category: category || undefined, status: statusFilter || undefined, sort, order }),
      api.products.categories(),
    ])
      .then(([list, cats]) => {
        setProducts(list)
        setCategories(cats)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [search, category, statusFilter, sort, order])

  useEffect(() => {
    load()
  }, [load])

  if (loading) {
    return (
      <div className="p-8">
        <LoadingSpinner message="Loading opportunities…" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <ErrorBanner message={error} onRetry={load} />
        <Link to="/imports" className="mt-4 inline-block text-[var(--forge-accent)] text-sm">Import data →</Link>
      </div>
    )
  }

  return (
    <div className="p-8">
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-[var(--forge-text)]">Opportunities</h1>
          <p className="text-[var(--forge-text-muted)] mt-1">
            Compare and filter product candidates
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/product/new')}
          className="px-4 py-2 rounded-md bg-[var(--forge-accent)] text-white text-sm font-medium hover:opacity-90"
        >
          Add product
        </button>
      </header>

      <div className="flex flex-wrap gap-3 mb-6">
        <input
          type="search"
          placeholder="Search products…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 rounded-md border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)] placeholder:text-[var(--forge-text-muted)] min-w-[200px]"
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="px-3 py-2 rounded-md border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 rounded-md border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
        >
          <option value="">All statuses</option>
          {Object.entries(statusLabel).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
        <select
          value={`${sort}-${order}`}
          onChange={(e) => {
            const [s, o] = e.target.value.split('-') as [string, 'asc' | 'desc']
            setSort(s)
            setOrder(o)
          }}
          className="px-3 py-2 rounded-md border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
        >
          <option value="updated_at-desc">Last updated (newest)</option>
          <option value="updated_at-asc">Last updated (oldest)</option>
          <option value="name-asc">Name A–Z</option>
          <option value="name-desc">Name Z–A</option>
          <option value="opportunity_score-desc">Score (high first)</option>
          <option value="opportunity_score-asc">Score (low first)</option>
        </select>
      </div>

      <div className="rounded-lg border border-[var(--forge-border)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--forge-border)] bg-[var(--forge-surface)]">
                <th className="text-left p-3 font-medium text-[var(--forge-text-muted)]">Product</th>
                <th className="text-left p-3 font-medium text-[var(--forge-text-muted)]">Category</th>
                <th className="text-left p-3 font-medium text-[var(--forge-text-muted)]">Source</th>
                <th className="text-right p-3 font-medium text-[var(--forge-text-muted)]">Score</th>
                <th className="text-right p-3 font-medium text-[var(--forge-text-muted)]">Price</th>
                <th className="text-left p-3 font-medium text-[var(--forge-text-muted)]">Competition</th>
                <th className="text-left p-3 font-medium text-[var(--forge-text-muted)]">Status</th>
                <th className="text-right p-3 font-medium text-[var(--forge-text-muted)]">Updated</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr
                  key={p.id}
                  className="border-b border-[var(--forge-border)] hover:bg-[var(--forge-surface)]/50"
                >
                  <td className="p-3">
                    <Link to={`/product/${p.slug}`} className="font-medium text-[var(--forge-accent)]">
                      {p.name}
                    </Link>
                  </td>
                  <td className="p-3 text-[var(--forge-text-muted)]">{p.category}</td>
                  <td className="p-3 text-[var(--forge-text-muted)]">{p.source}</td>
                  <td className="p-3 text-right">
                    {p.opportunity_score != null ? p.opportunity_score.toFixed(1) : '—'}
                  </td>
                  <td className="p-3 text-right">
                    {p.estimated_price != null ? `$${p.estimated_price.toFixed(2)}` : '—'}
                  </td>
                  <td className="p-3 text-[var(--forge-text-muted)]">
                    {p.competition_level ?? '—'}
                  </td>
                  <td className="p-3">
                    <span className="text-[var(--forge-text-muted)]">
                      {statusLabel[p.status] ?? p.status}
                    </span>
                  </td>
                  <td className="p-3 text-right text-[var(--forge-text-muted)]">
                    {new Date(p.updated_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {products.length === 0 && (
          <div className="p-8">
            <EmptyState
              title={search || category || statusFilter ? 'No products match your filters' : 'No products yet'}
              description={search || category || statusFilter ? 'Try different search or filters.' : 'Import a CSV or add a product to get started.'}
              actionLabel={search || category || statusFilter ? undefined : 'Add product'}
              onAction={search || category || statusFilter ? undefined : () => navigate('/product/new')}
            />
          </div>
        )}
      </div>
    </div>
  )
}
