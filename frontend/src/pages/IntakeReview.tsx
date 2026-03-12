import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { ErrorBanner } from '../components/ErrorBanner'
import { LoadingSpinner } from '../components/LoadingSpinner'
import type { IntakeResponse, IntakeStatus, IntakeApproveResponse } from '../types'

const STATUS_LABELS: Record<IntakeStatus, string> = {
  raw_collected: 'Raw Collected',
  enriching: 'Enriching…',
  brief_drafted: 'Brief Ready',
  brief_approved: 'Approved',
  rejected: 'Rejected',
  cad_queued: 'CAD Queued',
}

const STATUS_COLORS: Record<IntakeStatus, string> = {
  raw_collected: 'bg-gray-100 text-gray-600',
  enriching: 'bg-blue-100 text-blue-700',
  brief_drafted: 'bg-amber-100 text-amber-700',
  brief_approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-600',
  cad_queued: 'bg-purple-100 text-purple-700',
}

const LEVEL_COLORS = {
  green: 'text-green-600',
  yellow: 'text-amber-600',
  red: 'text-red-500',
}

const MATERIALS = ['PLA', 'PETG', 'TPU', 'ABS'] as const

// ---------------------------------------------------------------------------
// Brief editor helpers
// ---------------------------------------------------------------------------

function asStringArray(val: unknown): string[] {
  if (Array.isArray(val)) return val.filter((v) => typeof v === 'string')
  return []
}

function asDims(val: unknown): { length: number; width: number; height: number } {
  const d = (val ?? {}) as Record<string, unknown>
  return {
    length: Number(d.length) || 0,
    width: Number(d.width) || 0,
    height: Number(d.height) || 0,
  }
}

// ---------------------------------------------------------------------------
// BriefEditor component
// ---------------------------------------------------------------------------

interface BriefEditorProps {
  intakeId: string
  brief: Record<string, unknown>
  onSaved: (updated: IntakeResponse) => void
}

function BriefEditor({ intakeId, brief, onSaved }: BriefEditorProps) {
  const [local, setLocal] = useState<Record<string, unknown>>({ ...brief })
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [regenerating, setRegenerating] = useState(false)

  // Reset when brief prop changes (after re-enrich)
  useEffect(() => { setLocal({ ...brief }) }, [brief])

  const set = (key: string, val: unknown) => setLocal((prev) => ({ ...prev, [key]: val }))

  const dims = asDims(local.approximate_dimensions_mm)
  const features = asStringArray(local.dominant_features)
  const avoid = asStringArray(local.avoid)

  const hasChanges = JSON.stringify(local) !== JSON.stringify(brief)

  const saveChanges = async () => {
    setSaving(true)
    setSaveError(null)
    try {
      // Find changed fields and PATCH each one
      let last: IntakeResponse | null = null
      for (const [key, val] of Object.entries(local)) {
        if (JSON.stringify(val) !== JSON.stringify(brief[key])) {
          last = await api.intake.patchBriefField(intakeId, key, val)
        }
      }
      if (last) onSaved(last)
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  const regenPrompt = async () => {
    setRegenerating(true)
    setSaveError(null)
    try {
      const updated = await api.intake.regeneratePrompt(intakeId)
      onSaved(updated)
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : 'Regeneration failed')
    } finally {
      setRegenerating(false)
    }
  }

  const inputClass =
    'w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm text-[var(--forge-text)] placeholder-[var(--forge-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--forge-accent)]'
  const labelClass = 'block text-xs font-medium text-[var(--forge-text-muted)] mb-1'

  return (
    <div className="space-y-4">

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelClass}>Product Type</label>
          <input
            className={inputClass}
            value={String(local.product_type ?? '')}
            onChange={(e) => set('product_type', e.target.value)}
          />
        </div>
        <div>
          <label className={labelClass}>Material *</label>
          <select
            className={inputClass}
            value={String(local.material ?? '')}
            onChange={(e) => set('material', e.target.value)}
          >
            <option value="">— select —</option>
            {MATERIALS.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
      </div>

      <div>
        <label className={labelClass}>Primary Geometry *</label>
        <input
          className={inputClass}
          value={String(local.primary_geometry ?? '')}
          onChange={(e) => set('primary_geometry', e.target.value)}
          placeholder="e.g. low-profile rectangular bar with top-entry cable slots"
        />
      </div>

      <div>
        <label className={labelClass}>Primary Use Case</label>
        <input
          className={inputClass}
          value={String(local.primary_use_case ?? '')}
          onChange={(e) => set('primary_use_case', e.target.value)}
        />
      </div>

      <div>
        <label className={labelClass}>
          Dominant Features * <span className="font-normal">(one per line, min 3)</span>
        </label>
        <textarea
          className={`${inputClass} h-28 resize-y`}
          value={features.join('\n')}
          onChange={(e) =>
            set('dominant_features', e.target.value.split('\n').map((s) => s.trim()).filter(Boolean))
          }
          placeholder="evenly spaced top-entry cable slots&#10;flat base suitable for adhesive pad&#10;smooth uninterrupted sides"
        />
        <p className={`text-xs mt-1 ${features.length >= 3 ? 'text-green-600' : 'text-red-500'}`}>
          {features.length} / 3 minimum
        </p>
      </div>

      <div>
        <label className={labelClass}>Approximate Dimensions (mm) *</label>
        <div className="grid grid-cols-3 gap-3">
          {(['length', 'width', 'height'] as const).map((axis) => (
            <div key={axis}>
              <label className="block text-xs text-[var(--forge-text-muted)] mb-1 capitalize">{axis}</label>
              <input
                type="number"
                className={inputClass}
                value={dims[axis] || ''}
                onChange={(e) =>
                  set('approximate_dimensions_mm', { ...dims, [axis]: parseFloat(e.target.value) || 0 })
                }
                placeholder="0"
              />
            </div>
          ))}
        </div>
      </div>

      <div>
        <label className={labelClass}>Aesthetic</label>
        <input
          className={inputClass}
          value={String(local.aesthetic ?? '')}
          onChange={(e) => set('aesthetic', e.target.value)}
          placeholder="e.g. minimalist, smooth, consumer-product appearance"
        />
      </div>

      <div>
        <label className={labelClass}>
          Avoid * <span className="font-normal">(one per line, min 3)</span>
        </label>
        <textarea
          className={`${inputClass} h-24 resize-y`}
          value={avoid.join('\n')}
          onChange={(e) =>
            set('avoid', e.target.value.split('\n').map((s) => s.trim()).filter(Boolean))
          }
          placeholder="visible layer lines&#10;sharp corners&#10;overly tall aspect ratio"
        />
        <p className={`text-xs mt-1 ${avoid.length >= 3 ? 'text-green-600' : 'text-red-500'}`}>
          {avoid.length} / 3 minimum
        </p>
      </div>

      <div>
        <label className={labelClass}>Resemblance Goal</label>
        <input
          className={inputClass}
          value={String(local.resemblance_goal ?? '')}
          onChange={(e) => set('resemblance_goal', e.target.value)}
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <label className={`${labelClass} mb-0`}>
            OpenSCAD Prompt * <span className="font-normal">(min 150 chars)</span>
          </label>
          <button
            onClick={regenPrompt}
            disabled={regenerating}
            className="text-xs text-[var(--forge-accent)] hover:underline disabled:opacity-50"
          >
            {regenerating ? 'Regenerating…' : '↻ Regenerate'}
          </button>
        </div>
        <textarea
          className={`${inputClass} h-48 resize-y font-mono text-xs`}
          value={String(local.openscad_prompt ?? '')}
          onChange={(e) => set('openscad_prompt', e.target.value)}
          placeholder="Create a 3D-printable [product_type] in OpenSCAD…"
        />
        <p className={`text-xs mt-1 ${String(local.openscad_prompt ?? '').length >= 150 ? 'text-green-600' : 'text-red-500'}`}>
          {String(local.openscad_prompt ?? '').length} chars (min 150)
        </p>
      </div>

      {/* Parametric variables — read-only display */}
      {Array.isArray(local.parametric_variables) && local.parametric_variables.length > 0 && (
        <div>
          <label className={labelClass}>Parametric Variables</label>
          <div className="rounded border border-[var(--forge-border)] divide-y divide-[var(--forge-border)] text-xs">
            {(local.parametric_variables as Record<string, unknown>[]).map((v, i) => (
              <div key={i} className="px-3 py-2 flex gap-4 text-[var(--forge-text)]">
                <span className="font-mono font-semibold">{String(v.name)}</span>
                <span className="text-[var(--forge-text-muted)]">{String(v.controls)}</span>
                <span className="ml-auto text-[var(--forge-text-muted)]">
                  {String(v.min)}–{String(v.max)} (default: {String(v.default)})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {saveError && <p className="text-sm text-red-500">{saveError}</p>}

      {hasChanges && (
        <button
          onClick={saveChanges}
          disabled={saving}
          className="w-full px-4 py-2 rounded-md text-sm font-medium bg-[var(--forge-accent)] text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          {saving ? 'Saving…' : 'Save Changes'}
        </button>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// IntakeReview page
// ---------------------------------------------------------------------------

export function IntakeReview() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [intake, setIntake] = useState<IntakeResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Action states
  const [approving, setApproving] = useState(false)
  const [approveResult, setApproveResult] = useState<IntakeApproveResponse | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [showRejectForm, setShowRejectForm] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [rejecting, setRejecting] = useState(false)
  const [enriching, setEnriching] = useState(false)
  const [reviewerNotes, setReviewerNotes] = useState('')

  const load = () => {
    if (!id) return
    setLoading(true)
    setError(null)
    api.intake.get(id)
      .then((data) => {
        setIntake(data)
        setReviewerNotes(data.reviewer_notes ?? '')
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [id])

  const handleApprove = async () => {
    if (!intake?.draft_brief_json || !id) return
    setActionError(null)
    setApproving(true)
    try {
      const result = await api.intake.approve(
        id,
        intake.draft_brief_json,
        reviewerNotes || undefined,
      )
      setApproveResult(result)
      load()
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : 'Approval failed')
    } finally {
      setApproving(false)
    }
  }

  const handleReject = async () => {
    if (!id || !rejectReason.trim()) return
    setActionError(null)
    setRejecting(true)
    try {
      await api.intake.reject(id, rejectReason.trim())
      setShowRejectForm(false)
      load()
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : 'Rejection failed')
    } finally {
      setRejecting(false)
    }
  }

  const handleReEnrich = async () => {
    if (!id) return
    setActionError(null)
    setEnriching(true)
    try {
      await api.intake.reEnrich(id, reviewerNotes || undefined)
      load()
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : 'Re-enrichment failed')
    } finally {
      setEnriching(false)
    }
  }

  if (loading) return <div className="p-8"><LoadingSpinner /></div>
  if (error) return <div className="p-8"><ErrorBanner message={error} onRetry={load} /></div>
  if (!intake) return null

  const conf = intake.confidence_detail_json
  const hasBrief = !!intake.draft_brief_json
  const canApprove = hasBrief && intake.status !== 'brief_approved' && intake.status !== 'rejected'
  const canReject = intake.status !== 'brief_approved' && intake.status !== 'rejected'
  const canReEnrich = intake.status !== 'enriching'

  return (
    <div className="p-8 max-w-6xl mx-auto">

      {/* Header */}
      <div className="flex items-start gap-4 mb-6">
        <button
          onClick={() => navigate('/intake')}
          className="mt-0.5 text-sm text-[var(--forge-text-muted)] hover:text-[var(--forge-text)] shrink-0"
        >
          ← Queue
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-semibold text-[var(--forge-text)] truncate">
            {intake.raw_title || intake.source_keyword || '(untitled)'}
          </h1>
          <div className="flex items-center gap-3 mt-1 flex-wrap">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[intake.status]}`}>
              {STATUS_LABELS[intake.status]}
            </span>
            {conf && (
              <span className={`text-sm font-medium ${LEVEL_COLORS[conf.warning_level]}`}>
                Confidence: {Math.round((intake.confidence_score ?? 0) * 100)}%
                {' '}({conf.warning_level})
              </span>
            )}
            <span className="text-xs text-[var(--forge-text-muted)]">
              {intake.enrichment_attempt_count} enrichment{intake.enrichment_attempt_count !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 shrink-0 flex-wrap justify-end">
          {canReEnrich && (
            <button
              onClick={handleReEnrich}
              disabled={enriching}
              className="px-3 py-1.5 rounded text-sm border border-[var(--forge-border)] text-[var(--forge-text-muted)] hover:text-[var(--forge-text)] hover:bg-[var(--forge-surface)] disabled:opacity-50 transition-colors"
            >
              {enriching ? 'Queuing…' : 'Re-enrich'}
            </button>
          )}
          {canReject && (
            <button
              onClick={() => setShowRejectForm((v) => !v)}
              className="px-3 py-1.5 rounded text-sm border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
            >
              Reject
            </button>
          )}
          {canApprove && (
            <button
              onClick={handleApprove}
              disabled={approving || !hasBrief}
              className="px-4 py-1.5 rounded text-sm font-medium bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {approving ? 'Approving…' : 'Approve Brief'}
            </button>
          )}
        </div>
      </div>

      {/* Action feedback */}
      {actionError && (
        <div className="mb-4 p-3 rounded bg-red-50 border border-red-200 text-sm text-red-600">
          {actionError}
        </div>
      )}
      {approveResult && (
        <div className="mb-4 p-3 rounded bg-green-50 border border-green-200 text-sm text-green-700 flex gap-4">
          <span>Approved — Product #{approveResult.product_id} created</span>
          <button
            onClick={() => navigate(`/product/${approveResult.product_id}`)}
            className="underline font-medium"
          >
            View product →
          </button>
        </div>
      )}

      {/* Reject form */}
      {showRejectForm && (
        <div className="mb-4 p-4 rounded border border-red-200 bg-red-50 space-y-3">
          <label className="block text-sm font-medium text-red-700">Rejection reason</label>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            className="w-full px-3 py-2 rounded border border-red-300 bg-white text-sm text-[var(--forge-text)] focus:outline-none focus:ring-1 focus:ring-red-400 h-20 resize-none"
            placeholder="Explain why this intake is being rejected…"
          />
          <div className="flex gap-2">
            <button
              onClick={handleReject}
              disabled={rejecting || !rejectReason.trim()}
              className="px-3 py-1.5 rounded text-sm font-medium bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
            >
              {rejecting ? 'Rejecting…' : 'Confirm Reject'}
            </button>
            <button
              onClick={() => setShowRejectForm(false)}
              className="px-3 py-1.5 rounded text-sm text-[var(--forge-text-muted)] hover:text-[var(--forge-text)]"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Low confidence field warnings */}
      {conf && conf.low_confidence_fields.length > 0 && (
        <div className="mb-4 p-3 rounded bg-amber-50 border border-amber-200 text-sm text-amber-700">
          Low confidence: {conf.low_confidence_fields.join(', ')}
        </div>
      )}

      {/* Main content: two-column */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Left: Raw data */}
        <div className="space-y-4">

          {/* Raw listing */}
          <section className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] overflow-hidden">
            <div className="px-4 py-3 border-b border-[var(--forge-border)]">
              <h2 className="text-sm font-semibold text-[var(--forge-text)]">Raw Listing Data</h2>
            </div>
            <dl className="divide-y divide-[var(--forge-border)]">
              {[
                ['Source', intake.source_url
                  ? <a href={intake.source_url} target="_blank" rel="noreferrer" className="text-[var(--forge-accent)] hover:underline truncate block max-w-xs">{intake.source_url}</a>
                  : intake.source_keyword ?? '—'],
                ['Price', intake.raw_price_usd != null ? `$${intake.raw_price_usd.toFixed(2)}` : '—'],
                ['Rating', intake.raw_rating != null ? `${intake.raw_rating} ★` : '—'],
                ['Reviews', intake.raw_review_count?.toLocaleString() ?? '—'],
                ['Images', intake.image_count],
              ].map(([k, v]) => (
                <div key={String(k)} className="flex px-4 py-2.5 text-sm">
                  <dt className="w-24 shrink-0 text-[var(--forge-text-muted)]">{k}</dt>
                  <dd className="text-[var(--forge-text)]">{v}</dd>
                </div>
              ))}
            </dl>
          </section>

          {/* Description */}
          {intake.raw_description && (
            <section className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] overflow-hidden">
              <div className="px-4 py-3 border-b border-[var(--forge-border)]">
                <h2 className="text-sm font-semibold text-[var(--forge-text)]">Description</h2>
              </div>
              <p className="px-4 py-3 text-sm text-[var(--forge-text)] whitespace-pre-wrap line-clamp-10">
                {intake.raw_description}
              </p>
            </section>
          )}

          {/* Tags */}
          {Array.isArray(intake.raw_tags) && intake.raw_tags.length > 0 && (
            <section className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] overflow-hidden">
              <div className="px-4 py-3 border-b border-[var(--forge-border)]">
                <h2 className="text-sm font-semibold text-[var(--forge-text)]">Tags</h2>
              </div>
              <div className="px-4 py-3 flex flex-wrap gap-2">
                {intake.raw_tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 rounded bg-[var(--forge-bg)] border border-[var(--forge-border)] text-xs text-[var(--forge-text)]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </section>
          )}

          {/* Reviewer notes */}
          <section className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] overflow-hidden">
            <div className="px-4 py-3 border-b border-[var(--forge-border)]">
              <h2 className="text-sm font-semibold text-[var(--forge-text)]">Reviewer Notes</h2>
            </div>
            <div className="px-4 py-3">
              <textarea
                value={reviewerNotes}
                onChange={(e) => setReviewerNotes(e.target.value)}
                placeholder="Add context for the enricher or approver…"
                className="w-full px-3 py-2 rounded border border-[var(--forge-border)] bg-[var(--forge-bg)] text-sm text-[var(--forge-text)] placeholder-[var(--forge-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--forge-accent)] h-20 resize-none"
              />
              <p className="text-xs text-[var(--forge-text-muted)] mt-1">
                Passed to enricher on re-enrich; included with approval.
              </p>
            </div>
          </section>

          {/* Rejection reason (if rejected) */}
          {intake.rejection_reason && (
            <div className="p-3 rounded bg-red-50 border border-red-200 text-sm text-red-700">
              <span className="font-medium">Rejected: </span>{intake.rejection_reason}
            </div>
          )}
        </div>

        {/* Right: Brief editor */}
        <div>
          <section className="rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)] overflow-hidden">
            <div className="px-4 py-3 border-b border-[var(--forge-border)] flex items-center justify-between">
              <h2 className="text-sm font-semibold text-[var(--forge-text)]">Draft Brief</h2>
              {conf && (
                <div className="flex gap-2 text-xs">
                  {Object.entries(conf.per_field).map(([field, score]) => (
                    <span
                      key={field}
                      title={field}
                      className={`w-2 h-2 rounded-full ${score >= 0.8 ? 'bg-green-400' : score >= 0.5 ? 'bg-amber-400' : 'bg-red-400'}`}
                    />
                  ))}
                </div>
              )}
            </div>
            <div className="p-4">
              {hasBrief ? (
                <BriefEditor
                  intakeId={intake.id}
                  brief={intake.draft_brief_json!}
                  onSaved={(updated) => setIntake(updated)}
                />
              ) : intake.status === 'enriching' ? (
                <div className="py-8 text-center">
                  <LoadingSpinner message="AI enrichment in progress…" />
                </div>
              ) : (
                <div className="py-8 text-center text-sm text-[var(--forge-text-muted)]">
                  No draft brief yet.{' '}
                  {canReEnrich && (
                    <button onClick={handleReEnrich} className="text-[var(--forge-accent)] hover:underline">
                      Run enrichment
                    </button>
                  )}
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
