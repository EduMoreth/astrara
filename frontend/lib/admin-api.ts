const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://astrara-production.up.railway.app'

function getAdminToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('admin_token')
}

export function setAdminToken(token: string) {
  localStorage.setItem('admin_token', token)
}

export function clearAdminToken() {
  localStorage.removeItem('admin_token')
}

export function isAdminLoggedIn(): boolean {
  return !!getAdminToken()
}

async function adminRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAdminToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers })

  if (res.status === 401) {
    clearAdminToken()
    if (typeof window !== 'undefined') {
      window.location.replace('/admin/login')
    }
    throw new Error('Sessao expirada')
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Erro desconhecido' }))
    throw new Error(error.detail || `Erro ${res.status}`)
  }

  return res.json()
}

// ── Auth ──────────────────────────────────────────────
export async function adminLogin(email: string, password: string) {
  const res = await fetch(`${API_URL}/admin/api/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Credenciais invalidas' }))
    throw new Error(err.detail)
  }
  return res.json()
}

// ── Stats ─────────────────────────────────────────────
export const getStats = () => adminRequest<Record<string, number>>('/admin/api/stats')
export const getUsersDaily = (days = 30) => adminRequest<Array<{ date: string; count: number }>>(`/admin/api/stats/users-daily?days=${days}`)
export const getRevenueDaily = () => adminRequest<Array<{ date: string; total: number }>>('/admin/api/stats/revenue-daily')

// ── Users ─────────────────────────────────────────────
export interface AdminUser {
  id: string
  name: string
  email: string
  plan: string
  status: string
  credits: number
  chart_count: number
  created_at: string
}

export const getUsers = (page = 1, limit = 20, search = '', plan = '', status = '') =>
  adminRequest<{ users: AdminUser[]; total: number; page: number; pages: number }>(
    `/admin/api/users?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}&plan=${plan}&status=${status}`
  )

export const getUser = (id: string) => adminRequest<Record<string, unknown>>(`/admin/api/users/${id}`)
export const updateUser = (id: string, data: Record<string, string>) =>
  adminRequest(`/admin/api/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
export const deleteUser = (id: string) =>
  adminRequest(`/admin/api/users/${id}`, { method: 'DELETE' })
export const banUser = (id: string, reason: string) =>
  adminRequest(`/admin/api/users/${id}/ban`, { method: 'POST', body: JSON.stringify({ reason }) })
export const manageCredits = (id: string, type: string, amount: number, reason: string, kind: string = 'standard') =>
  adminRequest(`/admin/api/users/${id}/credits`, {
    method: 'POST', body: JSON.stringify({ type, amount, reason, kind })
  })

// ── Products ──────────────────────────────────────────
export interface AdminProduct {
  id: string
  name: string
  description: string
  type: string
  price_cents: number
  credits: number
  stripe_product_id: string | null
  stripe_price_id: string | null
  active: boolean
  created_at: string
}

export const getProducts = () => adminRequest<AdminProduct[]>('/admin/api/products')
export const createProduct = (data: Record<string, unknown>) =>
  adminRequest('/admin/api/products', { method: 'POST', body: JSON.stringify(data) })
export const updateProduct = (id: string, data: Record<string, unknown>) =>
  adminRequest(`/admin/api/products/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
export const toggleProduct = (id: string) =>
  adminRequest<{ active: boolean }>(`/admin/api/products/${id}/toggle`, { method: 'PATCH' })
export const deleteProduct = (id: string) =>
  adminRequest(`/admin/api/products/${id}`, { method: 'DELETE' })

// ── Transactions ──────────────────────────────────────
export const getTransactions = (page = 1, limit = 20, status = '') =>
  adminRequest<{ transactions: Record<string, unknown>[]; total: number; page: number; pages: number }>(
    `/admin/api/transactions?page=${page}&limit=${limit}&status=${status}`
  )
export const getRevenue = () => adminRequest<{ monthly: number; yearly: number; total_transactions: number }>('/admin/api/revenue')

// ── Charts ────────────────────────────────────────────
export const getCharts = (page = 1, limit = 20) =>
  adminRequest<{ charts: Record<string, unknown>[]; total: number; page: number; pages: number }>(
    `/admin/api/charts?page=${page}&limit=${limit}`
  )
export const deleteChart = (id: string) =>
  adminRequest(`/admin/api/charts/${id}`, { method: 'DELETE' })

// ── Config ────────────────────────────────────────────
export const getConfig = () => adminRequest<Record<string, { value: string; description: string }>>('/admin/api/config')
export const updateConfig = (configs: Record<string, string>) =>
  adminRequest('/admin/api/config', { method: 'PATCH', body: JSON.stringify({ configs }) })

// ── Logs ──────────────────────────────────────────────
export const getLogs = (page = 1, limit = 50, action = '') =>
  adminRequest<{ logs: Record<string, unknown>[]; total: number; page: number; pages: number }>(
    `/admin/api/logs?page=${page}&limit=${limit}&action=${encodeURIComponent(action)}`
  )
