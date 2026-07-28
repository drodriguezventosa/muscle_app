// Training calendar: what the trainer schedules and what the student reports.

import { api } from './client'
import { i18n } from '@/i18n'

export type PlanItemStatus = 'pending' | 'done' | 'partial' | 'missed'

export interface PlanItem {
  id: number
  exerciseId: number
  exerciseName: string
  scheduledOn: string // YYYY-MM-DD
  targetSets: number
  targetReps: number
  targetWeightKg: number | null
  notes: string | null
  doneWeightKg: number | null
  doneReps: number | null
  status: PlanItemStatus
}

export interface ScheduleRequest {
  exerciseId: number
  scheduledOn: string
  targetSets?: number
  targetReps?: number
  targetWeightKg?: number | null
  notes?: string | null
}

interface PlanItemPayload {
  id: number
  exercise_id: number
  exercise_name: string
  scheduled_on: string
  target_sets: number
  target_reps: number
  target_weight_kg: number | null
  notes: string | null
  done_weight_kg: number | null
  done_reps: number | null
  status: PlanItemStatus
}

function toItem(payload: PlanItemPayload): PlanItem {
  return {
    id: payload.id,
    exerciseId: payload.exercise_id,
    exerciseName: payload.exercise_name,
    scheduledOn: payload.scheduled_on,
    targetSets: payload.target_sets,
    targetReps: payload.target_reps,
    targetWeightKg: payload.target_weight_kg,
    notes: payload.notes,
    doneWeightKg: payload.done_weight_kg,
    doneReps: payload.done_reps,
    status: payload.status,
  }
}

function range(from: string, to: string): string {
  return `from=${from}&to=${to}&lang=${i18n.global.locale.value}`
}

/** The signed-in student's own calendar. */
export async function myPlan(from: string, to: string): Promise<PlanItem[]> {
  const payload = await api.get<PlanItemPayload[]>(`/coaching/me/plan?${range(from, to)}`)
  return payload.map(toItem)
}

/** The calendar of one of the trainer's students. */
export async function studentPlan(
  studentId: number,
  from: string,
  to: string,
): Promise<PlanItem[]> {
  const payload = await api.get<PlanItemPayload[]>(
    `/coaching/students/${studentId}/plan?${range(from, to)}`,
  )
  return payload.map(toItem)
}

/** Schedule an exercise, or edit the targets already set for that day. */
export async function scheduleExercise(
  studentId: number,
  request: ScheduleRequest,
): Promise<PlanItem> {
  const payload = await api.post<PlanItemPayload>(
    `/coaching/students/${studentId}/plan?lang=${i18n.global.locale.value}`,
    {
      exercise_id: request.exerciseId,
      scheduled_on: request.scheduledOn,
      target_sets: request.targetSets,
      target_reps: request.targetReps,
      target_weight_kg: request.targetWeightKg,
      notes: request.notes,
    },
  )
  return toItem(payload)
}

export function unscheduleExercise(itemId: number): Promise<void> {
  return api.remove(`/coaching/plan/${itemId}`)
}

/** Report what was lifted; returns the item with its status recomputed. */
export async function reportPlanItem(
  itemId: number,
  weightKg: number,
  reps: number,
  completed: boolean,
): Promise<PlanItem> {
  const payload = await api.post<PlanItemPayload>(
    `/coaching/me/plan/${itemId}/report?lang=${i18n.global.locale.value}`,
    { weight_kg: weightKg, reps, completed },
  )
  return toItem(payload)
}
