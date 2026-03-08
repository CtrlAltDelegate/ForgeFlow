import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../services/api'
import { ErrorBanner } from '../components/ErrorBanner'
import { LoadingSpinner } from '../components/LoadingSpinner'
import type { ProductListItem, ListingResponse } from '../types'

export function ListingStudio() {
  const [searchParams] = useSearchParams()
  const productSlug = searchParams.get('product')

  const [products, setProducts] = useState<ProductListItem[]>([])
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null)
  const [listings, setListings] = useState<ListingResponse[]>([])
  const [selectedListing, setSelectedListing] = useState<ListingResponse | null>(null)

  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.products
      .list({ limit: 200 })
      .then((list) => {
        setProducts(list)
        if (productSlug && list.length > 0) {
          const p = list.find((x) => x.slug === productSlug)
          if (p) setSelectedProductId(p.id)
        }
        if (!selectedProductId && list.length > 0 && !productSlug) setSelectedProductId(list[0].id)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [productSlug])

  useEffect(() => {
    if (selectedProductId == null) {
      setListings([])
      setSelectedListing(null)
      return
    }
    api.listings
      .list(selectedProductId)
      .then((list) => {
        setListings(list)
        setSelectedListing(list[0] ?? null)
      })
      .catch((e) => setError(e.message))
  }, [selectedProductId])

  const handleGenerate = async () => {
    if (selectedProductId == null) return
    setGenerating(true)
    setError(null)
    try {
      const created = await api.listings.create(selectedProductId)
      setListings((prev) => [created, ...prev])
      setSelectedListing(created)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generate failed')
    } finally {
      setGenerating(false)
    }
  }

  const parseList = (s: string | null): string[] => {
    if (!s) return []
    try {
      const v = JSON.parse(s)
      return Array.isArray(v) ? v : []
    } catch {
      return []
    }
  }
  const bullets = parseList(selectedListing?.bullet_points_json ?? null)
  const tags = parseList(selectedListing?.tags_json ?? null)

  if (loading) {
    return (
      <div className="p-8">
        <LoadingSpinner message="Loading products…" />
      </div>
    )
  }

  return (
    <div className="p-8">
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-[var(--forge-text)]">Listing Studio</h1>
          <p className="text-[var(--forge-text-muted)] mt-1">
            Generate and edit marketplace listing content
          </p>
        </div>
        <div className="flex gap-2">
          <label className="block text-sm text-[var(--forge-text-muted)] self-center">Product</label>
          <select
            value={selectedProductId ?? ''}
            onChange={(e) => setSelectedProductId(e.target.value ? Number(e.target.value) : null)}
            className="px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)] min-w-[200px]"
          >
            <option value="">Select product</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating || selectedProductId == null}
            className="px-4 py-2 rounded-md bg-[var(--forge-accent)] text-white font-medium disabled:opacity-50"
          >
            {generating ? 'Generating…' : 'Generate listing'}
          </button>
        </div>
      </header>

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onDismiss={() => setError(null)} />
        </div>
      )}

      {!selectedListing ? (
        <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-8 text-center text-[var(--forge-text-muted)]">
          Select a product and click “Generate listing” to create a draft.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
              <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Title</h2>
              <p className="text-[var(--forge-text)]">{selectedListing.title ?? '—'}</p>
            </div>
            <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
              <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Short pitch</h2>
              <p className="text-sm text-[var(--forge-text)]">{selectedListing.short_pitch ?? '—'}</p>
            </div>
            <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
              <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Bullet points</h2>
              <ul className="list-disc list-inside text-sm text-[var(--forge-text)] space-y-1">
                {bullets.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
              <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Description</h2>
              <p className="text-sm text-[var(--forge-text)] whitespace-pre-wrap">{selectedListing.description ?? '—'}</p>
            </div>
          </div>
          <div className="space-y-4">
            <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
              <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Suggested price</h2>
              <p className="text-xl font-semibold text-[var(--forge-text)]">
                {selectedListing.suggested_price != null ? `$${selectedListing.suggested_price.toFixed(2)}` : '—'}
              </p>
            </div>
            <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
              <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Tags</h2>
              <p className="text-sm text-[var(--forge-text)]">{tags.join(', ')}</p>
            </div>
            <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
              <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Photo prompt</h2>
              <p className="text-sm text-[var(--forge-text)]">{selectedListing.photo_prompt ?? '—'}</p>
            </div>
            <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
              <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Why it could sell</h2>
              <p className="text-sm text-[var(--forge-text)]">{selectedListing.why_it_could_sell ?? '—'}</p>
            </div>
            <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
              <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Differentiation</h2>
              <p className="text-sm text-[var(--forge-text)]">{selectedListing.differentiation_angle ?? '—'}</p>
            </div>
          </div>
        </div>
      )}

      {listings.length > 1 && (
        <div className="mt-6 rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
          <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Versions</h2>
          <div className="flex flex-wrap gap-2">
            {listings.map((l) => (
              <button
                key={l.id}
                type="button"
                onClick={() => setSelectedListing(l)}
                className={`px-3 py-1 rounded text-sm ${selectedListing?.id === l.id ? 'bg-[var(--forge-accent)] text-white' : 'border border-[var(--forge-border)] text-[var(--forge-text-muted)]'}`}
              >
                v{l.version}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
