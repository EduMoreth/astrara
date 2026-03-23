const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ChartRequest {
  name: string
  year: number
  month: number
  day: number
  hour: number
  minute: number
  city: string
  country?: string
}

interface ChartResponse {
  svg: string
  positions: Record<
    string,
    { sign: string; deg: number }
  >
}

interface AuthResponse {
  access_token: string
  token_type: string
}

interface UserChart {
  id: string
  name: string
  birth_date: string
  birth_time: string
  birth_city: string
  positions_json: Record<string, { sign: string; deg: number }>
  svg_data: string
  created_at: string
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== 'undefined' ? localStorage.getItem('astrara_token') : null

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Erro desconhecido' }))
    throw new Error(error.detail || `Erro ${res.status}`)
  }

  return res.json()
}

export async function generateChart(data: ChartRequest): Promise<ChartResponse> {
  return request<ChartResponse>('/chart/generate', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function register(
  name: string,
  email: string,
  password: string
): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  })
}

export async function login(
  email: string,
  password: string
): Promise<AuthResponse> {
  return request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function getUserCharts(): Promise<UserChart[]> {
  return request<UserChart[]>('/user/charts')
}

export async function saveChart(chartId: string): Promise<void> {
  return request('/user/charts/save', {
    method: 'POST',
    body: JSON.stringify({ chart_id: chartId }),
  })
}
