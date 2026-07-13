// Workout generator API call. Attributes go in the POST body (not the query
// string) so personal data stays out of URLs.

import { api } from './client'
import { toExercise, type ExercisePayload } from './explorer'
import type { Difficulty, Equipment, Goal, Workout } from './types'
import { i18n } from '@/i18n'

export interface GenerateRequest {
  goal: Goal
  experience: Difficulty
  heightCm: number
  weightKg: number
  sex?: 'male' | 'female' | 'other'
  age?: number
  equipment?: Equipment[]
}

interface WorkoutItemPayload {
  exercise: ExercisePayload
  sets: number
  reps: string
  rest_seconds: number
}

interface WorkoutPayload {
  goal: Goal
  name: string
  description: string
  difficulty: Difficulty
  bmi: number
  bmi_category: string
  items: WorkoutItemPayload[]
}

export async function generateWorkout(req: GenerateRequest): Promise<Workout> {
  const lang = i18n.global.locale.value
  const payload = await api.post<WorkoutPayload>(`/workouts/generate?lang=${lang}`, {
    goal: req.goal,
    experience: req.experience,
    height_cm: req.heightCm,
    weight_kg: req.weightKg,
    sex: req.sex,
    age: req.age,
    equipment: req.equipment,
  })
  return {
    goal: payload.goal,
    name: payload.name,
    description: payload.description,
    difficulty: payload.difficulty,
    bmi: payload.bmi,
    bmiCategory: payload.bmi_category,
    items: payload.items.map((i) => ({
      exercise: toExercise(i.exercise),
      sets: i.sets,
      reps: i.reps,
      restSeconds: i.rest_seconds,
    })),
  }
}
