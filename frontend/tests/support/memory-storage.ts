/**
 * A minimal in-memory Storage for tests that touch persisted state.
 *
 * Stub it per test instead of relying on the environment: CI runs jsdom's
 * localStorage (shared across tests in a file, so state leaks between them),
 * while Node 26 locally exposes its own inert global that shadows jsdom's.
 * Stubbing makes both behave the same and starts every test empty.
 */
export function memoryStorage(): Storage {
  const entries = new Map<string, string>()
  return {
    get length() {
      return entries.size
    },
    key: (index: number) => [...entries.keys()][index] ?? null,
    getItem: (key: string) => entries.get(key) ?? null,
    setItem: (key: string, value: string) => void entries.set(key, String(value)),
    removeItem: (key: string) => void entries.delete(key),
    clear: () => entries.clear(),
  }
}
