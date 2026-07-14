import { defineStore } from 'pinia'
import { ref } from 'vue'

// Demo-only: which exercises a trainer has assigned to each student. Persisted in
// localStorage so the mockup keeps state; no backend, no accounts (see ADR-0006).

const KEY = 'muscleapp:coach-assignments'

function loadState(): Record<number, string[]> {
  try {
    const raw = globalThis.localStorage?.getItem(KEY)
    if (raw) return JSON.parse(raw) as Record<number, string[]>
  } catch {
    // ignore
  }
  return {}
}

export const useCoachingStore = defineStore('coaching', () => {
  const assignments = ref<Record<number, string[]>>(loadState())

  function persist(): void {
    globalThis.localStorage?.setItem(KEY, JSON.stringify(assignments.value))
  }

  function assigned(studentId: number): string[] {
    return assignments.value[studentId] ?? []
  }

  function toggle(studentId: number, exercise: string): void {
    const current = assigned(studentId)
    const next = current.includes(exercise)
      ? current.filter((e) => e !== exercise)
      : [...current, exercise]
    assignments.value = { ...assignments.value, [studentId]: next }
    persist()
  }

  return { assignments, assigned, toggle }
})
