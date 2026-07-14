import { defineStore } from 'pinia'
import { ref } from 'vue'

// Client-side workout progress (ADR-0011): logs live in the browser's
// localStorage — no login, no backend, nothing leaves the device. Keyed by the
// catalog exercise id so history survives routine regeneration.

export interface SessionLog {
  date: string // YYYY-MM-DD
  weight: number // kg (0 = bodyweight)
  completed: boolean // hit all sets at the target reps
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
  return new Date().toISOString().slice(0, 10)
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
    date: string = todayISO(),
  ): void {
    const entries = [...history(exerciseId), { date, weight, completed }]
    entries.sort((a, b) => a.date.localeCompare(b.date))
    logs.value = { ...logs.value, [exerciseId]: entries }
    names.value = { ...names.value, [exerciseId]: name }
    persist()
  }

  function clearAll(): void {
    logs.value = {}
    names.value = {}
    persist()
  }

  return { logs, names, history, last, best, suggested, isRecord, log, clearAll }
})
