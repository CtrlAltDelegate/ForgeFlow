interface ErrorBannerProps {
  message: string
  onDismiss?: () => void
  onRetry?: () => void
}

export function ErrorBanner({ message, onDismiss, onRetry }: ErrorBannerProps) {
  return (
    <div
      className="rounded-lg border border-red-500/50 bg-red-500/10 p-4 text-red-400 text-sm flex items-start justify-between gap-3"
      role="alert"
    >
      <span className="flex-1">{message}</span>
      <div className="flex gap-2 shrink-0">
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="px-2 py-1 rounded border border-red-400/50 hover:bg-red-500/20 text-red-300 text-xs font-medium"
          >
            Retry
          </button>
        )}
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="px-2 py-1 rounded border border-red-400/50 hover:bg-red-500/20 text-red-300 text-xs"
            aria-label="Dismiss"
          >
            ×
          </button>
        )}
      </div>
    </div>
  )
}
