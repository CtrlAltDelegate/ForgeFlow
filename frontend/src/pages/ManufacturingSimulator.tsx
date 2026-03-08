import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../services/api'
import { ErrorBanner } from '../components/ErrorBanner'
import { LoadingSpinner } from '../components/LoadingSpinner'
import type { ProductListItem, CadModelResponse, SimulationResponse, SimulationResultWithWarnings } from '../types'

export function ManufacturingSimulator() {
  const [searchParams] = useSearchParams()
  const productSlug = searchParams.get('product')

  const [products, setProducts] = useState<ProductListItem[]>([])
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null)
  const [cadModels, setCadModels] = useState<CadModelResponse[]>([])
  const [simulations, setSimulations] = useState<SimulationResponse[]>([])
  const [selectedSim, setSelectedSim] = useState<SimulationResponse | null>(null)

  const [materialType, setMaterialType] = useState('PLA')
  const [layerHeight, setLayerHeight] = useState(0.2)
  const [infill, setInfill] = useState(20)
  const [nozzleSize, setNozzleSize] = useState(0.4)
  const [cadModelId, setCadModelId] = useState<number | null>(null)

  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])

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
      setCadModels([])
      setSimulations([])
      setSelectedSim(null)
      return
    }
    Promise.all([
      api.cad.list(selectedProductId),
      api.simulation.list(selectedProductId),
    ]).then(([cadList, simList]) => {
      setCadModels(cadList)
      setSimulations(simList)
      setSelectedSim(simList[0] ?? null)
      setCadModelId(cadList.length > 0 ? cadList[0].id : null)
    }).catch((e) => setError(e.message))
  }, [selectedProductId])

  const handleRun = async () => {
    if (selectedProductId == null) return
    setRunning(true)
    setError(null)
    setWarnings([])
    try {
      const result: SimulationResultWithWarnings = await api.simulation.create(selectedProductId, {
        cad_model_id: cadModelId ?? undefined,
        material_type: materialType,
        layer_height: layerHeight,
        infill,
        nozzle_size: nozzleSize,
      })
      setSimulations((prev) => [result.simulation, ...prev])
      setSelectedSim(result.simulation)
      setWarnings(result.warnings ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Simulation failed')
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <LoadingSpinner message="Loading products…" />
      </div>
    )
  }

  return (
    <div className="p-8">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold text-[var(--forge-text)]">Manufacturing Simulator</h1>
        <p className="text-[var(--forge-text-muted)] mt-1">
          Estimate print time, material use, and difficulty (heuristic)
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
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-[var(--forge-text-muted)] mb-1">CAD model (optional)</label>
            <select
              value={cadModelId ?? ''}
              onChange={(e) => setCadModelId(e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
            >
              <option value="">Use default volume</option>
              {cadModels.map((c) => (
                <option key={c.id} value={c.id}>v{c.version} – {c.model_type}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-[var(--forge-text-muted)] mb-1">Material</label>
            <select
              value={materialType}
              onChange={(e) => setMaterialType(e.target.value)}
              className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-surface)] text-[var(--forge-text)]"
            >
              <option value="PLA">PLA</option>
              <option value="PETG">PETG</option>
              <option value="ABS">ABS</option>
              <option value="TPU">TPU</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs text-[var(--forge-text-muted)]">Layer height (mm)</label>
              <input
                type="number"
                step="0.05"
                value={layerHeight}
                onChange={(e) => setLayerHeight(parseFloat(e.target.value) || 0.2)}
                className="w-full px-2 py-1 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--forge-text-muted)]">Infill %</label>
              <input
                type="number"
                min="0"
                max="100"
                value={infill}
                onChange={(e) => setInfill(parseInt(e.target.value, 10) || 20)}
                className="w-full px-2 py-1 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-[var(--forge-text-muted)]">Nozzle (mm)</label>
              <input
                type="number"
                step="0.1"
                value={nozzleSize}
                onChange={(e) => setNozzleSize(parseFloat(e.target.value) || 0.4)}
                className="w-full px-2 py-1 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm"
              />
            </div>
          </div>

          <button
            type="button"
            onClick={handleRun}
            disabled={running || selectedProductId == null}
            className="w-full px-4 py-2 rounded-md bg-[var(--forge-accent)] text-white font-medium disabled:opacity-50"
          >
            {running ? 'Running…' : 'Run simulation'}
          </button>
        </div>

        <div className="lg:col-span-2 space-y-4">
          {warnings.length > 0 && (
            <div className="rounded-lg border border-amber-500/50 bg-amber-500/10 p-4">
              <h2 className="text-sm font-medium text-amber-400 mb-2">Warnings</h2>
              <ul className="text-sm text-amber-200 list-disc list-inside">
                {warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
            <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">Latest result</h2>
            {selectedSim ? (
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-[var(--forge-text-muted)]">Print time</span>
                  <p className="font-medium">{selectedSim.estimated_print_time_minutes?.toFixed(0) ?? '—'} min</p>
                </div>
                <div>
                  <span className="text-[var(--forge-text-muted)]">Material</span>
                  <p className="font-medium">{selectedSim.estimated_material_grams?.toFixed(0) ?? '—'} g</p>
                </div>
                <div>
                  <span className="text-[var(--forge-text-muted)]">Filament cost</span>
                  <p className="font-medium">
                    {selectedSim.estimated_filament_cost != null ? `$${selectedSim.estimated_filament_cost.toFixed(2)}` : '—'}
                  </p>
                </div>
                <div>
                  <span className="text-[var(--forge-text-muted)]">Difficulty</span>
                  <p className="font-medium">{selectedSim.difficulty_score?.toFixed(1) ?? '—'}/100</p>
                </div>
                <div className="col-span-2">
                  <span className="text-[var(--forge-text-muted)]">Supports</span>
                  <p className="font-medium">{selectedSim.supports_required ? 'Yes' : 'No'}</p>
                </div>
                <div className="col-span-2">
                  <span className="text-[var(--forge-text-muted)]">Orientation</span>
                  <p className="font-medium">{selectedSim.recommended_orientation ?? '—'}</p>
                </div>
                {selectedSim.notes && (
                  <p className="col-span-2 text-xs text-[var(--forge-text-muted)] mt-2">{selectedSim.notes}</p>
                )}
              </div>
            ) : (
              <p className="text-sm text-[var(--forge-text-muted)]">Run a simulation to see estimates.</p>
            )}
          </div>

          {simulations.length > 1 && (
            <div className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] p-4">
              <h2 className="text-sm font-medium text-[var(--forge-text-muted)] mb-2">History</h2>
              <ul className="space-y-1">
                {simulations.slice(0, 5).map((s) => (
                  <li key={s.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedSim(s)}
                      className={`text-sm ${selectedSim?.id === s.id ? 'text-[var(--forge-accent)]' : 'text-[var(--forge-text-muted)] hover:text-[var(--forge-text)]'}`}
                    >
                      {new Date(s.simulated_at).toLocaleString()} – {s.estimated_print_time_minutes?.toFixed(0)} min
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
