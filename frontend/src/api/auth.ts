// Coaching-area sign-in. There is no public sign-up: only the seeded demo
// accounts exist, and their credentials are shown in the form on purpose.

import { api } from './client'

export type UserRole = 'client' | 'trainer'

export interface AuthUser {
  id: number
  email: string
  name: string
  role: UserRole
}

interface SessionPayload {
  access_token: string
  token_type: string
  expires_in: number
  user: AuthUser
}

export interface Session {
  accessToken: string
  expiresAt: number // epoch ms, so a stale token is dropped without a request
  user: AuthUser
}

export async function login(email: string, password: string): Promise<Session> {
  const p = await api.post<SessionPayload>('/auth/login', { email, password })
  return {
    accessToken: p.access_token,
    expiresAt: Date.now() + p.expires_in * 1000,
    user: p.user,
  }
}

export function currentUser(): Promise<AuthUser> {
  return api.get<AuthUser>('/auth/me')
}
