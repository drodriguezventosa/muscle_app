<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useThemeStore } from '@/stores/theme'

const { t } = useI18n()
const theme = useThemeStore()

const label = computed(() => (theme.theme === 'dark' ? t('theme.toLight') : t('theme.toDark')))
</script>

<template>
  <button type="button" class="toggle" :aria-label="label" :title="label" @click="theme.toggle()">
    <span aria-hidden="true">{{ theme.theme === 'dark' ? '☀️' : '🌙' }}</span>
  </button>
</template>

<style scoped>
.toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  background: var(--color-surface);
  font-size: 1rem;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}
.toggle:hover {
  border-color: var(--color-accent);
  box-shadow: var(--glow);
}
</style>
