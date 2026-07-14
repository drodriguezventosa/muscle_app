<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { SessionLog } from '@/stores/progress'
import { useProgressStore } from '@/stores/progress'

const { t } = useI18n()
const progress = useProgressStore()

// Exercises with history, most recently trained first.
const exercises = computed(() =>
  Object.keys(progress.logs)
    .map(Number)
    .filter((id) => progress.history(id).length > 0)
    .sort((a, b) => {
      const la = progress.last(a)?.date ?? ''
      const lb = progress.last(b)?.date ?? ''
      return lb.localeCompare(la)
    }),
)

// Sparkline points for a history (day-to-day weight trend).
function sparkline(history: SessionLog[]): string {
  const weights = history.map((h) => h.weight)
  const max = Math.max(...weights, 1)
  const min = Math.min(...weights)
  const range = max - min || 1
  const W = 200
  const H = 40
  const P = 4
  return history
    .map((h, i) => {
      const x = history.length === 1 ? W / 2 : P + (i / (history.length - 1)) * (W - 2 * P)
      const y = H - P - ((h.weight - min) / range) * (H - 2 * P)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

function mondayOf(dateISO: string): string {
  const d = new Date(`${dateISO}T00:00:00`)
  const offset = (d.getDay() + 6) % 7 // 0 = Monday
  d.setDate(d.getDate() - offset)
  return d.toISOString().slice(0, 10)
}

// Best weight per week, most recent 4 weeks first.
function weeks(history: SessionLog[]): { week: string; best: number }[] {
  const byWeek = new Map<string, number>()
  for (const h of history) {
    const k = mondayOf(h.date)
    byWeek.set(k, Math.max(byWeek.get(k) ?? 0, h.weight))
  }
  return [...byWeek.entries()]
    .sort((a, b) => b[0].localeCompare(a[0]))
    .slice(0, 4)
    .map(([week, best]) => ({ week, best }))
}

function fmtDay(iso: string): string {
  const [, m, d] = iso.split('-')
  return `${d}/${m}`
}
</script>

<template>
  <section class="progress">
    <header class="intro animate-in">
      <p class="eyebrow">{{ t('progress.eyebrow') }}</p>
      <h1>
        <span class="gradient-text">{{ t('progress.titleHighlight') }}</span>
        {{ t('progress.titleRest') }}
      </h1>
      <p class="lead">{{ t('progress.lead') }}</p>
    </header>

    <p v-if="exercises.length === 0" class="empty glass animate-in">{{ t('progress.empty') }}</p>

    <ul v-else class="cards">
      <li v-for="id in exercises" :key="id" class="card glass animate-in">
        <div class="card-head">
          <h2 class="name">{{ progress.names[id] }}</h2>
          <span class="record">{{ t('progress.best') }} {{ progress.best(id) }} kg ⭐</span>
        </div>
        <p class="meta">
          {{ progress.history(id).length }} {{ t('progress.sessions') }} ·
          {{ t('progress.latest') }} {{ progress.last(id)?.weight }} kg ({{
            fmtDay(progress.last(id)!.date)
          }})
        </p>

        <svg class="spark" viewBox="0 0 200 40" preserveAspectRatio="none" aria-hidden="true">
          <polyline :points="sparkline(progress.history(id))" />
        </svg>

        <div class="weeks">
          <span class="weeks-label">{{ t('progress.weeks') }}</span>
          <span v-for="w in weeks(progress.history(id))" :key="w.week" class="week">
            {{ fmtDay(w.week) }}: {{ w.best }} kg
          </span>
        </div>
      </li>
    </ul>

    <button v-if="exercises.length" type="button" class="clear" @click="progress.clearAll()">
      {{ t('progress.clear') }}
    </button>
  </section>
</template>

<style scoped>
.progress {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}
.intro {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.25em;
  font-size: 0.72rem;
  color: var(--color-accent);
}
h1 {
  margin: 0;
  font-size: clamp(1.9rem, 5vw, 3rem);
  font-weight: 800;
  line-height: 1.1;
}
.lead {
  margin: 0;
  color: var(--color-muted);
  max-width: 55ch;
}
.empty {
  margin: 0;
  padding: var(--space-lg);
  color: var(--color-muted);
}
.cards {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-md);
}
@media (min-width: 720px) {
  .cards {
    grid-template-columns: 1fr 1fr;
  }
}
.card {
  padding: var(--space-md) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-sm);
}
.name {
  margin: 0;
  font-size: 1.05rem;
}
.record {
  font-size: 0.78rem;
  color: var(--color-accent);
  white-space: nowrap;
}
.meta {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.85rem;
}
.spark {
  width: 100%;
  height: 44px;
  margin: var(--space-xs) 0;
}
.spark polyline {
  fill: none;
  stroke: url(#g);
  stroke: var(--color-accent);
  stroke-width: 2;
  vector-effect: non-scaling-stroke;
}
.weeks {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.78rem;
}
.weeks-label {
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.68rem;
}
.week {
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-accent-soft);
  color: var(--color-accent);
}
.clear {
  align-self: flex-start;
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-muted);
  font: inherit;
  font-size: 0.82rem;
  cursor: pointer;
}
.clear:hover {
  color: var(--color-text);
  border-color: var(--color-accent);
}
</style>
