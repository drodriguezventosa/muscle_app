// Frontend-facing types for the muscle explorer. Field names are camelCase;
// the API client maps the backend's snake_case payloads into these.

export type MuscleGroup = 'chest' | 'back' | 'shoulders' | 'arms' | 'core' | 'legs' | 'glutes'

export type Equipment =
  'bodyweight' | 'dumbbell' | 'barbell' | 'machine' | 'cable' | 'kettlebell' | 'band'

export type Difficulty = 'beginner' | 'intermediate' | 'advanced'

export type MuscleRole = 'primary' | 'secondary'

export interface Muscle {
  id: number
  name: string
  muscleGroup: MuscleGroup
  svgId: string
  description: string
}

export interface TargetedMuscle {
  muscleId: number
  role: MuscleRole
}

export interface Exercise {
  id: number
  name: string
  description: string
  equipment: Equipment
  difficulty: Difficulty
  targetedMuscles: TargetedMuscle[]
}
