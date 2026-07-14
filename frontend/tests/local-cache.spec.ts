import { beforeEach, describe, expect, it } from 'vitest'

import { readCache, writeCache } from '@/lib/localCache'

// The test env doesn't provide a working localStorage, so install a Map-backed
// stub — makes these tests deterministic regardless of the runner.
function installLocalStorage(): void {
  const store = new Map<string, string>()
  const mock: Storage = {
    getItem: (k) => (store.has(k) ? (store.get(k) as string) : null),
    setItem: (k, v) => void store.set(k, String(v)),
    removeItem: (k) => void store.delete(k),
    clear: () => store.clear(),
    key: (i) => [...store.keys()][i] ?? null,
    get length() {
      return store.size
    },
  }
  Object.defineProperty(globalThis, 'localStorage', {
    value: mock,
    configurable: true,
    writable: true,
  })
}

describe('localCache (stale-while-revalidate helper)', () => {
  beforeEach(() => {
    installLocalStorage()
  })

  it('round-trips a value under a versioned key', () => {
    expect(readCache('muscles:es')).toBeNull()
    writeCache('muscles:es', [{ svgId: 'chest' }])
    expect(readCache<Array<{ svgId: string }>>('muscles:es')).toEqual([{ svgId: 'chest' }])
  })

  it('returns null on missing or malformed entries instead of throwing', () => {
    expect(readCache('missing')).toBeNull()
    globalThis.localStorage.setItem('muscleapp:cache:v1:broken', '{not json')
    expect(readCache('broken')).toBeNull()
  })
})
