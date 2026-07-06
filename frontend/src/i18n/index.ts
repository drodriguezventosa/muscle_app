import { createI18n } from 'vue-i18n'

import en from './locales/en'
import es from './locales/es'

export const SUPPORTED_LOCALES = ['es', 'en'] as const
export type Locale = (typeof SUPPORTED_LOCALES)[number]

export const LOCALE_FLAGS: Record<Locale, string> = { es: '🇪🇸', en: '🇬🇧' }
export const LOCALE_NAMES: Record<Locale, string> = { es: 'Español', en: 'English' }

const STORAGE_KEY = 'muscleapp:locale'

// Storage/navigator may be unavailable (tests, SSR); access them defensively.
function detectLocale(): Locale {
  try {
    const stored = globalThis.localStorage?.getItem(STORAGE_KEY)
    if (stored === 'es' || stored === 'en') return stored
  } catch {
    // ignore storage access errors
  }
  // Default to the browser language, falling back to English.
  return globalThis.navigator?.language?.toLowerCase().startsWith('es') ? 'es' : 'en'
}

export const i18n = createI18n({
  legacy: false,
  locale: detectLocale(),
  fallbackLocale: 'en',
  messages: { es, en },
})

if (typeof document !== 'undefined') {
  document.documentElement.lang = i18n.global.locale.value
}

export function setLocale(locale: Locale): void {
  i18n.global.locale.value = locale
  try {
    globalThis.localStorage?.setItem(STORAGE_KEY, locale)
  } catch {
    // ignore storage access errors
  }
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale
  }
}
