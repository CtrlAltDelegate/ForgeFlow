import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../services/api'
import type { ProductCreate as ProductCreateType, ResearchDataCreate } from '../types'

export function ProductCreate() {
  const navigate = useNavigate()
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<ProductCreateType & ResearchDataCreate>({
    name: '',
    category: '',
    source: 'manual',
    source_keyword: null,
    source_notes: null,
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
    if (!form.name.trim() || !form.category.trim()) {
      setError('Name and category are required.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const product = await api.products.create({
        name: form.name.trim(),
        category: form.category.trim(),
        source: form.source || 'manual',
        source_keyword: form.source_keyword || null,
        source_notes: form.source_notes || null,
      })
      await api.products.addResearch(product.id, {
        source_type: 'manual',
        keyword: form.source_keyword || null,
        listed_price: form.listed_price ?? null,
        review_count: form.review_count ?? null,
        rating: form.rating ?? null,
        estimated_sales: form.estimated_sales ?? null,
        competitor_count: form.competitor_count ?? null,
        listing_count: form.listing_count ?? null,
        listing_age_days: form.listing_age_days ?? null,
        notes: form.notes || null,
      })
      navigate(`/product/${product.slug}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create product')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-8">
      <header className="mb-6">
        <Link to="/opportunities" className="text-sm text-[var(--forge-text-muted)] hover:text-[var(--forge-accent)]">
          ← Opportunities
        </Link>
        <h1 className="text-2xl font-semibold text-[var(--forge-text)] mt-2">Add product</h1>
        <p className="text-[var(--forge-text-muted)] mt-1">Create a product and optional research data.</p>
      </header>

      {error && (
        <div className="mb-4 rounded-lg border border-red-500/50 bg-red-500/10 p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="max-w-xl space-y-4">
        <div>
          <label className="block text-sm text-[var(--forge-text-muted)] mb-1">Product name *</label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
            required
          />
        </div>
        <div>
          <label className="block text-sm text-[var(--forge-text-muted)] mb-1">Category *</label>
          <input
            type="text"
            value={form.category}
            onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
            className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
            required
          />
        </div>
        <div>
          <label className="block text-sm text-[var(--forge-text-muted)] mb-1">Source keyword / notes</label>
          <input
            type="text"
            value={form.source_keyword ?? ''}
            onChange={(e) => setForm((f) => ({ ...f, source_keyword: e.target.value || null }))}
            className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-[var(--forge-text-muted)] mb-1">Listed price</label>
            <input
              type="number"
              step="0.01"
              value={form.listed_price ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, listed_price: e.target.value ? parseFloat(e.target.value) : null }))}
              className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--forge-text-muted)] mb-1">Review count</label>
            <input
              type="number"
              value={form.review_count ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, review_count: e.target.value ? parseInt(e.target.value, 10) : null }))}
              className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--forge-text-muted)] mb-1">Rating</label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="5"
              value={form.rating ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, rating: e.target.value ? parseFloat(e.target.value) : null }))}
              className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--forge-text-muted)] mb-1">Competitors</label>
            <input
              type="number"
              value={form.competitor_count ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, competitor_count: e.target.value ? parseInt(e.target.value, 10) : null }))}
              className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
            />
          </div>
        </div>
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 rounded-md bg-[var(--forge-accent)] text-white font-medium disabled:opacity-50"
          >
            {saving ? 'Creating…' : 'Create product'}
          </button>
          <Link
            to="/opportunities"
            className="px-4 py-2 rounded-md border border-[var(--forge-border)] text-[var(--forge-text)]"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  )
}
