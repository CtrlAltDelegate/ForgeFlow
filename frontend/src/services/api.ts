const API_BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  dashboard: {
    summary: () => request<import('../types').DashboardSummary>('/dashboard/summary'),
  },
  products: {
    list: (params?: {
      skip?: number
      limit?: number
      search?: string
      category?: string
      status?: string
      sort?: string
      order?: string
    }) => {
      const sp = new URLSearchParams()
      if (params?.skip != null) sp.set('skip', String(params.skip))
      if (params?.limit != null) sp.set('limit', String(params.limit))
      if (params?.search) sp.set('search', params.search)
      if (params?.category) sp.set('category', params.category)
      if (params?.status) sp.set('status', params.status)
      if (params?.sort) sp.set('sort', params.sort)
      if (params?.order) sp.set('order', params.order)
      const q = sp.toString()
      return request<import('../types').ProductListItem[]>(`/products${q ? `?${q}` : ''}`)
    },
    categories: () => request<string[]>('/products/categories'),
    get: (idOrSlug: string) =>
      request<import('../types').Product>(`/products/${encodeURIComponent(idOrSlug)}`),
  },
}
