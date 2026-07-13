import { defineStore } from 'pinia'
import { ref } from 'vue'

import { generateWorkout, type GenerateRequest } from '@/api/workouts'
import type { Difficulty, Equipment, Goal, Workout } from '@/api/types'
import { i18n } from '@/i18n'

// Where the user trains → which equipment the generator may use.
export type Place = 'gym' | 'home'
const PLACE_EQUIPMENT: Record<Place, Equipment[] | undefined> = {
  gym: undefined, // no restriction
  home: ['bodyweight', 'dumbbell'],
}

export const useWorkoutsStore = defineStore('workouts', () => {
  const goal = ref<Goal>('hypertrophy')
  const experience = ref<Difficulty>('beginner')
  const place = ref<Place>('gym')
  const sex = ref<'male' | 'female' | 'other' | ''>('')
  const age = ref<number | null>(null)
  const heightCm = ref<number | null>(null)
  const weightKg = ref<number | null>(null)

  const result = ref<Workout | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function generate(): Promise<void> {
    if (!heightCm.value || !weightKg.value) {
      error.value = i18n.global.t('workouts.errors.attributes')
      return
    }
    error.value = null
    loading.value = true
    try {
      const req: GenerateRequest = {
        goal: goal.value,
        experience: experience.value,
        heightCm: heightCm.value,
        weightKg: weightKg.value,
        equipment: PLACE_EQUIPMENT[place.value],
      }
      if (sex.value) req.sex = sex.value
      if (age.value) req.age = age.value
      result.value = await generateWorkout(req)
    } catch {
      error.value = i18n.global.t('workouts.errors.generate')
    } finally {
      loading.value = false
    }
  }

  return {
    goal,
    experience,
    place,
    sex,
    age,
    heightCm,
    weightKg,
    result,
    loading,
    error,
    generate,
  }
})
