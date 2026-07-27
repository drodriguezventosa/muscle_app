// Coaching API: the trainer's roster and the student's progress sync.
// Every endpoint here needs a signed-in user; the token is added by the client.

import { api } from './client'
import { i18n } from '@/i18n'
import type { Difficulty, Goal } from './types'

export interface StudentSummary {
  id: number
  name: string
  goal: Goal | null
  level: Difficulty | null
  age: number | null
  heightCm: number | null
  weightKg: number | null
  bmi: number | null
  sessionsLast30d: number
  lastSessionOn: string | null // YYYY-MM-DD
}

export interface SeriesPoint {
  on: string // YYYY-MM-DD
  value: number
}

export interface ExerciseProgression {
  exerciseId: number
  exerciseName: string
  points: SeriesPoint[]
  gainPct: number
}

export interface WeeklyAdherence {
  weekStart: string // YYYY-MM-DD (a Monday)
  sessions: number
}

export interface StudentDashboard {
  student: StudentSummary
  bodyWeight: SeriesPoint[]
  strength: ExerciseProgression[]
  adherence: WeeklyAdherence[]
  totalSessions: number
  weightChangeKg: number | null
}

/** One logged session, as the browser recorded it. */
export interface SessionSync {
  exerciseId: number
  loggedOn: string
  weightKg: number
  reps: number
  completed: boolean
}

/** Attributes the user has filled in elsewhere; anything omitted is left as is. */
export interface ProfileSync {
  weightKg?: number
  heightCm?: number
  age?: number
  goal?: Goal
  level?: Difficulty
}

interface StudentPayload {
  id: number
  name: string
  goal: Goal | null
  level: Difficulty | null
  age: number | null
  height_cm: number | null
  weight_kg: number | null
  bmi: number | null
  sessions_last_30d: number
  last_session_on: string | null
}

interface DashboardPayload {
  student: StudentPayload
  body_weight: SeriesPoint[]
  strength: {
    exercise_id: number
    exercise_name: string
    points: SeriesPoint[]
    gain_pct: number
  }[]
  adherence: { week_start: string; sessions: number }[]
  total_sessions: number
  weight_change_kg: number | null
}

function toStudent(payload: StudentPayload): StudentSummary {
  return {
    id: payload.id,
    name: payload.name,
    goal: payload.goal,
    level: payload.level,
    age: payload.age,
    heightCm: payload.height_cm,
    weightKg: payload.weight_kg,
    bmi: payload.bmi,
    sessionsLast30d: payload.sessions_last_30d,
    lastSessionOn: payload.last_session_on,
  }
}

function toDashboard(payload: DashboardPayload): StudentDashboard {
  return {
    student: toStudent(payload.student),
    bodyWeight: payload.body_weight,
    strength: payload.strength.map((progression) => ({
      exerciseId: progression.exercise_id,
      exerciseName: progression.exercise_name,
      points: progression.points,
      gainPct: progression.gain_pct,
    })),
    adherence: payload.adherence.map((week) => ({
      weekStart: week.week_start,
      sessions: week.sessions,
    })),
    totalSessions: payload.total_sessions,
    weightChangeKg: payload.weight_change_kg,
  }
}

export async function listStudents(): Promise<StudentSummary[]> {
  const payload = await api.get<StudentPayload[]>('/coaching/students')
  return payload.map(toStudent)
}

export async function getStudent(studentId: number): Promise<StudentDashboard> {
  const lang = i18n.global.locale.value
  return toDashboard(
    await api.get<DashboardPayload>(`/coaching/students/${studentId}?lang=${lang}`),
  )
}

export async function myProgress(): Promise<StudentDashboard> {
  const lang = i18n.global.locale.value
  return toDashboard(await api.get<DashboardPayload>(`/coaching/me/progress?lang=${lang}`))
}

/** Push local sessions (and any known attributes) and return how many were stored. */
export async function syncProgress(
  sessions: SessionSync[],
  profile: ProfileSync = {},
): Promise<number> {
  const body = await api.post<{ synced: number }>('/coaching/me/progress', {
    sessions: sessions.map((session) => ({
      exercise_id: session.exerciseId,
      logged_on: session.loggedOn,
      weight_kg: session.weightKg,
      reps: session.reps,
      completed: session.completed,
    })),
    weight_kg: profile.weightKg,
    height_cm: profile.heightCm,
    age: profile.age,
    goal: profile.goal,
    level: profile.level,
  })
  return body.synced
}
