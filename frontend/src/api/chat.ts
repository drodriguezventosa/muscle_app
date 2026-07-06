// Chatbot API call. Reuses the explorer's exercise mapping.

import { api } from './client'
import { toExercise, type ExercisePayload } from './explorer'
import type { Difficulty, Equipment, Exercise } from './types'
import { i18n } from '@/i18n'

export interface Recommendation {
  reply: string
  exercises: Exercise[]
}

interface RecommendationPayload {
  reply: string
  exercises: ExercisePayload[]
}

export async function recommend(
  message: string,
  equipment?: Equipment,
  difficulty?: Difficulty,
): Promise<Recommendation> {
  const payload = await api.post<RecommendationPayload>(
    `/chat/recommendations?lang=${i18n.global.locale.value}`,
    { message, equipment, difficulty },
  )
  return { reply: payload.reply, exercises: payload.exercises.map(toExercise) }
}
