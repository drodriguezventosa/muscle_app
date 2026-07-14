import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { INCREMENT_KG, useProgressStore } from '@/stores/progress'

describe('progress store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.localStorage?.clear()
  })

  it('records sessions and tracks last and best', () => {
    const s = useProgressStore()
    s.log(1, 'Squat', 60, true, '2026-07-01')
    s.log(1, 'Squat', 65, true, '2026-07-08')
    expect(s.history(1)).toHaveLength(2)
    expect(s.last(1)?.weight).toBe(65)
    expect(s.best(1)).toBe(65)
    expect(s.isRecord(1, 70)).toBe(true)
    expect(s.isRecord(1, 65)).toBe(false)
  })

  it('suggests progressive overload only after a completed session', () => {
    const s = useProgressStore()
    expect(s.suggested(1)).toBeNull()
    s.log(1, 'Squat', 60, true)
    expect(s.suggested(1)).toBe(60 + INCREMENT_KG)
    s.log(1, 'Squat', 60, false) // failed to complete → repeat the weight
    expect(s.suggested(1)).toBe(60)
  })

  it('persists to localStorage across store instances', () => {
    useProgressStore().log(2, 'Bench', 40, true, '2026-07-02')
    setActivePinia(createPinia()) // fresh store reads from storage
    const reloaded = useProgressStore()
    expect(reloaded.best(2)).toBe(40)
    expect(reloaded.names[2]).toBe('Bench')
  })
})
