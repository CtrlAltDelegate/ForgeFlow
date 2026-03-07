import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../services/api'
import type { Product, ResearchDataCreate } from '../types'

function ResearchForm({
  productId,
  onSaved,
  onCancel,
  saving,
  setSaving,
}: {
  productId: number
  onSaved: () => void
  onCancel: () => void
  saving: boolean
  setSaving: (v: boolean) => void
}) {
  const [form, setForm] = useState<ResearchDataCreate>({
    source_type: 'manual',
    listed_price: null,
    review_count: null,
    rating: null,
    estimated_sales: null,
    competitor_count: null,
    listing_count: null,
    listing_age_days: null,
    notes: null,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.products.addResearch(productId, form)
      onSaved()
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 p-3 rounded border border-[var(--forge-border)] space-y-2">
      <div className="grid grid-cols-2 gap-2">
        <input
          type="number"
          step="0.01"
          placeholder="Listed price"
          value={form.listed_price ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, listed_price: e.target.value ? parseFloat(e.target.value) : null }))}
          className="px-2 py-1 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm"
        />
        <input
          type="number"
          placeholder="Review count"
          value={form.review_count ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, review_count: e.target.value ? parseInt(e.target.value, 10) : null }))}
          className="px-2 py-1 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm"
        />
        <input
          type="number"
          step="0.1"
          placeholder="Rating"
          value={form.rating ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, rating: e.target.value ? parseFloat(e.target.value) : null }))}
          className="px-2 py-1 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm"
        />
        <input
          type="number"
          placeholder="Competitors"
          value={form.competitor_count ?? ''}
          onChange={(e) => setForm((f) => ({ ...f, competitor_count: e.target.value ? parseInt(e.target.value, 10) : null }))}
          className="px-2 py-1 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm"
        />
      </div>
      <div className="flex gap-2">
        <button type="submit" disabled={saving} className="px-3 py-1 rounded bg-[var(--forge-accent)] text-white text-sm disabled:opacity-50">
          {saving ? 'Saving…' : 'Save'}
        </button>
        <button type="button" onClick={onCancel} className="px-3 py-1 rounded border border-[var(--forge-border)] text-sm">
          Cancel
        </button>
      </div>
    </form>
  )
}

const statusLabel: Record<string, string> = {
  research_only: 'Research only',
  scored: 'Scored',
  cad_generated: 'CAD generated',
  manufacturing_simulated: 'Manufacturing simulated',
  listing_generated: 'Listing generated',
  prototype_candidate: 'Prototype candidate',
  archived: 'Archived',
}

export function ProductDetail() {
  const { idOrSlug } = useParams<{ idOrSlug: string }>()
  const [product, setProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [scoreLoading, setScoreLoading] = useState(false)
  const [researchFormOpen, setResearchFormOpen] = useState(false)
  const [researchSaving, setResearchSaving] = useState(false)

  const refresh = () => {
    if (!idOrSlug) return
    api.products.get(idOrSlug).then(setProduct).catch((e) => setError(e.message))
  }

  useEffect(() => {
    if (!idOrSlug) return
    api.products
      .get(idOrSlug)
      .then(setProduct)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [idOrSlug])

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[40vh]">
        <p className="text-[var(--forge-text-muted)]">Loading product…</p>
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="p-8">
        <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4 text-red-400">
          {error ?? 'Product not found'}
        </div>
        <Link to="/opportunities" className="mt-4 inline-block text-[var(--forge-accent)]">
          ← Back to opportunities
        </Link>
      </div>
    )
  }

  const score = product.latest_opportunity_score

  return (
    <div className="p-8">
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <Link to="/opportunities" className="text-sm text-[var(--forge-text-muted)] hover:text-[var(--forge-accent)]">
            ← Opportunities
          </Link>
          <h1 className="text-2xl font-semibold text-[var(--forge-text)] mt-2">{product.name}</h1>
          <p className="text-[var(--forge-text-muted)] mt-1">
            {product.category} · {statusLabel[product.status] ?? product.status}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={scoreLoading || !product.research_data.length}
            onClick={async () => {
              if (!product?.id) return
              setScoreLoading(true)
              setError(null)
              try {
                await api.products.score(product.id)
                refresh()
              } catch (e) {
                setError(e instanceof Error ? e.message : 'Score failed')
              } finally {
                setScoreLoading(false)
              }
            }}
            className="px-4 py-2 rounded-md border border-[var(--forge-accent)] bg-[var(--forge-accent)]/20 text-[var(--forge-accent)] text-sm font-medium hover:bg-[var(--forge-accent)]/30 disabled:opacity-50"
          >
            {scoreLoading ? 'Scoring…' : 'Score opportunity'}
          </button>
          <button
            type="button"
            className="px-4 py-2 rounded-md border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)] text-sm font-medium hover:bg-[var(--forge-border)]"
          >
            Generate CAD
          </button>
          <button
            type="button"
            className="px-4 py-2 rounded-md border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)] text-sm font-medium hover:bg-[var(--forge-border)]"
          >
            Run simulation
          </button>
          <button
            type="button"
            className="px-4 py-2 rounded-md border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)] text-sm font-medium hover:bg-[var(--forge-border)]"
          >
            Generate listing
          </button>
          <button
            type="button"
            className="px-4 py-2 rounded-md bg-[var(--forge-accent)] text-white text-sm font-medium hover:opacity-90"
          >
            Mark as prototype candidate
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <section className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
            <h2 className="text-lg font-medium text-[var(--forge-text)] mb-3">Overview</h2>
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <dt className="text-[var(--forge-text-muted)]">Source</dt>
              <dd>{product.source}</dd>
              <dt className="text-[var(--forge-text-muted)]">Source keyword</dt>
              <dd>{product.source_keyword ?? '—'}</dd>
              <dt className="text-[var(--forge-text-muted)]">Created</dt>
              <dd>{new Date(product.created_at).toLocaleString()}</dd>
              <dt className="text-[var(--forge-text-muted)]">Updated</dt>
              <dd>{new Date(product.updated_at).toLocaleString()}</dd>
            </dl>
            {product.source_notes && (
              <p className="mt-3 text-sm text-[var(--forge-text-muted)]">{product.source_notes}</p>
            )}
          </section>

          <section className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
            <h2 className="text-lg font-medium text-[var(--forge-text)] mb-3">Research data</h2>
            {product.research_data.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[var(--forge-text-muted)]">
                      <th className="pb-2">Listed price</th>
                      <th className="pb-2">Reviews</th>
                      <th className="pb-2">Rating</th>
                      <th className="pb-2">Est. sales</th>
                      <th className="pb-2">Competitors</th>
                    </tr>
                  </thead>
                  <tbody>
                    {product.research_data.map((r) => (
                      <tr key={r.id} className="border-t border-[var(--forge-border)]">
                        <td className="py-2">{r.listed_price != null ? `$${r.listed_price}` : '—'}</td>
                        <td className="py-2">{r.review_count ?? '—'}</td>
                        <td className="py-2">{r.rating ?? '—'}</td>
                        <td className="py-2">{r.estimated_sales ?? '—'}</td>
                        <td className="py-2">{r.competitor_count ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-[var(--forge-text-muted)]">No research data yet.</p>
            )}
            <button
              type="button"
              onClick={() => setResearchFormOpen(!researchFormOpen)}
              className="mt-3 text-sm text-[var(--forge-accent)] hover:underline"
            >
              {researchFormOpen ? 'Cancel' : 'Add research data'}
            </button>
            {researchFormOpen && (
              <ResearchForm
                productId={product.id}
                onSaved={() => { setResearchFormOpen(false); refresh() }}
                onCancel={() => setResearchFormOpen(false)}
                saving={researchSaving}
                setSaving={setResearchSaving}
              />
            )}
          </section>
        </div>

        <div className="space-y-6">
          <section className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
            <h2 className="text-lg font-medium text-[var(--forge-text)] mb-3">Opportunity score</h2>
            {score ? (
              <>
                <div className="text-3xl font-bold text-[var(--forge-accent)]">
                  {score.total_score.toFixed(1)}
                </div>
                <p className="text-xs text-[var(--forge-text-muted)] mt-1">ForgeFlow Opportunity Score</p>
                <ul className="mt-4 space-y-2 text-sm">
                  <li className="flex justify-between">
                    <span className="text-[var(--forge-text-muted)]">Demand</span>
                    <span>{score.demand_score}</span>
                  </li>
                  <li className="flex justify-between">
                    <span className="text-[var(--forge-text-muted)]">Competition</span>
                    <span>{score.competition_score}</span>
                  </li>
                  <li className="flex justify-between">
                    <span className="text-[var(--forge-text-muted)]">Manufacturing</span>
                    <span>{score.manufacturing_score}</span>
                  </li>
                  <li className="flex justify-between">
                    <span className="text-[var(--forge-text-muted)]">Margin</span>
                    <span>{score.margin_score}</span>
                  </li>
                  <li className="flex justify-between">
                    <span className="text-[var(--forge-text-muted)]">Differentiation</span>
                    <span>{score.differentiation_score}</span>
                  </li>
                </ul>
                <p className="text-xs text-[var(--forge-text-muted)] mt-3">
                  Scored at {new Date(score.scored_at).toLocaleString()}
                </p>
              </>
            ) : (
              <p className="text-sm text-[var(--forge-text-muted)]">Not scored yet.</p>
            )}
          </section>

          <section className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
            <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">CAD status</h2>
            <p className="text-sm text-[var(--forge-text-muted)]">No CAD model yet.</p>
          </section>

          <section className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
            <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Manufacturing</h2>
            <p className="text-sm text-[var(--forge-text-muted)]">No simulation yet.</p>
          </section>

          <section className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
            <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Listing draft</h2>
            <p className="text-sm text-[var(--forge-text-muted)]">No listing yet.</p>
          </section>
        </div>
      </div>
    </div>
  )
}
