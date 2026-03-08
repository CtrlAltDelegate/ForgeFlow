interface EmptyStateProps {
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
  className?: string
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  className = '',
}: EmptyStateProps) {
  return (
    <div
      className={`rounded-lg border border-[var(--forge-border)] bg-[var(--forge-surface)]/50 p-8 text-center ${className}`}
    >
      <p className="font-medium text-[var(--forge-text)]">{title}</p>
      {description && (
        <p className="mt-1 text-sm text-[var(--forge-text-muted)] max-w-md mx-auto">{description}</p>
      )}
      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          className="mt-4 px-4 py-2 rounded-md bg-[var(--forge-accent)] text-white text-sm font-medium hover:opacity-90"
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}
