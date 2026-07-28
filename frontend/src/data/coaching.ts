// The trainers on offer in the hiring cards. Still a mockup — no real payments.
// Students, their history and their plans all come from the API now.

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
