<script setup lang="ts">
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { isoDay, startOfWeek, todayISO } from '@/utils/dates'

/** A dot under a day: one per scheduled exercise, coloured by how it went. */
export type DayMark = 'pending' | 'done' | 'partial' | 'missed'

/**
 * A week strip with the selected day expanded below it.
 *
 * Seven columns of exercise cards only work on a wide screen, and even there
 * they crowd; a strip of seven small day buttons plus one full-width day reads
 * the same on a phone, on a tablet and inside a panel. The week stays visible
 * at a glance through the dots.
 */
const props = defineProps<{
  weekStart: string
  selectedDay: string
  /** Statuses per ISO day, drawn as dots under each day button. */
  marks?: Record<string, DayMark[]>
  busy?: boolean
}>()
const emit = defineEmits<{ 'update:weekStart': [string]; 'update:selectedDay': [string] }>()

const { t, locale } = useI18n()

const MAX_DOTS = 4

const days = computed(() =>
  Array.from({ length: 7 }, (_, offset) => {
    const day = new Date(`${props.weekStart}T00:00:00`)
    day.setDate(day.getDate() + offset)
    const iso = isoDay(day)
    const marks = props.marks?.[iso] ?? []
    return {
      iso,
      weekday: day.toLocaleDateString(locale.value, { weekday: 'short' }).slice(0, 3),
      number: day.getDate(),
      isToday: iso === todayISO(),
      marks: marks.slice(0, MAX_DOTS),
      extra: Math.max(0, marks.length - MAX_DOTS),
      total: marks.length,
    }
  }),
)

const weekLabel = computed(() => {
  const from = new Date(`${props.weekStart}T00:00:00`)
  const to = new Date(`${days.value[6].iso}T00:00:00`)
  const month = (date: Date) => date.toLocaleDateString(locale.value, { month: 'short' })
  return from.getMonth() === to.getMonth()
    ? `${from.getDate()}–${to.getDate()} ${month(to)}`
    : `${from.getDate()} ${month(from)} – ${to.getDate()} ${month(to)}`
})

const dayLabel = computed(() =>
  new Date(`${props.selectedDay}T00:00:00`).toLocaleDateString(locale.value, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }),
)

function shift(weeks: number): void {
  const day = new Date(`${props.weekStart}T00:00:00`)
  day.setDate(day.getDate() + weeks * 7)
  emit('update:weekStart', isoDay(day))
}

function goToToday(): void {
  emit('update:weekStart', startOfWeek(todayISO()))
  emit('update:selectedDay', todayISO())
}

// Changing week keeps a day selected: today when it is in view, else the Monday.
watch(
  () => props.weekStart,
  (week) => {
    if (days.value.some((day) => day.iso === props.selectedDay)) return
    const today = todayISO()
    emit('update:selectedDay', startOfWeek(today) === week ? today : week)
  },
)
</script>

<template>
  <div class="calendar">
    <header class="week-head">
      <button type="button" class="nav" :aria-label="t('plan.previousWeek')" @click="shift(-1)">
        ‹
      </button>
      <strong class="week-label">{{ weekLabel }}</strong>
      <button type="button" class="nav" :aria-label="t('plan.nextWeek')" @click="shift(1)">
        ›
      </button>
      <button
        type="button"
        class="today-btn"
        :disabled="weekStart === startOfWeek(todayISO()) && selectedDay === todayISO()"
        @click="goToToday"
      >
        {{ t('plan.today') }}
      </button>
    </header>

    <ol class="strip" :class="{ busy }">
      <li v-for="day in days" :key="day.iso">
        <button
          type="button"
          class="day"
          :class="{ on: day.iso === selectedDay, today: day.isToday }"
          :aria-pressed="day.iso === selectedDay"
          :aria-label="t('plan.dayLabel', { n: day.total })"
          @click="emit('update:selectedDay', day.iso)"
        >
          <span class="weekday">{{ day.weekday }}</span>
          <span class="number">{{ day.number }}</span>
          <span class="dots" aria-hidden="true">
            <span v-for="(mark, index) in day.marks" :key="index" class="dot" :class="mark"></span>
            <span v-if="day.extra" class="extra">+{{ day.extra }}</span>
          </span>
        </button>
      </li>
    </ol>

    <section class="day-detail" :class="{ busy }" aria-live="polite">
      <h4 class="day-title">{{ dayLabel }}</h4>
      <slot :day="selectedDay"></slot>
    </section>
  </div>
</template>

<style scoped>
.calendar {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.week-head {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}
.nav {
  width: 32px;
  height: 32px;
  flex: none;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  background: transparent;
  color: var(--color-text);
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
}
.nav:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}
.week-label {
  min-width: 9ch;
  text-align: center;
  font-size: 0.92rem;
}
.today-btn {
  margin-left: auto;
  padding: 5px 12px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-muted);
  font: inherit;
  font-size: 0.78rem;
  cursor: pointer;
}
.today-btn:not(:disabled):hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}
.today-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
/* Seven equal day buttons: the only row that must fit on a phone, and it does —
   everything else lives in the day below, at full width. */
.strip {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
  transition: opacity 0.18s ease;
}
.strip.busy {
  opacity: 0.5;
}
.day {
  width: 100%;
  min-height: 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 2px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background 0.15s ease;
}
.day:hover {
  border-color: var(--color-accent-soft);
}
.day.today .number {
  color: var(--color-accent);
}
.day.on {
  border-color: var(--color-accent);
  background: var(--color-accent-soft);
}
.weekday {
  text-transform: uppercase;
  font-size: 0.6rem;
  letter-spacing: 0.04em;
  color: var(--color-muted);
  white-space: nowrap;
}
.number {
  font-weight: 700;
  font-size: 1rem;
  line-height: 1.1;
}
.dots {
  display: flex;
  align-items: center;
  gap: 2px;
  min-height: 8px;
}
.dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--color-muted);
}
.dot.done {
  background: var(--color-accent);
}
.dot.partial {
  background: #eda100;
}
.dot.missed {
  background: var(--color-danger);
}
.extra {
  font-size: 0.55rem;
  color: var(--color-muted);
}
.day-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  transition: opacity 0.18s ease;
}
.day-detail.busy {
  opacity: 0.5;
}
.day-title {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  text-transform: capitalize;
}
@media (prefers-reduced-motion: reduce) {
  .strip,
  .day,
  .day-detail {
    transition: none;
  }
}
</style>
