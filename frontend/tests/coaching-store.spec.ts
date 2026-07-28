import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// Hoisted: `vi.mock` factories run before the imports below are evaluated.
const { myTrainer, hireTrainer, cancelTrainer } = vi.hoisted(() => ({
  myTrainer: vi.fn(),
  hireTrainer: vi.fn(),
  cancelTrainer: vi.fn(),
}))
vi.mock('@/api/coaching', () => ({ myTrainer, hireTrainer, cancelTrainer }))
vi.mock('@/api/client', () => ({ setAccessToken: vi.fn(), api: {} }))
vi.mock('@/api/auth', () => ({ login: vi.fn(), currentUser: vi.fn() }))

import { useAuthStore } from '@/stores/auth'
import { useCoachingStore } from '@/stores/coaching'
import { memoryStorage } from './support/memory-storage'

const ANA = {
  id: 1,
  name: 'Ana López',
  specialty: 'strength' as const,
  rating: 4.9,
  pricePerMonth: 39,
  bio: null,
  students: 7,
}

function signIn(role: 'client' | 'trainer'): void {
  useAuthStore().user = { id: 2, email: `${role}@demo.muscleapp`, name: 'Javier M.', role }
}

describe('coaching store', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', memoryStorage())
    setActivePinia(createPinia())
    myTrainer.mockReset()
    hireTrainer.mockReset()
    cancelTrainer.mockReset()
  })

  it('does not ask the API while signed out', async () => {
    const coaching = useCoachingStore()

    await coaching.load()

    expect(myTrainer).not.toHaveBeenCalled()
    expect(coaching.hasTrainer).toBe(false)
  })

  it('does not ask for a trainer when the user is one', async () => {
    signIn('trainer')
    const coaching = useCoachingStore()

    await coaching.load()

    expect(myTrainer).not.toHaveBeenCalled()
  })

  it('reads the link once and reports whether there is a trainer', async () => {
    signIn('client')
    myTrainer.mockResolvedValue(ANA)
    const coaching = useCoachingStore()

    await coaching.load()
    await coaching.load()

    expect(myTrainer).toHaveBeenCalledTimes(1) // cached for the session
    expect(coaching.hasTrainer).toBe(true)
    expect(coaching.trainer?.name).toBe('Ana López')
  })

  it('re-reads on demand, for when the link changed elsewhere', async () => {
    signIn('client')
    myTrainer.mockResolvedValue(null)
    const coaching = useCoachingStore()
    await coaching.load()

    myTrainer.mockResolvedValue(ANA)
    await coaching.load(true)

    expect(coaching.hasTrainer).toBe(true)
  })

  it('hiring keeps the trainer that came back', async () => {
    signIn('client')
    hireTrainer.mockResolvedValue(ANA)
    const coaching = useCoachingStore()

    await coaching.hire(1)

    expect(hireTrainer).toHaveBeenCalledWith(1)
    expect(coaching.trainer).toEqual(ANA)
  })

  it('cancelling leaves them without one', async () => {
    signIn('client')
    hireTrainer.mockResolvedValue(ANA)
    const coaching = useCoachingStore()
    await coaching.hire(1)

    await coaching.cancel()

    expect(cancelTrainer).toHaveBeenCalled()
    expect(coaching.hasTrainer).toBe(false)
  })

  it('forgets the trainer on reset, so the next student starts clean', async () => {
    signIn('client')
    myTrainer.mockResolvedValue(ANA)
    const coaching = useCoachingStore()
    await coaching.load()

    coaching.reset()

    expect(coaching.hasTrainer).toBe(false)
    expect(coaching.loaded).toBe(false)
  })
})
