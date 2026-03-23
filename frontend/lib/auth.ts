export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('astrara_token')
}

export function setToken(token: string): void {
  localStorage.setItem('astrara_token', token)
}

export function removeToken(): void {
  localStorage.removeItem('astrara_token')
}

export function isAuthenticated(): boolean {
  return !!getToken()
}

export function parseJwt(token: string): { sub: string; name: string; email: string; exp: number } | null {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonPayload)
  } catch {
    return null
  }
}

export function getUserFromToken() {
  const token = getToken()
  if (!token) return null
  const payload = parseJwt(token)
  if (!payload) return null
  if (payload.exp * 1000 < Date.now()) {
    removeToken()
    return null
  }
  return payload
}
