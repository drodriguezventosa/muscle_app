import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Workout } from '@/api/types'

vi.mock('@/api/workouts', () => ({ generateWorkout: vi.fn() }))

import { generateWorkout } from '@/api/workouts'
import { useWorkoutsStore } from '@/stores/workouts'

const workout: Workout = {
  goal: 'hypertrophy',
  name: 'Rutina de hipertrofia',
  description: '',
  difficulty: 'intermediate',
  bmi: 24.7,
  bmiCategory: 'normal',
  items: [],
}

describe('workouts store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('requires height and weight before generating', async () => {
    const store = useWorkoutsStore()
    await store.generate()
    expect(store.error).not.toBeNull()
    expect(generateWorkout).not.toHaveBeenCalled()
  })

  it('generates a routine and maps home to bodyweight/dumbbell equipment', async () => {
    vi.mocked(generateWorkout).mockResolvedValue(workout)
    const store = useWorkoutsStore()
    store.heightCm = 180
    store.weightKg = 80
    store.place = 'home'
    store.goal = 'hypertrophy'
    await store.generate()

    expect(store.result).toEqual(workout)
    expect(store.error).toBeNull()
    expect(generateWorkout).toHaveBeenCalledWith(
      expect.objectContaining({ goal: 'hypertrophy', equipment: ['bodyweight', 'dumbbell'] }),
    )
  })
})
