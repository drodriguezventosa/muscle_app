// Tiny localStorage cache for a stale-while-revalidate strategy: paint cached
// data instantly, then refresh from the network. Keeps the explorer usable and
// fast even if the backend is slow or waking from a cold start. Versioned keys
// so a schema change invalidates old entries. Best-effort — never throws.

const PREFIX = 'muscleapp:cache:v1:'

export function readCache<T>(key: string): T | null {
  try {
    const raw = globalThis.localStorage?.getItem(PREFIX + key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}

export function writeCache<T>(key: string, value: T): void {
  try {
    globalThis.localStorage?.setItem(PREFIX + key, JSON.stringify(value))
  } catch {
    // storage full/unavailable — caching is best-effort
  }
}
