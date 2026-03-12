import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { ErrorBanner } from '../components/ErrorBanner'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { EmptyState } from '../components/EmptyState'
import type { IntakeListItem, IntakeStatus, TriggerMode } from '../types'

const STATUS_LABELS: Record<IntakeStatus, string> = {
  raw_collected: 'Raw',
  enriching: 'Enriching…',
  brief_drafted: 'Brief Ready',
  brief_approved: 'Approved',
  rejected: 'Rejected',
  cad_queued: 'CAD Queued',
}

const STATUS_COLORS: Record<IntakeStatus, string> = {
  raw_collected: 'bg-gray-100 text-gray-600',
  enriching: 'bg-blue-100 text-blue-700 animate-pulse',
  brief_drafted: 'bg-amber-100 text-amber-700',
  brief_approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-600',
  cad_queued: 'bg-purple-100 text-purple-700',
}

const MODE_LABELS: Record<TriggerMode, string> = {
  etsy_url: 'Etsy',
  erank_paste: 'eRank',
  manual: 'Manual',
}

const ALL_STATUSES: IntakeStatus[] = [
  'raw_collected', 'enriching', 'brief_drafted', 'brief_approved', 'rejected', 'cad_queued',
]

function ConfidenceBadge({ score, level }: { score: number | null; level?: 'red' | 'yellow' | 'green' }) {
  if (score == null) return <span className="text-[var(--forge-text-muted)]">—</span>
  const pct = Math.round(score * 100)
  const color = level === 'green'
    ? 'text-green-600'
    : level === 'yellow'
    ? 'text-amber-600'
    : 'text-red-500'
  return <span className={`font-mono text-sm ${color}`}>{pct}%</span>
}

export function IntakeQueue() {
  const navigate = useNavigate()
  const [intakes, setIntakes] = useState<IntakeListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<IntakeStatus | ''>('')

  // New intake form
  const [showForm, setShowForm] = useState(false)
  const [mode, setMode] = useState<TriggerMode>('etsy_url')
  const [sourceUrl, setSourceUrl] = useState('')
  const [rawTitle, setRawTitle] = useState('')
  const [keyword, setKeyword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [lastSubmitted, setLastSubmitted] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    setError(null)
    api.intake.list({ limit: 100 })
      .then(setIntakes)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleSubmit = async () => {
    setSubmitError(null)
    setSubmitting(true)
    try {
      const body = {
        trigger_mode: mode,
        source_url: mode === 'etsy_url' ? sourceUrl.trim() || null : null,
        source_keyword: mode === 'erank_paste' ? keyword.trim() || null : null,
        raw_title: mode === 'manual' ? rawTitle.trim() || null : undefined,
      }
      const res = await api.intake.submit(body)
      setLastSubmitted(res.intake_id)
      setShowForm(false)
      setSourceUrl('')
      setRawTitle('')
      setKeyword('')
      load()
    } catch (e: unknown) {
      setSubmitError(e instanceof Error ? e.message : 'Submission failed')
    } finally {
      setSubmitting(false)
    }
  }

  const filtered = statusFilter
    ? intakes.filter((i) => i.status === statusFilter)
    : intakes

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-[var(--forge-text)]">Intake Queue</h1>
          <p className="text-sm text-[var(--forge-text-muted)] mt-0.5">
            Product discovery → AI enrichment → brief review
          </p>
        </div>
        <button
          onClick={() => { setShowForm((v) => !v); setSubmitError(null) }}
          className="px-4 py-2 rounded-md text-sm font-medium bg-[var(--forge-accent)] text-white hover:opacity-90 transition-opacity"
        >
          {showForm ? 'Cancel' : '+ New Intake'}
        </button>
      </div>

      {/* New intake form */}
      {showForm && (
        <div className="mb-6 p-5 rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)]">
          <h2 className="text-sm font-semibold text-[var(--forge-text)] mb-4">New Intake</h2>

          {/* Mode selector */}
          <div className="flex gap-4 mb-4">
            {(['etsy_url', 'manual', 'erank_paste'] as TriggerMode[]).map((m) => (
              <label key={m} className="flex items-center gap-2 cursor-pointer text-sm text-[var(--forge-text)]">
                <input
                  type="radio"
                  name="mode"
                  value={m}
                  checked={mode === m}
                  onChange={() => setMode(m)}
                  className="accent-[var(--forge-accent)]"
                />
                {MODE_LABELS[m]}
              </label>
            ))}
          </div>

          {/* Mode-specific input */}
          {mode === 'etsy_url' && (
            <input
              type="url"
              placeholder="https://www.etsy.com/listing/..."
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm text-[var(--forge-text)] placeholder-[var(--forge-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--forge-accent)]"
            />
          )}
          {mode === 'manual' && (
            <input
              type="text"
              placeholder="Product title (e.g. USB Cable Desk Organizer)"
              value={rawTitle}
              onChange={(e) => setRawTitle(e.target.value)}
              className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm text-[var(--forge-text)] placeholder-[var(--forge-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--forge-accent)]"
            />
          )}
          {mode === 'erank_paste' && (
            <input
              type="text"
              placeholder="eRank keyword (e.g. desk cable organizer)"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm text-[var(--forge-text)] placeholder-[var(--forge-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--forge-accent)]"
            />
          )}

          {submitError && (
            <p className="mt-3 text-sm text-red-500">{submitError}</p>
          )}

          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-4 py-2 rounded-md text-sm font-medium bg-[var(--forge-accent)] text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {submitting ? 'Submitting…' : 'Submit'}
            </button>
            {submitting && mode === 'etsy_url' && (
              <span className="text-xs text-[var(--forge-text-muted)]">
                Scraping listing — this can take up to 10s…
              </span>
            )}
          </div>
        </div>
      )}

      {lastSubmitted && (
        <div className="mb-4 p-3 rounded bg-green-50 border border-green-200 text-sm text-green-700 flex items-center justify-between">
          <span>Intake created — enrichment running in background</span>
          <button
            onClick={() => navigate(`/intake/${lastSubmitted}`)}
            className="underline font-medium"
          >
            View
          </button>
        </div>
      )}

      {/* Status filter tabs */}
      <div className="flex gap-1 mb-4 flex-wrap">
        <button
          onClick={() => setStatusFilter('')}
          className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
            statusFilter === ''
              ? 'bg-[var(--forge-accent)]/20 text-[var(--forge-accent)]'
              : 'text-[var(--forge-text-muted)] hover:bg-[var(--forge-border)]'
          }`}
        >
          All ({intakes.length})
        </button>
        {ALL_STATUSES.map((s) => {
          const count = intakes.filter((i) => i.status === s).length
          if (count === 0) return null
          return (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                statusFilter === s
                  ? 'bg-[var(--forge-accent)]/20 text-[var(--forge-accent)]'
                  : 'text-[var(--forge-text-muted)] hover:bg-[var(--forge-border)]'
              }`}
            >
              {STATUS_LABELS[s]} ({count})
            </button>
          )
        })}
      </div>

      {/* Content */}
      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorBanner message={error} onRetry={load} />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No intakes yet"
          description="Submit an Etsy URL, eRank keyword, or manual title to start."
          actionLabel="+ New Intake"
          onAction={() => setShowForm(true)}
        />
      ) : (
        <div className="rounded-lg border border-[var(--forge-border)] overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--forge-surface)] border-b border-[var(--forge-border)]">
                <th className="text-left px-4 py-3 font-medium text-[var(--forge-text-muted)]">Title</th>
                <th className="text-left px-4 py-3 font-medium text-[var(--forge-text-muted)]">Mode</th>
                <th className="text-left px-4 py-3 font-medium text-[var(--forge-text-muted)]">Status</th>
                <th className="text-left px-4 py-3 font-medium text-[var(--forge-text-muted)]">Confidence</th>
                <th className="text-left px-4 py-3 font-medium text-[var(--forge-text-muted)]">Images</th>
                <th className="text-left px-4 py-3 font-medium text-[var(--forge-text-muted)]">Created</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--forge-border)]">
              {filtered.map((intake) => (
                <tr
                  key={intake.id}
                  onClick={() => navigate(`/intake/${intake.id}`)}
                  className="hover:bg-[var(--forge-surface)] cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 text-[var(--forge-text)] font-medium max-w-xs">
                    <span className="truncate block">
                      {intake.raw_title || intake.source_keyword || intake.source_url || '(untitled)'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-[var(--forge-text-muted)]">
                    {MODE_LABELS[intake.trigger_mode]}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[intake.status]}`}>
                      {STATUS_LABELS[intake.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <ConfidenceBadge score={intake.confidence_score} />
                  </td>
                  <td className="px-4 py-3 text-[var(--forge-text-muted)]">
                    {intake.image_count}
                  </td>
                  <td className="px-4 py-3 text-[var(--forge-text-muted)]">
                    {new Date(intake.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right text-[var(--forge-accent)] font-medium">
                    Review →
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
