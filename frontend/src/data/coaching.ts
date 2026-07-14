// Sample data for the trainers/coaching preview. This is a mockup of the future
// (monetizable) personal-trainer feature — no login, no real payments, no backend.

import type { Difficulty, Goal } from '@/api/types'

export interface Trainer {
  id: number
  name: string
  specialty: Goal
  rating: number
  pricePerMonth: number // euros
  initials: string
}

export interface StudentProgress {
  exercise: string
  best: number // kg
  sessions: number
}

export interface Student {
  id: number
  name: string
  goal: Goal
  level: Difficulty
  lastActiveDays: number
  initials: string
  progress: StudentProgress[]
}

export const TRAINERS: Trainer[] = [
  {
    id: 1,
    name: 'Ana López',
    specialty: 'strength',
    rating: 4.9,
    pricePerMonth: 39,
    initials: 'AL',
  },
  {
    id: 2,
    name: 'Marco Ruiz',
    specialty: 'hypertrophy',
    rating: 4.8,
    pricePerMonth: 45,
    initials: 'MR',
  },
  {
    id: 3,
    name: 'Sara Gil',
    specialty: 'fat_loss',
    rating: 5.0,
    pricePerMonth: 35,
    initials: 'SG',
  },
  {
    id: 4,
    name: 'Leo Torres',
    specialty: 'hypertrophy',
    rating: 4.7,
    pricePerMonth: 29,
    initials: 'LT',
  },
]

export const STUDENTS: Student[] = [
  {
    id: 1,
    name: 'Javier M.',
    goal: 'hypertrophy',
    level: 'intermediate',
    lastActiveDays: 2,
    initials: 'JM',
    progress: [
      { exercise: 'Barbell curl', best: 35, sessions: 6 },
      { exercise: 'Barbell bench press', best: 70, sessions: 8 },
      { exercise: 'Barbell back squat', best: 90, sessions: 7 },
    ],
  },
  {
    id: 2,
    name: 'Lucía P.',
    goal: 'fat_loss',
    level: 'beginner',
    lastActiveDays: 1,
    initials: 'LP',
    progress: [
      { exercise: 'Goblet squat', best: 16, sessions: 4 },
      { exercise: 'Lat pulldown', best: 30, sessions: 5 },
    ],
  },
  {
    id: 3,
    name: 'Diego R.',
    goal: 'strength',
    level: 'advanced',
    lastActiveDays: 5,
    initials: 'DR',
    progress: [
      { exercise: 'Barbell back squat', best: 140, sessions: 12 },
      { exercise: 'Romanian deadlift', best: 120, sessions: 10 },
      { exercise: 'Overhead press', best: 55, sessions: 9 },
    ],
  },
]

// Exercises a trainer can assign (a small slice of the catalog for the demo).
export const ASSIGNABLE: string[] = [
  'Barbell back squat',
  'Barbell bench press',
  'Romanian deadlift',
  'Pull-up',
  'Overhead press',
  'Barbell curl',
  'Triceps rope pushdown',
  'Plank',
  'Leg press',
  'Bulgarian split squat',
]
