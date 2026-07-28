// Typed HTTP client for the MuscleApp API.
// The base URL is injected at build time via Vite env vars (12-factor).

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

// The access token lives in the auth store; the client only holds a reference so
// that importing it here would not create a store <-> client import cycle.
let accessToken: string | null = null

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // FormData must keep the browser's own multipart Content-Type (it carries the
  // boundary), so the JSON default is only applied to non-form bodies.
  const isForm = init?.body instanceof FormData
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(isForm ? {} : { 'Content-Type': 'application/json' }),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...(init?.headers ?? {}),
    },
  })
  if (!response.ok) {
    throw new ApiError(response.status, `Request to ${path} failed`)
  }
  // 204 has no body to parse; callers of those endpoints expect nothing back.
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  upload: <T>(path: string, form: FormData) => request<T>(path, { method: 'POST', body: form }),
  remove: (path: string) => request<void>(path, { method: 'DELETE' }),
}
