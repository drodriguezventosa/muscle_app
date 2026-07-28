// Sample data for the trainers/coaching preview: the trainers on offer and the
// exercises a coach can assign. Still a mockup — no real payments. The students
// are no longer here: they come from the coaching API (see ADR-0021).

import type { Goal } from '@/api/types'

export interface Trainer {
  id: number
  name: string
  specialty: Goal
  rating: number
  pricePerMonth: number // euros
  initials: string
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
