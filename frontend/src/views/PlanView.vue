<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { myPlan, reportPlanItem, type PlanItem } from '@/api/plan'
import HealthDisclaimer from '@/components/HealthDisclaimer.vue'
import WeekCalendar, { type DayMark } from '@/components/WeekCalendar.vue'
import { addDays, startOfWeek, todayISO } from '@/utils/dates'

// The student's side of the coaching area: what the trainer scheduled, and a
// place to say what was actually lifted. Reporting less than the target is
// expected — it is how the trainer learns the plan was too ambitious.
const { t } = useI18n()

const weekStart = ref(startOfWeek(todayISO()))
const selectedDay = ref(todayISO())
const items = ref<PlanItem[]>([])
const loading = ref(true)
const error = ref(false)
/** Which item has its report form open, and what is typed in it. */
const reporting = ref<number | null>(null)
const draft = reactive<{ weight: number | null; reps: number | null; sets: number | null }>({
  weight: null,
  reps: null,
  sets: null,
})
const saving = ref(false)

let pendingRequest = 0

async function load(): Promise<void> {
  const request = ++pendingRequest
  loading.value = true
  try {
    const week = await myPlan(weekStart.value, addDays(weekStart.value, 6))
    if (request !== pendingRequest) return
    items.value = week
    error.value = false
  } catch {
    if (request === pendingRequest) error.value = true
  } finally {
    if (request === pendingRequest) loading.value = false
  }
}

onMounted(load)
watch(weekStart, load)

/** One dot per scheduled exercise, so the week reads at a glance. */
const marks = computed<Record<string, DayMark[]>>(() => {
  const byDay: Record<string, DayMark[]> = {}
  for (const item of items.value) {
    ;(byDay[item.scheduledOn] ??= []).push(item.status)
  }
  return byDay
})

const dayItems = computed(() =>
  items.value.filter((item) => item.scheduledOn === selectedDay.value),
)
const done = computed(() => items.value.filter((item) => item.status === 'done').length)
const pending = computed(() => items.value.filter((item) => item.status === 'pending').length)

function openReport(item: PlanItem): void {
  reporting.value = item.id
  // Pre-filled with the target: hitting it is one tap, adjusting is a nudge.
  draft.weight = item.doneWeightKg || item.targetWeightKg || null
  draft.reps = item.doneReps ?? item.targetReps
  draft.sets = item.doneSets ?? item.targetSets
}

async function save(item: PlanItem): Promise<void> {
  saving.value = true
  try {
    const updated = await reportPlanItem(
      item.id,
      draft.weight ?? 0,
      draft.reps ?? item.targetReps,
      draft.sets ?? item.targetSets,
    )
    items.value = items.value.map((entry) => (entry.id === updated.id ? updated : entry))
    reporting.value = null
  } catch {
    error.value = true
  } finally {
    saving.value = false
  }
}

function targetLabel(item: PlanItem): string {
  // No target load means bodyweight work: "0 kg" would read as nonsense.
  const load = item.targetWeightKg ? `${item.targetWeightKg} kg` : t('plan.openLoad')
  return `${item.targetSets} × ${item.targetReps} · ${load}`
}

/** What the student reported, phrased so bodyweight work never says "0 kg". */
function doneLabel(item: PlanItem): string {
  const done = {
    sets: item.doneSets ?? item.targetSets,
    reps: item.doneReps,
    kg: item.doneWeightKg,
  }
  return item.doneWeightKg ? t('plan.lifted', done) : t('plan.liftedBodyweight', done)
}
</script>

<template>
  <section class="plan">
    <header class="intro animate-in">
      <p class="eyebrow">{{ t('plan.eyebrow') }}</p>
      <h1>
        <span class="gradient-text">{{ t('plan.titleHighlight') }}</span>
        {{ t('plan.titleRest') }}
      </h1>
      <p class="lead">{{ t('plan.lead') }}</p>
      <HealthDisclaimer />
    </header>

    <p v-if="error" class="hint error" role="alert">{{ t('plan.error') }}</p>

    <div class="glass panel animate-in" style="animation-delay: 0.06s">
      <p class="summary">
        <span class="count">{{ done }}/{{ items.length }}</span>
        {{ t('plan.doneThisWeek') }}
        <span v-if="pending" class="pending-note">· {{ t('plan.pendingCount', pending) }}</span>
      </p>

      <WeekCalendar
        v-model:week-start="weekStart"
        v-model:selected-day="selectedDay"
        :marks="marks"
        :busy="loading"
      >
        <ul v-if="dayItems.length" class="items">
          <li v-for="item in dayItems" :key="item.id" class="item" :class="item.status">
            <div class="row">
              <div class="what">
                <p class="ex-name">{{ item.exerciseName }}</p>
                <p class="target">
                  {{ targetLabel(item) }}
                  <span v-if="item.doneWeightKg !== null" class="lifted">
                    ·
                    {{ doneLabel(item) }}
                  </span>
                </p>
                <p v-if="item.notes" class="notes">“{{ item.notes }}”</p>
              </div>
              <span class="badge" :class="item.status">{{ t(`plan.status.${item.status}`) }}</span>
              <button
                v-if="reporting !== item.id"
                type="button"
                class="report-btn"
                @click="openReport(item)"
              >
                {{ item.doneWeightKg === null ? t('plan.report') : t('plan.edit') }}
              </button>
            </div>

            <form v-if="reporting === item.id" class="report" @submit.prevent="save(item)">
              <!-- Bodyweight work has no load to report, so the field is not
                   shown at all rather than asking for a zero. -->
              <label v-if="item.targetWeightKg !== null" class="field">
                <span class="field-label">{{ t('plan.weightLifted') }}</span>
                <input v-model.number="draft.weight" type="number" min="0" step="0.5" />
              </label>
              <label class="field">
                <span class="field-label">{{ t('plan.repsDone') }}</span>
                <input v-model.number="draft.reps" type="number" min="0" max="100" />
              </label>
              <label class="field">
                <span class="field-label">{{ t('plan.setsDone') }}</span>
                <input v-model.number="draft.sets" type="number" min="0" max="20" />
              </label>
              <div class="actions">
                <button type="submit" class="primary" :disabled="saving">
                  {{ saving ? t('plan.saving') : t('plan.save') }}
                </button>
                <button type="button" class="ghost" @click="reporting = null">
                  {{ t('plan.cancel') }}
                </button>
              </div>
            </form>
          </li>
        </ul>
        <p v-else-if="!loading" class="empty">{{ t('plan.restDay') }}</p>
      </WeekCalendar>

      <p v-if="!items.length && !loading" class="hint">{{ t('plan.noPlan') }}</p>
    </div>
  </section>
</template>

<style scoped>
.plan {
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
.panel {
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.summary {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.88rem;
}
.count {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--color-text);
  margin-right: 4px;
}
.pending-note {
  color: var(--color-accent);
}
.items {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.item {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-strong);
  /* The status is a stripe as well as a word: colour never carries it alone. */
  border-left: 3px solid var(--color-muted);
}
.item.done {
  border-left-color: var(--color-accent);
}
.item.partial {
  border-left-color: #eda100;
}
.item.missed {
  border-left-color: var(--color-danger);
}
.row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}
.what {
  flex: 1 1 12rem;
  min-width: 0;
}
.ex-name {
  margin: 0;
  font-weight: 600;
}
.target,
.notes {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.8rem;
}
.notes {
  font-style: italic;
}
.lifted {
  color: var(--color-text);
}
.badge {
  flex: none;
  padding: 2px 10px;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  font-size: 0.72rem;
  color: var(--color-muted);
}
.badge.done {
  border-color: transparent;
  background: var(--color-accent-soft);
  color: var(--color-accent);
}
.badge.partial {
  border-color: transparent;
  background: rgba(237, 161, 0, 0.16);
  color: #eda100;
}
.badge.missed {
  border-color: transparent;
  background: color-mix(in srgb, var(--color-danger) 15%, transparent);
  color: var(--color-danger);
}
.report-btn {
  flex: none;
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-text);
  font: inherit;
  font-size: 0.8rem;
  cursor: pointer;
}
.report-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}
.report {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.field-label {
  font-size: 0.7rem;
  color: var(--color-muted);
}
.field input {
  width: 7rem;
  padding: 8px 10px;
}
.check {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 8px;
  font-size: 0.82rem;
  cursor: pointer;
}
.check input {
  position: absolute;
  opacity: 0;
  width: 1px;
  height: 1px;
}
.box {
  flex: none;
  display: inline-grid;
  place-items: center;
  width: 18px;
  height: 18px;
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-surface);
}
.box::after {
  content: '';
  width: 5px;
  height: 9px;
  border: solid transparent;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg) translate(-1px, -1px);
}
.check input:checked + .box {
  background: var(--gradient);
  border-color: transparent;
}
.check input:checked + .box::after {
  border-color: #06121a;
}
.check input:focus-visible + .box {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
.actions {
  display: flex;
  gap: var(--space-xs);
  padding-bottom: 4px;
}
.primary,
.ghost {
  padding: 8px 16px;
  border-radius: 999px;
  font: inherit;
  font-size: 0.82rem;
  cursor: pointer;
}
.primary {
  border: none;
  background: var(--gradient);
  color: #06121a;
  font-weight: 700;
}
.primary:disabled {
  opacity: 0.7;
  cursor: default;
}
.ghost {
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-muted);
}
.empty,
.hint {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.85rem;
}
.hint.error {
  color: var(--color-danger);
}
</style>
