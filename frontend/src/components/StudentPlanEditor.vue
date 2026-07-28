<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { searchExercises, type ExerciseOption } from '@/api/explorer'
import { scheduleExercise, studentPlan, unscheduleExercise, type PlanItem } from '@/api/plan'
import WeekCalendar, { type DayMark } from '@/components/WeekCalendar.vue'
import { addDays, startOfWeek, todayISO } from '@/utils/dates'

/** The trainer's side of the calendar: write the week, see what came back. */
const props = defineProps<{ studentId: number }>()

const { t, locale } = useI18n()

const weekStart = ref(startOfWeek(todayISO()))
const selectedDay = ref(todayISO())
const items = ref<PlanItem[]>([])
const loading = ref(false)
const error = ref(false)

/** Open only while adding an exercise to the selected day. */
const composing = ref(false)
const draft = reactive({
  exercise: null as ExerciseOption | null,
  sets: 3,
  reps: 10,
  weight: null as number | null,
})
const query = ref('')
const queryInput = ref<HTMLInputElement | null>(null)
const results = ref<ExerciseOption[]>([])
const saving = ref(false)

let pendingRequest = 0

async function load(): Promise<void> {
  const request = ++pendingRequest
  loading.value = true
  try {
    const week = await studentPlan(props.studentId, weekStart.value, addDays(weekStart.value, 6))
    if (request !== pendingRequest) return
    items.value = week
    error.value = false
  } catch {
    if (request === pendingRequest) error.value = true
  } finally {
    if (request === pendingRequest) loading.value = false
  }
}

watch([() => props.studentId, weekStart, locale], load, { immediate: true })
// Moving to another day (or another student) closes a half-written form.
watch([() => props.studentId, selectedDay], () => {
  composing.value = false
})

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

async function openComposer(): Promise<void> {
  composing.value = true
  draft.exercise = null
  draft.sets = 3
  draft.reps = 10
  draft.weight = null
  query.value = ''
  results.value = []
  // Straight into the search box: adding an exercise is a two-key job.
  await nextTick()
  queryInput.value?.focus()
}

let searchToken = 0

async function search(): Promise<void> {
  const term = query.value.trim()
  if (term.length < 2) {
    results.value = []
    return
  }
  const token = ++searchToken
  try {
    const found = await searchExercises(term, 6)
    // Ignore an answer that arrived after a newer keystroke.
    if (token === searchToken) results.value = found
  } catch {
    if (token === searchToken) results.value = []
  }
}

function choose(option: ExerciseOption): void {
  draft.exercise = option
  query.value = option.name
  results.value = []
}

async function add(): Promise<void> {
  if (!draft.exercise) return
  saving.value = true
  try {
    const item = await scheduleExercise(props.studentId, {
      exerciseId: draft.exercise.id,
      scheduledOn: selectedDay.value,
      targetSets: draft.sets,
      targetReps: draft.reps,
      targetWeightKg: draft.weight,
    })
    // Re-scheduling the same exercise that day edits it, so replace by id.
    items.value = [...items.value.filter((entry) => entry.id !== item.id), item]
    composing.value = false
  } catch {
    error.value = true
  } finally {
    saving.value = false
  }
}

async function remove(item: PlanItem): Promise<void> {
  const previous = items.value
  items.value = items.value.filter((entry) => entry.id !== item.id)
  try {
    await unscheduleExercise(item.id)
  } catch {
    items.value = previous // put it back: the server still has it
    error.value = true
  }
}

function targetLabel(item: PlanItem): string {
  const load = item.targetWeightKg ? `${item.targetWeightKg} kg` : t('plan.openLoad')
  return `${item.targetSets} × ${item.targetReps} · ${load}`
}
</script>

<template>
  <div class="editor">
    <p v-if="error" class="hint error" role="alert">{{ t('plan.error') }}</p>

    <WeekCalendar
      v-model:week-start="weekStart"
      v-model:selected-day="selectedDay"
      :marks="marks"
      :busy="loading"
    >
      <ul v-if="dayItems.length" class="items">
        <li v-for="item in dayItems" :key="item.id" class="item" :class="item.status">
          <div class="what">
            <p class="ex-name">{{ item.exerciseName }}</p>
            <p class="target">
              {{ targetLabel(item) }}
              <span v-if="item.doneWeightKg !== null" class="lifted">
                · {{ t('plan.lifted', { kg: item.doneWeightKg }) }}
              </span>
            </p>
          </div>
          <span class="badge" :class="item.status">{{ t(`plan.status.${item.status}`) }}</span>
          <button
            type="button"
            class="remove"
            :aria-label="t('plan.remove', { name: item.exerciseName })"
            @click="remove(item)"
          >
            ✕
          </button>
        </li>
      </ul>
      <p v-else-if="!loading && !composing" class="empty">{{ t('plan.nothingScheduled') }}</p>

      <form v-if="composing" class="composer" @submit.prevent="add">
        <div class="picker">
          <label class="field grow">
            <span class="field-label">{{ t('plan.exercise') }}</span>
            <input
              ref="queryInput"
              v-model="query"
              type="search"
              :placeholder="t('plan.searchExercise')"
              autocomplete="off"
              @input="search"
            />
          </label>
          <label class="field">
            <span class="field-label">{{ t('plan.sets') }}</span>
            <input v-model.number="draft.sets" type="number" min="1" max="20" />
          </label>
          <label class="field">
            <span class="field-label">{{ t('plan.reps') }}</span>
            <input v-model.number="draft.reps" type="number" min="1" max="100" />
          </label>
          <label class="field">
            <span class="field-label">{{ t('plan.kg') }}</span>
            <input v-model.number="draft.weight" type="number" min="0" step="0.5" />
          </label>
        </div>
        <ul v-if="results.length" class="results">
          <li v-for="option in results" :key="option.id">
            <button type="button" @click="choose(option)">{{ option.name }}</button>
          </li>
        </ul>
        <div class="actions">
          <button type="submit" class="primary" :disabled="!draft.exercise || saving">
            {{ saving ? t('plan.saving') : t('plan.save') }}
          </button>
          <button type="button" class="ghost" @click="composing = false">
            {{ t('plan.cancel') }}
          </button>
        </div>
      </form>
      <button v-else type="button" class="add" @click="openComposer">
        + {{ t('plan.addExercise') }}
      </button>
    </WeekCalendar>
  </div>
</template>

<style scoped>
.editor {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.hint {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.8rem;
}
.hint.error {
  color: var(--color-danger);
}
.items {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 8px 10px;
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
.what {
  flex: 1;
  min-width: 0;
}
.ex-name {
  margin: 0;
  font-weight: 600;
  font-size: 0.88rem;
}
.target {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.76rem;
}
.lifted {
  color: var(--color-text);
}
.badge {
  flex: none;
  padding: 2px 9px;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  font-size: 0.68rem;
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
.remove {
  flex: none;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--color-muted);
  font-size: 0.75rem;
  cursor: pointer;
}
.remove:hover {
  background: color-mix(in srgb, var(--color-danger) 14%, transparent);
  color: var(--color-danger);
}
.add {
  align-self: flex-start;
  padding: 6px 14px;
  border: 1px dashed var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-muted);
  font: inherit;
  font-size: 0.8rem;
  cursor: pointer;
}
.add:hover {
  border-color: var(--color-accent);
  border-style: solid;
  color: var(--color-accent);
}
.composer {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-sm);
  border: 1px solid var(--color-accent-soft);
  border-radius: var(--radius-sm);
}
/* The name takes the room it needs; the three numbers stay together and wrap
   as a block on a phone. */
.picker {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.field.grow {
  flex: 1 1 12rem;
  min-width: 0;
}
.field-label {
  font-size: 0.7rem;
  color: var(--color-muted);
}
.field input {
  width: 100%;
  padding: 7px 10px;
  font-size: 0.85rem;
}
.field:not(.grow) input {
  width: 4.5rem;
}
.results {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  max-height: 180px;
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}
.results button {
  width: 100%;
  padding: 7px 10px;
  border: none;
  background: transparent;
  color: var(--color-text);
  font: inherit;
  font-size: 0.82rem;
  text-align: left;
  cursor: pointer;
}
.results button:hover {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}
.actions {
  display: flex;
  gap: var(--space-xs);
}
.primary,
.ghost {
  padding: 7px 16px;
  border-radius: 999px;
  font: inherit;
  font-size: 0.8rem;
  cursor: pointer;
}
.primary {
  border: none;
  background: var(--gradient);
  color: #06121a;
  font-weight: 700;
}
.primary:disabled {
  opacity: 0.6;
  cursor: default;
}
.ghost {
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-muted);
}
.empty {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.82rem;
}
</style>
