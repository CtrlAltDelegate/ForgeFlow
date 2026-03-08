interface LoadingSpinnerProps {
  message?: string
  className?: string
}

export function LoadingSpinner({ message = 'Loading…', className = '' }: LoadingSpinnerProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 min-h-[40vh] text-[var(--forge-text-muted)] ${className}`}
      aria-live="polite"
      aria-busy="true"
    >
      <div
        className="w-8 h-8 rounded-full border-2 border-[var(--forge-border)] border-t-[var(--forge-accent)] animate-spin"
        aria-hidden
      />
      <p className="text-sm">{message}</p>
    </div>
  )
}
