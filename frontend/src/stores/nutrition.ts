import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  calculateNutrition,
  listFoods,
  recommendMeals,
  type NutritionRequest,
} from '@/api/nutrition'
import type { ActivityLevel, Food, NutritionGoal, NutritionTargets } from '@/api/types'
import { i18n } from '@/i18n'

// Last inputs + result persisted client-side (no login, ADR-0006/0011).
const KEY = 'muscleapp:nutrition'

interface Persisted {
  sex: 'male' | 'female' | 'other' | ''
  age: number | null
  heightCm: number | null
  weightKg: number | null
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
  const sex = ref<'male' | 'female' | 'other' | ''>(saved.sex ?? '')
  const age = ref<number | null>(saved.age ?? null)
  const heightCm = ref<number | null>(saved.heightCm ?? null)
  const weightKg = ref<number | null>(saved.weightKg ?? null)
  const activity = ref<ActivityLevel>(saved.activity ?? 'moderate')
  const goal = ref<NutritionGoal>(saved.goal ?? 'maintain')

  const result = ref<NutritionTargets | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const foods = ref<Food[]>([])
  async function loadFoods(): Promise<void> {
    try {
      foods.value = await listFoods()
    } catch {
      // catalog is best-effort; the calculator still works without it
    }
  }

  // Meal recommendation chat (RAG over the food catalog).
  const chatReply = ref<string | null>(null)
  const chatFoods = ref<Food[]>([])
  const chatLoading = ref(false)
  async function recommend(message: string): Promise<void> {
    if (!message.trim()) return
    chatLoading.value = true
    try {
      const rec = await recommendMeals(message)
      chatReply.value = rec.reply
      chatFoods.value = rec.foods
    } catch {
      chatReply.value = i18n.global.t('nutrition.chat.error')
      chatFoods.value = []
    } finally {
      chatLoading.value = false
    }
  }

  function persist(): void {
    const data: Persisted = {
      sex: sex.value,
      age: age.value,
      heightCm: heightCm.value,
      weightKg: weightKg.value,
      activity: activity.value,
      goal: goal.value,
    }
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
    chatReply,
    chatFoods,
    chatLoading,
    recommend,
  }
})
