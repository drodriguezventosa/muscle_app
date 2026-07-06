// Explorer API calls. Maps the backend snake_case payloads to camelCase types.

import { api } from './client'
import type { Difficulty, Equipment, Exercise, Muscle, MuscleGroup, MuscleRole } from './types'
import { i18n } from '@/i18n'

// Content locale sent to the backend so names/descriptions come back translated.
function lang(): string {
  return i18n.global.locale.value
}

interface MusclePayload {
  id: number
  name: string
  muscle_group: MuscleGroup
  svg_id: string
  description: string
}

interface TargetedMusclePayload {
  muscle_id: number
  role: MuscleRole
}

export interface ExercisePayload {
  id: number
  name: string
  description: string
  equipment: Equipment
  difficulty: Difficulty
  targeted_muscles: TargetedMusclePayload[]
}

function toMuscle(p: MusclePayload): Muscle {
  return {
    id: p.id,
    name: p.name,
    muscleGroup: p.muscle_group,
    svgId: p.svg_id,
    description: p.description,
  }
}

export function toExercise(p: ExercisePayload): Exercise {
  return {
    id: p.id,
    name: p.name,
    description: p.description,
    equipment: p.equipment,
    difficulty: p.difficulty,
    targetedMuscles: p.targeted_muscles.map((t) => ({ muscleId: t.muscle_id, role: t.role })),
  }
}

export async function listMuscles(): Promise<Muscle[]> {
  const payload = await api.get<MusclePayload[]>(`/muscles?lang=${lang()}`)
  return payload.map(toMuscle)
}

export async function getMuscleExercises(svgId: string): Promise<Exercise[]> {
  const payload = await api.get<ExercisePayload[]>(`/muscles/${svgId}/exercises?lang=${lang()}`)
  return payload.map(toExercise)
}
