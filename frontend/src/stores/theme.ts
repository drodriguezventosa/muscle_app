import { defineStore } from 'pinia'
import { ref } from 'vue'

// Light/dark theme, persisted in localStorage. The initial value is applied
// before paint by an inline script in index.html; this store reads it back and
// lets the UI toggle it.

export type Theme = 'dark' | 'light'
const KEY = 'muscleapp:theme'

function initial(): Theme {
  const attr = globalThis.document?.documentElement.getAttribute('data-theme')
  if (attr === 'light' || attr === 'dark') return attr
  try {
    const stored = globalThis.localStorage?.getItem(KEY)
    if (stored === 'light' || stored === 'dark') return stored
  } catch {
    // ignore
  }
  return 'dark'
}

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<Theme>(initial())

  function apply(): void {
    globalThis.document?.documentElement.setAttribute('data-theme', theme.value)
    try {
      globalThis.localStorage?.setItem(KEY, theme.value)
    } catch {
      // ignore
    }
  }

  function toggle(): void {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    apply()
  }

  apply()
  return { theme, toggle }
})
