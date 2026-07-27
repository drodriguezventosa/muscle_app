import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { login } = vi.hoisted(() => ({ login: vi.fn() }))

vi.mock('@/api/auth', () => ({ login, currentUser: vi.fn() }))
vi.mock('@/api/client', () => ({ setAccessToken: vi.fn(), api: {} }))

import { setAccessToken } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const SESSION = {
  accessToken: 'token-123',
  expiresAt: Date.now() + 3600_000,
  user: { id: 1, email: 'coach@demo.app', name: 'Ana', role: 'trainer' as const },
}
const KEY = 'muscleapp:session'

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    login.mockReset()
    globalThis.localStorage?.clear()
  })

  it('signs in, exposes the role and hands the token to the API client', async () => {
    login.mockResolvedValue(SESSION)
    const store = useAuthStore()

    expect(await store.signIn('coach@demo.app', 'muscleapp-demo')).toBe(true)
    expect(store.isSignedIn).toBe(true)
    expect(store.isTrainer).toBe(true)
    expect(setAccessToken).toHaveBeenCalledWith('token-123')
  })

  it('reports one generic error when the credentials are rejected', async () => {
    login.mockRejectedValue(new Error('401'))
    const store = useAuthStore()

    expect(await store.signIn('coach@demo.app', 'wrong')).toBe(false)
    expect(store.isSignedIn).toBe(false)
    expect(store.error).toBeTruthy()
  })

  it('signing out clears the session everywhere', async () => {
    login.mockResolvedValue(SESSION)
    const store = useAuthStore()
    await store.signIn('coach@demo.app', 'muscleapp-demo')

    store.signOut()

    expect(store.isSignedIn).toBe(false)
    // `?? null` because localStorage is absent in some Node/jsdom combinations.
    expect(globalThis.localStorage?.getItem(KEY) ?? null).toBeNull()
    expect(setAccessToken).toHaveBeenLastCalledWith(null)
  })

  it('ignores a stored session whose token has already expired', () => {
    globalThis.localStorage?.setItem(
      KEY,
      JSON.stringify({ ...SESSION, expiresAt: Date.now() - 1000 }),
    )
    expect(useAuthStore().isSignedIn).toBe(false)
  })
})
