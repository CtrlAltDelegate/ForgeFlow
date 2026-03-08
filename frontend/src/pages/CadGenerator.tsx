import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../services/api'
import { ErrorBanner } from '../components/ErrorBanner'
import { LoadingSpinner } from '../components/LoadingSpinner'
import type { ProductListItem, CadModelResponse, CadCreate } from '../types'

const PARAM_LABELS: Record<string, string> = {
  width: 'Width (mm)',
  height: 'Height (mm)',
  depth: 'Depth (mm)',
  length: 'Length (mm)',
  thickness: 'Thickness (mm)',
  wall_thickness: 'Wall thickness (mm)',
  hole_diameter: 'Hole diameter (mm)',
  inner_diameter: 'Inner diameter (mm)',
  outer_diameter: 'Outer diameter (mm)',
  inner_radius: 'Inner radius (mm)',
  channel_radius: 'Channel radius (mm)',
}

export function CadGenerator() {
  const [searchParams] = useSearchParams()
  const productSlug = searchParams.get('product')

  const [products, setProducts] = useState<ProductListItem[]>([])
  const [modelTypes, setModelTypes] = useState<string[]>([])
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null)
  const [modelType, setModelType] = useState('bracket')
  const [parameters, setParameters] = useState<Record<string, number | undefined>>({})
  const [cadModels, setCadModels] = useState<CadModelResponse[]>([])
  const [selectedCad, setSelectedCad] = useState<CadModelResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [exporting, setExporting] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [log, setLog] = useState<string[]>([])

  useEffect(() => {
    Promise.all([api.products.list({ limit: 200 }), api.cad.modelTypes()])
      .then(([list, types]) => {
        setProducts(list)
        setModelTypes(types)
        if (productSlug && list.length > 0) {
          const p = list.find((x) => x.slug === productSlug)
          if (p) setSelectedProductId(p.id)
        }
        if (!selectedProductId && list.length > 0 && !productSlug) {
          setSelectedProductId(list[0].id)
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [productSlug])

  useEffect(() => {
    if (selectedProductId == null) {
      setCadModels([])
      setSelectedCad(null)
      return
    }
    api.cad
      .list(selectedProductId)
      .then((list) => {
        setCadModels(list)
        setSelectedCad(list[0] ?? null)
      })
      .catch((e) => setError(e.message))
  }, [selectedProductId])

  const handleGenerate = async () => {
    if (selectedProductId == null) {
      setError('Select a product first.')
      return
    }
    setGenerating(true)
    setError(null)
    setLog((prev) => [...prev, `Generating ${modelType}...`])
    try {
      const body: CadCreate = {
        model_type: modelType,
        parameters: Object.fromEntries(
          Object.entries(parameters).filter(([, v]) => v != null)
        ) as Record<string, number>,
      }
      const created = await api.cad.create(selectedProductId, body)
      setCadModels((prev) => [created, ...prev])
      setSelectedCad(created)
      setLog((prev) => [...prev, `Created CAD model v${created.version} (${created.scad_file_path || 'saved'}).`])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generate failed')
      setLog((prev) => [...prev, `Error: ${e instanceof Error ? e.message : 'Unknown'}`])
    } finally {
      setGenerating(false)
    }
  }

  const handleExportStl = async (cadId: number) => {
    if (selectedProductId == null) return
    setExporting(cadId)
    setError(null)
    try {
      const result = await api.cad.exportStl(selectedProductId, cadId)
      if (result.success) {
        setLog((prev) => [...prev, `STL exported: ${result.stl_file_path}`])
        setCadModels((prev) =>
          prev.map((c) => (c.id === cadId ? { ...c, stl_file_path: result.stl_file_path ?? c.stl_file_path } : c))
        )
        if (selectedCad?.id === cadId) setSelectedCad({ ...selectedCad, stl_file_path: result.stl_file_path ?? selectedCad.stl_file_path })
      } else {
        setError(result.message)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Export failed')
    } finally {
      setExporting(null)
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <LoadingSpinner message="Loading products and CAD…" />
      </div>
    )
  }

  return (
    <div className="p-8">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold text-[var(--forge-text)]">CAD Generator</h1>
        <p className="text-[var(--forge-text-muted)] mt-1">
          Generate OpenSCAD models from templates and export STL
        </p>
      </header>

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onDismiss={() => setError(null)} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-[var(--forge-text-muted)] mb-1">Product</label>
            <select
              value={selectedProductId ?? ''}
              onChange={(e) => setSelectedProductId(e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
            >
              <option value="">Select product</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-[var(--forge-text-muted)] mb-1">Template type</label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value)}
              className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
            >
              {modelTypes.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, ' ')}
                </option>
              ))}
            </select>
          </div>

          <div>
            <span className="block text-sm text-[var(--forge-text-muted)] mb-2">Parameters (mm)</span>
            <div className="space-y-2">
              {Object.entries(PARAM_LABELS).map(([key, label]) => (
                <div key={key}>
                  <label className="block text-xs text-[var(--forge-text-muted)]">{label}</label>
                  <input
                    type="number"
                    step="0.1"
                    value={parameters[key] ?? ''}
                    onChange={(e) => {
                      const v = e.target.value ? parseFloat(e.target.value) : undefined
                      setParameters((prev) => {
                        const next = { ...prev }
                        if (v === undefined) delete next[key]
                        else next[key] = v
                        return next
                      })
                    }}
                    className="w-full px-2 py-1 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-[var(--forge-text)] text-sm"
                  />
                </div>
              ))}
            </div>
          </div>

          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating || selectedProductId == null}
            className="w-full px-4 py-2 rounded-md bg-[var(--forge-accent)] text-white font-medium disabled:opacity-50"
          >
            {generating ? 'Generating…' : 'Generate & save'}
          </button>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
            <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Generated code</h2>
            {selectedCad?.scad_code ? (
              <pre className="text-xs text-[var(--forge-text)] overflow-auto max-h-64 p-3 rounded bg-[var(--forge-bg)] whitespace-pre-wrap font-mono">
                {selectedCad.scad_code}
              </pre>
            ) : (
              <p className="text-sm text-[var(--forge-text-muted)]">Generate a model or select one below.</p>
            )}
            {selectedCad?.scad_file_path && (
              <p className="text-xs text-[var(--forge-text-muted)] mt-2">File: {selectedCad.scad_file_path}</p>
            )}
          </div>

          <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
            <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Saved models</h2>
            {cadModels.length === 0 ? (
              <p className="text-sm text-[var(--forge-text-muted)]">No CAD models yet for this product.</p>
            ) : (
              <ul className="space-y-2">
                {cadModels.map((c) => (
                  <li
                    key={c.id}
                    className={`flex flex-wrap items-center gap-2 p-2 rounded border ${selectedCad?.id === c.id ? 'border-[var(--forge-accent)]' : 'border-[var(--forge-border)]'}`}
                  >
                    <button
                      type="button"
                      onClick={() => setSelectedCad(c)}
                      className="text-sm font-medium text-[var(--forge-accent)] hover:underline"
                    >
                      v{c.version} – {c.model_type}
                    </button>
                    <span className="text-xs text-[var(--forge-text-muted)]">
                      {new Date(c.created_at).toLocaleString()}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleExportStl(c.id)}
                      disabled={exporting === c.id}
                      className="ml-auto px-2 py-1 rounded bg-[var(--forge-border)] text-xs disabled:opacity-50"
                    >
                      {exporting === c.id ? 'Exporting…' : 'Export STL'}
                    </button>
                    {c.stl_file_path && (
                      <span className="text-xs text-green-400">STL saved</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
            <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Log</h2>
            <div className="text-xs text-[var(--forge-text-muted)] max-h-24 overflow-auto font-mono">
              {log.length === 0 ? 'No activity yet.' : log.map((line, i) => <div key={i}>{line}</div>)}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
