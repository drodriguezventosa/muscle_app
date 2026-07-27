import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { memoryStorage } from './support/memory-storage'
import { useAuthStore } from '@/stores/auth'
import { useProgressStore } from '@/stores/progress'

// Hoisted: `vi.mock` factories run before the imports above are evaluated.
const { syncProgress } = vi.hoisted(() => ({ syncProgress: vi.fn().mockResolvedValue(1) }))
vi.mock('@/api/coaching', () => ({ syncProgress }))

function signIn(role: 'client' | 'trainer'): void {
  const auth = useAuthStore()
  auth.user = { id: 1, email: `${role}@demo.muscleapp`, name: 'Demo', role }
}

describe('progress sync', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', memoryStorage())
    setActivePinia(createPinia())
    syncProgress.mockClear()
  })

  it('does nothing while signed out', async () => {
    const progress = useProgressStore()
    progress.log(1, 'Squat', 60, true, 8)

    await progress.sync()

    expect(syncProgress).not.toHaveBeenCalled()
  })

  it('does nothing for a trainer, who has no progress of their own', async () => {
    signIn('trainer')
    const progress = useProgressStore()
    progress.log(1, 'Squat', 60, true, 8)

    await progress.sync()

    expect(syncProgress).not.toHaveBeenCalled()
  })

  it('pushes the whole local history for a signed-in student', async () => {
    signIn('client')
    const progress = useProgressStore()
    progress.log(1, 'Squat', 60, true, 8, '2026-07-01')

    await progress.sync({ weightKg: 78 })

    expect(syncProgress).toHaveBeenCalledWith(
      [{ exerciseId: 1, loggedOn: '2026-07-01', weightKg: 60, reps: 8, completed: true }],
      { weightKg: 78 },
    )
  })

  it('swallows a failed sync: localStorage is the source of truth', async () => {
    signIn('client')
    syncProgress.mockRejectedValueOnce(new Error('offline'))
    const progress = useProgressStore()
    progress.log(1, 'Squat', 60, true, 8)

    await expect(progress.sync()).resolves.toBeUndefined()
  })
})
