import { defineStore } from 'pinia'
import { ref } from 'vue'

import { syncProgress, type ProfileSync, type SessionSync } from '@/api/coaching'
import { useAuthStore } from '@/stores/auth'

// Workout progress stays offline-first (ADR-0011): logs live in the browser's
// localStorage, keyed by the catalog exercise id so history survives routine
// regeneration. Signing in adds a mirror — `sync()` pushes the same history to
// the server so a trainer can follow it — but never a dependency: everything
// here keeps working while signed out or offline.

export interface SessionLog {
  date: string // YYYY-MM-DD
  weight: number // kg (0 = bodyweight)
  completed: boolean // hit all sets at the target reps
  reps?: number // target reps of the session, needed to estimate a 1RM
}

interface Persisted {
  logs: Record<number, SessionLog[]>
  names: Record<number, string>
}

const KEY = 'muscleapp:progress'
// Progressive-overload step suggested after a fully-completed session.
export const INCREMENT_KG = 2.5

function loadState(): Persisted {
  try {
    const raw = globalThis.localStorage?.getItem(KEY)
    if (raw) return JSON.parse(raw) as Persisted
  } catch {
    // ignore corrupt/unavailable storage
  }
  return { logs: {}, names: {} }
}

function todayISO(): string {
  // The user's own day, not UTC: east of Greenwich, a session logged after
  // midnight would otherwise be filed as yesterday's.
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10)
}

export const useProgressStore = defineStore('progress', () => {
  const initial = loadState()
  const logs = ref<Record<number, SessionLog[]>>(initial.logs)
  const names = ref<Record<number, string>>(initial.names)

  function persist(): void {
    globalThis.localStorage?.setItem(KEY, JSON.stringify({ logs: logs.value, names: names.value }))
  }

  function history(exerciseId: number): SessionLog[] {
    return logs.value[exerciseId] ?? []
  }

  function last(exerciseId: number): SessionLog | null {
    const h = history(exerciseId)
    return h.length ? h[h.length - 1] : null
  }

  function best(exerciseId: number): number {
    return history(exerciseId).reduce((max, s) => Math.max(max, s.weight), 0)
  }

  // Suggested weight for the next session: bump after a completed one, else repeat.
  function suggested(exerciseId: number): number | null {
    const l = last(exerciseId)
    if (!l) return null
    return l.completed ? l.weight + INCREMENT_KG : l.weight
  }

  function isRecord(exerciseId: number, weight: number): boolean {
    return weight > 0 && weight > best(exerciseId)
  }

  function log(
    exerciseId: number,
    name: string,
    weight: number,
    completed: boolean,
    reps?: number,
    date: string = todayISO(),
  ): void {
    const entries = [...history(exerciseId), { date, weight, completed, reps }]
    entries.sort((a, b) => a.date.localeCompare(b.date))
    logs.value = { ...logs.value, [exerciseId]: entries }
    names.value = { ...names.value, [exerciseId]: name }
    persist()
  }

  /** Every stored session, flattened into what the API expects. */
  function pending(): SessionSync[] {
    return Object.entries(logs.value).flatMap(([exerciseId, entries]) =>
      entries.map((entry) => ({
        exerciseId: Number(exerciseId),
        loggedOn: entry.date,
        weightKg: entry.weight,
        reps: entry.reps ?? 0,
        completed: entry.completed,
      })),
    )
  }

  /**
   * Mirror the local history onto the server, best effort.
   *
   * Only for signed-in students: a trainer has no progress of their own, and a
   * visitor has no account to attach it to. Failures are swallowed on purpose —
   * localStorage is the source of truth, so a network hiccup must not surface
   * as an error in the middle of a workout.
   */
  async function sync(profile: ProfileSync = {}): Promise<void> {
    const auth = useAuthStore()
    if (!auth.isSignedIn || auth.isTrainer) return
    try {
      await syncProgress(pending(), profile)
    } catch {
      // Retried on the next logged session or sign-in.
    }
  }

  function clearAll(): void {
    logs.value = {}
    names.value = {}
    persist()
  }

  return { logs, names, history, last, best, suggested, isRecord, log, pending, sync, clearAll }
})
