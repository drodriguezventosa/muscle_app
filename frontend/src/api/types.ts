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

export type Goal = 'fat_loss' | 'hypertrophy' | 'strength'

export interface WorkoutItem {
  exercise: Exercise
  sets: number
  reps: string
  restSeconds: number
}

export interface Workout {
  goal: Goal
  name: string
  description: string
  difficulty: Difficulty
  bmi: number
  bmiCategory: string
  items: WorkoutItem[]
}

export interface Exercise {
  id: number
  name: string
  description: string
  equipment: Equipment
  difficulty: Difficulty
  videoUrl: string | null
  // How-to steps shown when there is no video, so every exercise has an example.
  steps: string[]
  targetedMuscles: TargetedMuscle[]
}
