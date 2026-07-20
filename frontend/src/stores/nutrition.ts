import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

import { calculateNutrition, listFoods, type NutritionRequest } from '@/api/nutrition'
import type { ActivityLevel, Food, NutritionGoal, NutritionTargets } from '@/api/types'
import { i18n } from '@/i18n'

// Only non-personal preferences are persisted client-side. Biometric data
// (sex/age/height/weight) is kept in-session only and never written to storage
// — it's sensitive and, on a no-login app, storing it in clear text adds risk
// without benefit (CodeQL "clear-text storage"; ADR-0006 privacy stance).
const KEY = 'muscleapp:nutrition'

interface Persisted {
  activity: ActivityLevel
  goal: NutritionGoal
}

function load(): Partial<Persisted> {
  try {
    const raw = globalThis.localStorage?.getItem(KEY)
    if (raw) return JSON.parse(raw) as Partial<Persisted>
  } catch {
    // ignore
  }
  return {}
}

export const useNutritionStore = defineStore('nutrition', () => {
  const saved = load()
  // Biometric inputs live in-session only (not persisted — see note above).
  const sex = ref<'male' | 'female' | 'other' | ''>('')
  const age = ref<number | null>(null)
  const heightCm = ref<number | null>(null)
  const weightKg = ref<number | null>(null)
  const activity = ref<ActivityLevel>(saved.activity ?? 'moderate')
  const goal = ref<NutritionGoal>(saved.goal ?? 'maintain')

  const result = ref<NutritionTargets | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Changing any input invalidates a shown result (the numbers would be stale),
  // so clear it and let the user press Calculate again. The inputs are kept.
  watch([sex, age, heightCm, weightKg, activity, goal], () => {
    if (result.value) result.value = null
  })

  const foods = ref<Food[]>([])
  async function loadFoods(): Promise<void> {
    try {
      foods.value = await listFoods()
    } catch {
      // catalog is best-effort; the calculator still works without it
    }
  }
  // Meal recommendations now live in the global assistant (ChatWidget), which
  // routes to the meal endpoint on the nutrition page.

  function persist(): void {
    const data: Persisted = { activity: activity.value, goal: goal.value }
    globalThis.localStorage?.setItem(KEY, JSON.stringify(data))
  }

  async function calculate(): Promise<void> {
    if (!heightCm.value || !weightKg.value || !age.value) {
      error.value = i18n.global.t('nutrition.errors.attributes')
      return
    }
    error.value = null
    loading.value = true
    try {
      const req: NutritionRequest = {
        age: age.value,
        heightCm: heightCm.value,
        weightKg: weightKg.value,
        activity: activity.value,
        goal: goal.value,
      }
      if (sex.value) req.sex = sex.value
      result.value = await calculateNutrition(req)
      persist()
    } catch {
      error.value = i18n.global.t('nutrition.errors.calculate')
    } finally {
      loading.value = false
    }
  }

  return {
    sex,
    age,
    heightCm,
    weightKg,
    activity,
    goal,
    result,
    loading,
    error,
    calculate,
    foods,
    loadFoods,
  }
})
