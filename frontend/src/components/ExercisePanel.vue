<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { Exercise } from '@/api/types'

defineProps<{
  muscleName: string | null
  exercises: Exercise[]
  loading: boolean
  error: string | null
}>()

const { t } = useI18n()
</script>

<template>
  <section class="panel" aria-live="polite">
    <h2 v-if="muscleName" class="title">{{ muscleName }}</h2>
    <p v-else class="hint">{{ t('panel.prompt') }}</p>

    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <p v-else-if="loading" class="hint">{{ t('panel.loading') }}</p>
    <p v-else-if="muscleName && exercises.length === 0" class="hint">
      {{ t('panel.empty') }}
    </p>

    <ul v-if="exercises.length" class="list">
      <li v-for="exercise in exercises" :key="exercise.id" class="card">
        <div class="card-head">
          <h3 class="card-title">{{ exercise.name }}</h3>
          <div class="badges">
            <span class="badge">{{ t(`equipment.${exercise.equipment}`) }}</span>
            <span class="badge badge-soft">{{ t(`difficulty.${exercise.difficulty}`) }}</span>
          </div>
        </div>
        <p class="card-desc">{{ exercise.description }}</p>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.title {
  margin: 0;
  font-size: 1.4rem;
}
.hint {
  color: var(--color-muted);
  margin: 0;
}
.error {
  color: var(--color-danger);
  margin: 0;
}
.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.card {
  position: relative;
  background: var(--color-surface-strong);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-md);
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
  animation: fade-in-up 0.4s ease both;
}
/* Gradient hairline that lights up on hover. */
.card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: var(--gradient);
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.2s ease;
}
.card:hover {
  transform: translateY(-3px);
  box-shadow: var(--glow);
}
.card:hover::before {
  opacity: 1;
}
.card:nth-child(2) {
  animation-delay: 0.05s;
}
.card:nth-child(3) {
  animation-delay: 0.1s;
}
.card:nth-child(4) {
  animation-delay: 0.15s;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-sm);
  flex-wrap: wrap;
}
.card-title {
  margin: 0;
  font-size: 1.05rem;
}
.badges {
  display: flex;
  gap: var(--space-xs);
}
.badge {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--gradient);
  color: #06121a;
  font-weight: 700;
}
.badge-soft {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}
.card-desc {
  margin: var(--space-sm) 0 0;
  color: var(--color-muted);
}
</style>
