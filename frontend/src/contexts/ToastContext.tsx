import { createContext, useCallback, useContext, useState } from 'react'

type ToastType = 'success' | 'error' | 'info'

interface ToastState {
  message: string
  type: ToastType
}

interface ToastContextValue {
  toast: ToastState | null
  showToast: (message: string, type?: ToastType) => void
  clearToast: () => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toast, setToast] = useState<ToastState | null>(null)

  const showToast = useCallback((message: string, type: ToastType = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }, [])

  const clearToast = useCallback(() => setToast(null), [])

  return (
    <ToastContext.Provider value={{ toast, showToast, clearToast }}>
      {children}
      {toast && (
        <div
          className="fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg border text-sm font-medium max-w-sm"
          style={{
            backgroundColor: toast.type === 'success' ? 'var(--forge-success)' : toast.type === 'error' ? 'rgb(239 68 68)' : 'var(--forge-surface)',
            color: toast.type === 'success' || toast.type === 'error' ? '#fff' : 'var(--forge-text)',
            borderColor: toast.type === 'success' ? 'var(--forge-success)' : toast.type === 'error' ? 'rgb(239 68 68)' : 'var(--forge-border)',
          }}
          role="status"
        >
          {toast.message}
        </div>
      )}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) return { showToast: () => {}, clearToast: () => {} }
  return ctx
}
