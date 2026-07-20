// Nutrition API. Attributes go in the POST body (not the query string) so
// personal data stays out of URLs.

import { api } from './client'
import type { ActivityLevel, Food, NutritionGoal, NutritionTargets } from './types'
import { i18n } from '@/i18n'

interface FoodPayload {
  id: number
  name: string
  category: string
  kcal: number
  protein_g: number
  carbs_g: number
  fat_g: number
  tags: string[]
}

function toFood(f: FoodPayload): Food {
  return {
    id: f.id,
    name: f.name,
    category: f.category,
    kcal: f.kcal,
    proteinG: f.protein_g,
    carbsG: f.carbs_g,
    fatG: f.fat_g,
    tags: f.tags,
  }
}

export async function listFoods(): Promise<Food[]> {
  const lang = i18n.global.locale.value
  const p = await api.get<FoodPayload[]>(`/nutrition/foods?lang=${lang}`)
  return p.map(toFood)
}

export interface MealRecommendation {
  reply: string
  foods: Food[]
}

export async function recommendMeals(message: string): Promise<MealRecommendation> {
  const lang = i18n.global.locale.value
  const p = await api.post<{ reply: string; foods: FoodPayload[] }>(
    `/nutrition/recommendations?lang=${lang}`,
    { message },
  )
  return { reply: p.reply, foods: p.foods.map(toFood) }
}

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
