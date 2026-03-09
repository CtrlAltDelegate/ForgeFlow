import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { ErrorBanner } from '../components/ErrorBanner'
import { useToast } from '../contexts/ToastContext'
import type { ImportListItem, CsvPreviewResponse, ResearchDataCreate } from '../types'

const emptyResearch: ResearchDataCreate = {
  source_type: 'manual',
  keyword: null,
  listed_price: null,
  review_count: null,
  rating: null,
  estimated_sales: null,
  competitor_count: null,
  listing_count: null,
  listing_age_days: null,
  notes: null,
}

export function DataImports() {
  const navigate = useNavigate()
  const { showToast } = useToast()
  const [imports, setImports] = useState<ImportListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<CsvPreviewResponse | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [manualOpen, setManualOpen] = useState(false)
  const [manualSaving, setManualSaving] = useState(false)
  const [manualForm, setManualForm] = useState({ name: '', category: '', source: 'manual', ...emptyResearch })

  const loadImports = () => {
    api.imports
      .list()
      .then(setImports)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadImports()
  }, [])

  const handleTemplateDownload = () => {
    api.imports.template().then((csv) => {
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'forgeflow_import_template.csv'
      a.click()
      URL.revokeObjectURL(url)
    }).catch((e) => setError(e.message))
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setSelectedFile(file)
    setPreview(null)
    setError(null)
    api.imports
      .preview(file)
      .then(setPreview)
      .catch((e) => setError(e.message))
  }

  const handleUpload = () => {
    if (!selectedFile) return
    setUploading(true)
    setError(null)
    api.imports
      .upload(selectedFile)
      .then((r) => {
        showToast(`Imported ${r.record_count} products.`)
        setSelectedFile(null)
        setPreview(null)
        loadImports()
      })
      .catch((e) => setError(e.message))
      .finally(() => setUploading(false))
  }

  return (
    <div className="p-8">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold text-[var(--forge-text)]">Data Imports</h1>
        <p className="text-[var(--forge-text-muted)] mt-1">
          Upload CSV, download template, or add products manually
        </p>
      </header>

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onDismiss={() => setError(null)} />
        </div>
      )}

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
          <h2 className="text-lg font-medium text-[var(--forge-text)] mb-3">CSV upload</h2>
          <div className="flex flex-col gap-3">
            <a
              href="#"
              onClick={(e) => { e.preventDefault(); handleTemplateDownload() }}
              className="text-sm text-[var(--forge-accent)] hover:underline"
            >
              Download CSV template
            </a>
            <label className="block">
              <span className="text-sm text-[var(--forge-text-muted)]">Choose file</span>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                className="mt-1 block w-full text-sm text-[var(--forge-text-muted)] file:mr-2 file:rounded file:border-0 file:bg-[var(--forge-accent)] file:px-3 file:py-1 file:text-white"
              />
            </label>
            {selectedFile && (
              <p className="text-sm text-[var(--forge-text-muted)] mt-1 truncate max-w-full" title={selectedFile.name}>
                Selected: {selectedFile.name}
              </p>
            )}
            <button
              type="button"
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              className="mt-3 w-full sm:w-auto px-5 py-2.5 rounded-md bg-[var(--forge-accent)] text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? 'Uploading…' : selectedFile ? (preview?.valid ? `Import ${preview.row_count} products` : 'Import CSV') : 'Select a file, then click Import'}
            </button>
            {preview && (
              <div className="text-sm mt-3">
                <p className="text-[var(--forge-text-muted)]">
                  {preview.valid ? (
                    <span className="text-green-400">{preview.row_count} rows valid. Preview:</span>
                  ) : (
                    <span className="text-amber-400">Validation errors (you can still try Import):</span>
                  )}
                </p>
                {preview.errors.length > 0 && (
                  <ul className="mt-1 list-disc list-inside text-amber-400">
                    {preview.errors.slice(0, 5).map((e, i) => (
                      <li key={i}>Row {e.row}: {e.message}</li>
                    ))}
                  </ul>
                )}
                {preview.preview.length > 0 && (
                  <table className="mt-2 w-full text-xs">
                    <thead>
                      <tr className="text-left text-[var(--forge-text-muted)]">
                        <th>Name</th>
                        <th>Category</th>
                        <th>Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {preview.preview.slice(0, 5).map((row, i) => (
                        <tr key={i}>
                          <td>{row.name}</td>
                          <td>{row.category}</td>
                          <td>{row.listed_price ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
          <h2 className="text-lg font-medium text-[var(--forge-text)] mb-3">Manual entry</h2>
          <button
            type="button"
            onClick={() => setManualOpen(!manualOpen)}
            className="text-sm text-[var(--forge-accent)] hover:underline"
          >
            {manualOpen ? 'Hide form' : 'Add a product + research data'}
          </button>
          {manualOpen && (
            <form
              className="mt-4 space-y-3"
              onSubmit={async (e) => {
                e.preventDefault()
                if (!manualForm.name.trim() || !manualForm.category.trim()) {
                  setError('Name and category are required.')
                  return
                }
                setManualSaving(true)
                setError(null)
                try {
                  const product = await api.products.create({
                    name: manualForm.name.trim(),
                    category: manualForm.category.trim(),
                    source: manualForm.source || 'manual',
                    source_keyword: manualForm.keyword || null,
                    source_notes: manualForm.notes || null,
                  })
                  await api.products.addResearch(product.id, {
                    source_type: 'manual',
                    keyword: manualForm.keyword || null,
                    listed_price: manualForm.listed_price ?? null,
                    review_count: manualForm.review_count ?? null,
                    rating: manualForm.rating ?? null,
                    estimated_sales: manualForm.estimated_sales ?? null,
                    competitor_count: manualForm.competitor_count ?? null,
                    listing_count: manualForm.listing_count ?? null,
                    listing_age_days: manualForm.listing_age_days ?? null,
                    notes: manualForm.notes || null,
                  })
                  showToast(`Product "${product.name}" created.`)
                  setManualForm({ name: '', category: '', source: 'manual', ...emptyResearch })
                  setManualOpen(false)
                  loadImports()
                  navigate(`/product/${product.slug}`)
                } catch (err) {
                  setError(err instanceof Error ? err.message : 'Failed to create product')
                } finally {
                  setManualSaving(false)
                }
              }}
            >
              <div>
                <label className="block text-xs text-[var(--forge-text-muted)] mb-1">Product name *</label>
                <input
                  type="text"
                  value={manualForm.name}
                  onChange={(e) => setManualForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-[var(--forge-text)]"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-[var(--forge-text-muted)] mb-1">Category *</label>
                <input
                  type="text"
                  value={manualForm.category}
                  onChange={(e) => setManualForm((f) => ({ ...f, category: e.target.value }))}
                  className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-[var(--forge-text)]"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs text-[var(--forge-text-muted)] mb-1">Listed price</label>
                  <input
                    type="number"
                    step="0.01"
                    value={manualForm.listed_price ?? ''}
                    onChange={(e) => setManualForm((f) => ({ ...f, listed_price: e.target.value ? parseFloat(e.target.value) : null }))}
                    className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-[var(--forge-text)]"
                  />
                </div>
                <div>
                  <label className="block text-xs text-[var(--forge-text-muted)] mb-1">Review count</label>
                  <input
                    type="number"
                    value={manualForm.review_count ?? ''}
                    onChange={(e) => setManualForm((f) => ({ ...f, review_count: e.target.value ? parseInt(e.target.value, 10) : null }))}
                    className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-[var(--forge-text)]"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs text-[var(--forge-text-muted)] mb-1">Rating</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="5"
                    value={manualForm.rating ?? ''}
                    onChange={(e) => setManualForm((f) => ({ ...f, rating: e.target.value ? parseFloat(e.target.value) : null }))}
                    className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-[var(--forge-text)]"
                  />
                </div>
                <div>
                  <label className="block text-xs text-[var(--forge-text-muted)] mb-1">Competitors</label>
                  <input
                    type="number"
                    value={manualForm.competitor_count ?? ''}
                    onChange={(e) => setManualForm((f) => ({ ...f, competitor_count: e.target.value ? parseInt(e.target.value, 10) : null }))}
                    className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-[var(--forge-text)]"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-[var(--forge-text-muted)] mb-1">Keyword / notes</label>
                <input
                  type="text"
                  value={manualForm.keyword ?? ''}
                  onChange={(e) => setManualForm((f) => ({ ...f, keyword: e.target.value || null }))}
                  className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-[var(--forge-text)]"
                  placeholder="Source keyword or notes"
                />
              </div>
              <button
                type="submit"
                disabled={manualSaving}
                className="px-4 py-2 rounded-md bg-[var(--forge-accent)] text-white text-sm font-medium disabled:opacity-50"
              >
                {manualSaving ? 'Saving…' : 'Create product'}
              </button>
            </form>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-medium text-[var(--forge-text)] mb-4">Import history</h2>
        {loading ? (
          <p className="text-[var(--forge-text-muted)]">Loading…</p>
        ) : imports.length === 0 ? (
          <p className="text-[var(--forge-text-muted)]">No imports yet.</p>
        ) : (
          <div className="rounded-lg border border-[var(--forge-border)] overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--forge-border)] bg-[var(--forge-surface)]">
                  <th className="text-left p-3 font-medium text-[var(--forge-text-muted)]">Date</th>
                  <th className="text-left p-3 font-medium text-[var(--forge-text-muted)]">File</th>
                  <th className="text-left p-3 font-medium text-[var(--forge-text-muted)]">Type</th>
                  <th className="text-right p-3 font-medium text-[var(--forge-text-muted)]">Records</th>
                  <th className="text-left p-3 font-medium text-[var(--forge-text-muted)]">Status</th>
                </tr>
              </thead>
              <tbody>
                {imports.map((r) => (
                  <tr key={r.id} className="border-b border-[var(--forge-border)]">
                    <td className="p-3 text-[var(--forge-text-muted)]">
                      {new Date(r.imported_at).toLocaleString()}
                    </td>
                    <td className="p-3">{r.file_name ?? '—'}</td>
                    <td className="p-3 text-[var(--forge-text-muted)]">{r.source_type}</td>
                    <td className="p-3 text-right">{r.record_count}</td>
                    <td className="p-3">{r.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
