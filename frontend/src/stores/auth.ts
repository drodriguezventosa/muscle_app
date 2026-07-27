import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { login as loginRequest, type AuthUser, type Session } from '@/api/auth'
import { setAccessToken } from '@/api/client'
import { i18n } from '@/i18n'

// The session is kept in localStorage so a reload does not sign the user out.
// Trade-off accepted for a token-based demo app: it is readable by scripts, so
// the token is short-lived (8 h) and carries no personal data beyond the user id
// (see ADR-0021). A cookie-based session would need CSRF handling server-side.
const KEY = 'muscleapp:session'

function load(): Session | null {
  try {
    const raw = globalThis.localStorage?.getItem(KEY)
    if (!raw) return null
    const session = JSON.parse(raw) as Session
    // Drop an expired token locally instead of discovering it on the next 401.
    if (!session.accessToken || session.expiresAt <= Date.now()) return null
    return session
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const restored = load()
  const user = ref<AuthUser | null>(restored?.user ?? null)
  const token = ref<string | null>(restored?.accessToken ?? null)
  const expiresAt = ref<number>(restored?.expiresAt ?? 0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  setAccessToken(token.value) // so the very first request after a reload is authenticated

  const isSignedIn = computed(() => Boolean(user.value))
  const isTrainer = computed(() => user.value?.role === 'trainer')

  function persist(session: Session | null): void {
    if (session) globalThis.localStorage?.setItem(KEY, JSON.stringify(session))
    else globalThis.localStorage?.removeItem(KEY)
  }

  function apply(session: Session | null): void {
    user.value = session?.user ?? null
    token.value = session?.accessToken ?? null
    expiresAt.value = session?.expiresAt ?? 0
    setAccessToken(token.value)
    persist(session)
  }

  async function signIn(email: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      apply(await loginRequest(email, password))
      return true
    } catch {
      // One message for every failure: the API deliberately does not say
      // whether it was the email or the password.
      error.value = i18n.global.t('auth.invalid')
      return false
    } finally {
      loading.value = false
    }
  }

  function signOut(): void {
    apply(null)
    error.value = null
  }

  return { user, token, isSignedIn, isTrainer, loading, error, signIn, signOut }
})
