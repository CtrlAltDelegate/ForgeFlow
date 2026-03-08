const API_BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: HeadersInit = { ...options?.headers }
  if (!(options?.body instanceof FormData)) {
    (headers as Record<string, string>)['Content-Type'] = 'application/json'
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const msg = typeof err.detail === 'string' ? err.detail : err.detail?.message || JSON.stringify(err.detail)
    throw new Error(msg)
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
    create: (body: import('../types').ProductCreate) =>
      request<import('../types').Product>('/products', { method: 'POST', body: JSON.stringify(body) }),
    update: (id: number, body: import('../types').ProductUpdate) =>
      request<import('../types').Product>(`/products/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: (id: number) =>
      request<void>(`/products/${id}`, { method: 'DELETE' }),
    score: (id: number) =>
      request<import('../types').OpportunityScoreSummary>(`/products/${id}/score`, { method: 'POST' }),
    addResearch: (productId: number, body: import('../types').ResearchDataCreate) =>
      request<import('../types').ResearchDataResponse>(`/products/${productId}/research`, { method: 'POST', body: JSON.stringify(body) }),
  },
  cad: {
    modelTypes: () => request<string[]>('/products/model-types'),
    list: (productId: number) =>
      request<import('../types').CadModelResponse[]>(`/products/${productId}/cad`),
    create: (productId: number, body: import('../types').CadCreate) =>
      request<import('../types').CadModelResponse>(`/products/${productId}/cad`, { method: 'POST', body: JSON.stringify(body) }),
    get: (productId: number, cadId: number) =>
      request<import('../types').CadModelResponse>(`/products/${productId}/cad/${cadId}`),
    exportStl: (productId: number, cadId: number) =>
      request<import('../types').CadExportResult>(`/products/${productId}/cad/${cadId}/export-stl`, { method: 'POST' }),
  },
  simulation: {
    list: (productId: number) =>
      request<import('../types').SimulationResponse[]>(`/products/${productId}/simulations`),
    create: (productId: number, body: import('../types').SimulationCreate) =>
      request<import('../types').SimulationResultWithWarnings>(`/products/${productId}/simulations`, { method: 'POST', body: JSON.stringify(body) }),
    get: (productId: number, simulationId: number) =>
      request<import('../types').SimulationResponse>(`/products/${productId}/simulations/${simulationId}`),
  },
  listings: {
    list: (productId: number) =>
      request<import('../types').ListingResponse[]>(`/products/${productId}/listings`),
    create: (productId: number) =>
      request<import('../types').ListingResponse>(`/products/${productId}/listings`, { method: 'POST' }),
    get: (productId: number, listingId: number) =>
      request<import('../types').ListingResponse>(`/products/${productId}/listings/${listingId}`),
    update: (productId: number, listingId: number, body: import('../types').ListingUpdate) =>
      request<import('../types').ListingResponse>(`/products/${productId}/listings/${listingId}`, { method: 'PATCH', body: JSON.stringify(body) }),
  },
  imports: {
    list: () => request<import('../types').ImportListItem[]>('/imports'),
    get: (id: number) => request<import('../types').ImportRecordResponse>(`/imports/${id}`),
    template: () => fetch(`${API_BASE}/imports/template`).then(r => r.text()),
    preview: (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return fetch(`${API_BASE}/imports/preview`, { method: 'POST', body: fd }).then(async res => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail?.message || err.detail || res.statusText)
        }
        return res.json() as Promise<import('../types').CsvPreviewResponse>
      })
    },
    upload: (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return fetch(`${API_BASE}/imports/upload`, { method: 'POST', body: fd }).then(async res => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail?.message || (typeof err.detail === 'object' && err.detail?.errors ? err.detail.errors.map((e: { row: number; message: string }) => `Row ${e.row}: ${e.message}`).join('; ') : undefined) || JSON.stringify(err.detail))
        }
        return res.json() as Promise<import('../types').ImportRecordResponse>
      })
    },
  },
}
