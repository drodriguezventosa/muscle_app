// Nutrition API. Attributes go in the POST body (not the query string) so
// personal data stays out of URLs.

import { api } from './client'
import type { ActivityLevel, NutritionGoal, NutritionTargets } from './types'

export interface NutritionRequest {
  sex?: 'male' | 'female' | 'other'
  age: number
  heightCm: number
  weightKg: number
  activity: ActivityLevel
  goal: NutritionGoal
}

interface NutritionTargetsPayload {
  bmr: number
  tdee: number
  calories: number
  protein_g: number
  carbs_g: number
  fat_g: number
  bmi: number
  bmi_category: string
  goal: NutritionGoal
  warning: string | null
}

export async function calculateNutrition(req: NutritionRequest): Promise<NutritionTargets> {
  const p = await api.post<NutritionTargetsPayload>('/nutrition/calculate', {
    sex: req.sex,
    age: req.age,
    height_cm: req.heightCm,
    weight_kg: req.weightKg,
    activity: req.activity,
    goal: req.goal,
  })
  return {
    bmr: p.bmr,
    tdee: p.tdee,
    calories: p.calories,
    proteinG: p.protein_g,
    carbsG: p.carbs_g,
    fatG: p.fat_g,
    bmi: p.bmi,
    bmiCategory: p.bmi_category,
    goal: p.goal,
    warning: p.warning,
  }
}
