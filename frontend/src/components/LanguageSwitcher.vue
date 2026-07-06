<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { LOCALE_FLAGS, LOCALE_NAMES, SUPPORTED_LOCALES, setLocale, type Locale } from '@/i18n'

const { locale, t } = useI18n({ useScope: 'global' })
const open = ref(false)
const root = ref<HTMLElement | null>(null)

function choose(next: Locale): void {
  setLocale(next)
  open.value = false
}

// Close when clicking outside (focusout would fire before the option click).
function onDocumentClick(event: MouseEvent): void {
  if (open.value && root.value && !root.value.contains(event.target as Node)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))
</script>

<template>
  <div ref="root" class="switcher">
    <button
      class="current"
      type="button"
      :aria-label="t('language')"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="open = !open"
    >
      <span class="flag">{{ LOCALE_FLAGS[locale as Locale] }}</span>
      <span class="code">{{ (locale as string).toUpperCase() }}</span>
    </button>

    <ul v-if="open" class="menu" role="listbox">
      <li v-for="option in SUPPORTED_LOCALES" :key="option">
        <button
          type="button"
          role="option"
          :aria-selected="option === locale"
          :class="{ active: option === locale }"
          @click="choose(option)"
        >
          <span class="flag">{{ LOCALE_FLAGS[option] }}</span>
          {{ LOCALE_NAMES[option] }}
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.switcher {
  position: relative;
}
.current {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  backdrop-filter: blur(var(--blur));
}
.current:hover {
  border-color: var(--color-accent);
  box-shadow: var(--glow);
}
.flag {
  font-size: 1.1rem;
  line-height: 1;
}
.code {
  font-size: 0.8rem;
  letter-spacing: 0.05em;
}
.menu {
  position: absolute;
  right: 0;
  top: calc(100% + 0.5rem);
  list-style: none;
  margin: 0;
  padding: var(--space-xs);
  min-width: 160px;
  background: var(--color-bg-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
  z-index: 30;
  animation: fade-in-up 0.15s ease both;
}
.menu button {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-sm);
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.menu button:hover {
  background: var(--color-surface-strong);
}
.menu button.active {
  color: var(--color-accent);
}
</style>
