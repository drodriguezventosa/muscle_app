import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Exercise, Muscle } from '@/api/types'

vi.mock('@/api/explorer', () => ({
  listMuscles: vi.fn(),
  getMuscleExercises: vi.fn(),
}))

import { getMuscleExercises, listMuscles } from '@/api/explorer'
import { useExplorerStore } from '@/stores/explorer'

const muscles: Muscle[] = [
  { id: 1, name: 'Chest', muscleGroup: 'chest', svgId: 'chest', description: '' },
]
const exercises: Exercise[] = [
  {
    id: 10,
    name: 'Push-up',
    description: '',
    equipment: 'bodyweight',
    difficulty: 'beginner',
    videoUrl: null,
    targetedMuscles: [{ muscleId: 1, role: 'primary' }],
  },
]

describe('explorer store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('loads muscles', async () => {
    vi.mocked(listMuscles).mockResolvedValue(muscles)
    const store = useExplorerStore()
    await store.loadMuscles()
    expect(store.muscles).toEqual(muscles)
    expect(store.error).toBeNull()
  })

  it('selects a muscle and loads its exercises', async () => {
    vi.mocked(listMuscles).mockResolvedValue(muscles)
    vi.mocked(getMuscleExercises).mockResolvedValue(exercises)
    const store = useExplorerStore()
    await store.loadMuscles()
    await store.selectMuscle('chest')
    expect(store.selectedSvgId).toBe('chest')
    expect(store.selectedMuscle?.name).toBe('Chest')
    expect(store.exercises).toEqual(exercises)
    expect(store.loading).toBe(false)
  })

  it('sets an error message when exercise loading fails', async () => {
    vi.mocked(getMuscleExercises).mockRejectedValue(new Error('network'))
    const store = useExplorerStore()
    await store.selectMuscle('chest')
    expect(store.error).not.toBeNull()
    expect(store.loading).toBe(false)
  })
})
