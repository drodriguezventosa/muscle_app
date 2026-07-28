<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  getStudent,
  listStudents,
  type StudentDashboard,
  type StudentSummary,
} from '@/api/coaching'
import BarChart, { type Bar } from '@/components/charts/BarChart.vue'
import LineChart, { type LineSeries } from '@/components/charts/LineChart.vue'
import ScatterChart, { type ScatterPoint } from '@/components/charts/ScatterChart.vue'
import { ASSIGNABLE } from '@/data/coaching'
import { useCoachingStore } from '@/stores/coaching'

// Trainer-only area (the route is guarded): the people this coach follows and
// how they are evolving. Every number and every mark comes from the history
// the students have logged.
const { t, locale } = useI18n()
const coaching = useCoachingStore()

// Categorical slots, in the fixed order the palette was validated in. The set
// of exercises is fixed per student and never filtered, so a slot always means
// the same line within a chart.
const SERIES_COLORS = ['var(--series-1)', 'var(--series-2)', 'var(--series-3)', 'var(--series-4)']
// The goal a student trains for, mapped to a slot by identity — the mapping is
// the same for every roster, so a colour never changes meaning between views.
const GOAL_COLORS: Record<string, string> = {
  fat_loss: 'var(--series-1)',
  hypertrophy: 'var(--series-2)',
  strength: 'var(--series-3)',
}
// The WHO healthy range, drawn as a reference band behind the students.
const HEALTHY_BMI: [number, number] = [18.5, 25]

const students = ref<StudentSummary[]>([])
const selected = ref<StudentSummary | null>(null)
const dashboard = ref<StudentDashboard | null>(null)
const loading = ref(true)
const loadingDetail = ref(false)
const error = ref(false)

onMounted(async () => {
  try {
    students.value = await listStudents()
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
})

// Only the newest request may write: clicking down the list fires several, and
// a slow earlier one must not land on top of the student now selected.
let pendingRequest = 0

async function select(student: StudentSummary): Promise<void> {
  const request = ++pendingRequest
  selected.value = student
  // The previous student's data is dropped straight away — stale numbers under
  // a new name would be worse than a blank — but the slots below keep their
  // height, so the panel dims in place instead of collapsing and jumping back.
  dashboard.value = null
  loadingDetail.value = true
  try {
    const detail = await getStudent(student.id)
    if (request !== pendingRequest) return
    dashboard.value = detail
  } catch {
    if (request === pendingRequest) error.value = true
  } finally {
    if (request === pendingRequest) loadingDetail.value = false
  }
}

// Exercise names are localized server-side, so a language switch reloads them.
watch(locale, () => {
  if (selected.value) void select(selected.value)
})

function daysSince(day: string | null): number | null {
  if (!day) return null
  const diff = Date.now() - new Date(`${day}T00:00:00`).getTime()
  return Math.max(0, Math.floor(diff / 86_400_000))
}

/** Latest estimated 1RM of a progression, which is the last point. */
function current(points: { value: number }[]): number {
  return points.length ? points[points.length - 1].value : 0
}

/** Up to two initials, the same shorthand the roster avatars use. */
function initialsOf(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

function formatDay(day: string, withYear = false): string {
  return new Date(`${day}T00:00:00`).toLocaleDateString(locale.value, {
    day: 'numeric',
    month: 'short',
    ...(withYear ? { year: 'numeric' } : {}),
  })
}

const strengthSeries = computed<LineSeries[]>(() =>
  (dashboard.value?.strength ?? []).map((progression, index) => ({
    key: progression.exerciseId,
    name: progression.exerciseName,
    color: SERIES_COLORS[index % SERIES_COLORS.length],
    points: progression.points.map((point) => ({ on: point.on, value: point.value })),
  })),
)

const weightSeries = computed<LineSeries[]>(() => {
  const points = dashboard.value?.bodyWeight ?? []
  // A line needs two points to say anything; one measurement is just the KPI.
  if (points.length < 2) return []
  return [
    {
      key: 'weight',
      name: t('students.weightTitle'),
      color: 'var(--series-1)',
      points: points.map((point) => ({ on: point.on, value: point.value })),
    },
  ]
})

const adherenceBars = computed<Bar[]>(() =>
  (dashboard.value?.adherence ?? []).map((week) => ({
    label: formatDay(week.weekStart),
    title: t('students.weekOf', { date: formatDay(week.weekStart, true) }),
    value: week.sessions,
  })),
)

/** One dot per student with both attributes known; colour carries the goal. */
const rosterPoints = computed<ScatterPoint[]>(() =>
  students.value
    .filter((student) => student.age !== null && student.bmi !== null)
    .map((student) => ({
      key: student.id,
      initials: initialsOf(student.name),
      name: student.name,
      x: student.age as number,
      y: student.bmi as number,
      group: student.goal ?? 'unknown',
      groupLabel: student.goal ? t(`goal.${student.goal}`) : '—',
      color: student.goal ? GOAL_COLORS[student.goal] : 'var(--color-muted)',
    })),
)
</script>

<template>
  <section class="trainers">
    <header class="intro animate-in">
      <p class="eyebrow">{{ t('students.eyebrow') }}</p>
      <h1>
        <span class="gradient-text">{{ t('students.titleHighlight') }}</span>
        {{ t('students.titleRest') }}
      </h1>
      <p class="lead">{{ t('students.lead') }}</p>
    </header>

    <!-- Coach dashboard -->
    <p v-if="loading" class="hint">{{ t('students.loading') }}</p>
    <p v-else-if="error && !students.length" class="hint error" role="alert">
      {{ t('students.error') }}
    </p>
    <p v-else-if="!students.length" class="hint">{{ t('students.empty') }}</p>

    <div v-else class="coach">
      <ul class="students">
        <li v-for="st in students" :key="st.id">
          <button
            type="button"
            class="student"
            :class="{ on: selected?.id === st.id }"
            @click="select(st)"
          >
            <span class="avatar sm" aria-hidden="true">{{ initialsOf(st.name) }}</span>
            <span class="student-info">
              <span class="student-name">{{ st.name }}</span>
              <span class="student-meta">
                <template v-if="st.goal">{{ t(`goal.${st.goal}`) }} · </template>
                <template v-if="st.level">{{ t(`difficulty.${st.level}`) }} · </template>
                <template v-if="daysSince(st.lastSessionOn) !== null">
                  {{ t('students.lastActive', daysSince(st.lastSessionOn) ?? 0) }}
                </template>
                <template v-else>{{ t('students.never') }}</template>
              </span>
            </span>
            <span
              class="streak"
              :class="{ low: st.sessionsLast30d < 8 }"
              :title="t('students.kpiSessions30')"
              >{{ st.sessionsLast30d }}</span
            >
          </button>
        </li>
      </ul>

      <div class="detail glass">
        <!-- Nothing selected: the roster as a whole, so the panel is never empty. -->
        <template v-if="!selected">
          <h2 class="detail-name">{{ t('students.rosterTitle') }}</h2>
          <p class="hint">{{ t('trainers.selectStudent') }}</p>
          <ScatterChart
            v-if="rosterPoints.length"
            :points="rosterPoints"
            :x-label="t('students.ageAxis')"
            :y-label="t('students.kpiBmi')"
            :y-band="HEALTHY_BMI"
            :y-band-label="t('students.healthyBmi')"
          />
        </template>
        <template v-else>
          <h2 class="detail-name">{{ selected.name }}</h2>

          <!-- Headline numbers, straight from the student's logged history. -->
          <ul class="kpis">
            <li class="kpi">
              <span class="kpi-value">{{ dashboard?.totalSessions ?? '—' }}</span>
              <span class="kpi-label">{{ t('students.kpiTotal') }}</span>
            </li>
            <li class="kpi">
              <span class="kpi-value">{{ selected.sessionsLast30d }}</span>
              <span class="kpi-label">{{ t('students.kpiSessions30') }}</span>
            </li>
            <li class="kpi">
              <span class="kpi-value"
                >{{ selected.weightKg ?? '—' }}<small v-if="selected.weightKg"> kg</small></span
              >
              <span class="kpi-label">
                {{ t('students.kpiWeight') }}
                <template v-if="dashboard?.weightChangeKg">
                  ({{ dashboard.weightChangeKg > 0 ? '+' : '' }}{{ dashboard.weightChangeKg }})
                </template>
              </span>
            </li>
            <li class="kpi">
              <span class="kpi-value">{{ selected.bmi ?? '—' }}</span>
              <span class="kpi-label">
                {{ t('students.kpiBmi') }}
                <template v-if="selected.age"
                  >· {{ t('students.years', { n: selected.age }) }}</template
                >
              </span>
            </li>
          </ul>

          <!-- Each chart lives in a slot that already has its final height, so
               switching student dims the panel in place: no collapse, no jump
               back, nothing moving under the pointer. -->
          <h3 class="section">{{ t('students.strengthTitle') }}</h3>
          <div class="slot strength" :class="{ busy: loadingDetail }" aria-live="polite">
            <template v-if="dashboard?.strength.length">
              <LineChart :series="strengthSeries" unit="kg" :height="230" />
              <!-- The gain per exercise is the number the trainer acts on, so it
                   stays written out instead of living only in the chart. -->
              <ul class="progress-list">
                <li v-for="p in dashboard.strength" :key="p.exerciseId" class="progress-row">
                  <span class="ex">{{ p.exerciseName }}</span>
                  <span class="stat">
                    {{ current(p.points) }} kg ·
                    {{ t('students.sessionsCount', { n: p.points.length }, p.points.length) }}
                    <span v-if="p.gainPct > 0" class="gain">+{{ p.gainPct }}%</span>
                  </span>
                </li>
              </ul>
            </template>
            <p v-else-if="!loadingDetail" class="hint">{{ t('students.noStrength') }}</p>
            <p v-else class="hint">{{ t('students.loading') }}</p>
          </div>

          <template v-if="loadingDetail || weightSeries.length">
            <h3 class="section">{{ t('students.weightTitle') }}</h3>
            <div class="slot weight" :class="{ busy: loadingDetail }">
              <LineChart
                v-if="weightSeries.length"
                :series="weightSeries"
                unit="kg"
                area
                :height="180"
              />
            </div>
          </template>

          <template v-if="loadingDetail || adherenceBars.length">
            <h3 class="section">
              {{ t('students.adherenceTitle') }}
              <span class="assigned">{{ t('students.adherenceHint') }}</span>
            </h3>
            <div class="slot adherence" :class="{ busy: loadingDetail }">
              <BarChart v-if="adherenceBars.length" :bars="adherenceBars" :height="170" />
              <p v-else class="hint">{{ t('students.loading') }}</p>
            </div>
          </template>

          <h3 class="section">
            {{ t('trainers.assign') }}
            <span class="assigned">{{
              t('trainers.assignedCount', { n: coaching.assigned(selected.id).length })
            }}</span>
          </h3>
          <div class="assignables">
            <label
              v-for="ex in ASSIGNABLE"
              :key="ex"
              class="assignable"
              :class="{ on: coaching.assigned(selected.id).includes(ex) }"
            >
              <input
                type="checkbox"
                :checked="coaching.assigned(selected.id).includes(ex)"
                @change="coaching.toggle(selected.id, ex)"
              />
              <span class="box" aria-hidden="true"></span>
              <span class="ex-name">{{ ex }}</span>
            </label>
          </div>
          <p class="note">{{ t('trainers.assignNote') }}</p>
        </template>
      </div>
    </div>
  </section>
</template>

<style scoped>
.trainers {
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
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.preview {
  letter-spacing: 0.04em;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-size: 0.62rem;
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
.tabs {
  display: flex;
  gap: var(--space-xs);
}
.tab {
  padding: 8px 18px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-text);
  font: inherit;
  cursor: pointer;
}
.tab.on {
  background: var(--gradient);
  color: #06121a;
  font-weight: 700;
  border-color: transparent;
  box-shadow: var(--glow);
}
.cards {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-md);
}
.card {
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
  text-align: center;
}
.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--gradient);
  color: #06121a;
  font-weight: 800;
  font-size: 1.1rem;
}
.avatar.sm {
  width: 40px;
  height: 40px;
  font-size: 0.9rem;
}
.name {
  margin: 0;
  font-size: 1.1rem;
}
.badge {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--color-accent-soft);
  color: var(--color-accent);
}
.rating {
  margin: 0;
  color: #fbbf24;
  font-size: 0.9rem;
}
.price {
  margin: var(--space-xs) 0 0;
  font-size: 1.3rem;
  font-weight: 800;
}
.price span {
  font-size: 0.8rem;
  font-weight: 400;
  color: var(--color-muted);
}
.hire {
  margin-top: var(--space-sm);
  padding: 8px 20px;
  border: none;
  border-radius: 999px;
  background: var(--gradient);
  color: #06121a;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
.active-badge {
  margin: var(--space-sm) 0 0;
  color: var(--color-accent);
  font-weight: 700;
  font-size: 0.9rem;
}
.cancel {
  padding: 6px 16px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-muted);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
.cancel:hover {
  border-color: var(--color-danger);
  color: var(--color-danger);
}
.coach {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-md);
}
@media (min-width: 820px) {
  .coach {
    grid-template-columns: minmax(0, 280px) minmax(0, 1fr);
    align-items: start;
  }
}
.students {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.student {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.student.on,
.student:hover {
  border-color: var(--color-accent);
}
.student-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.student-name {
  font-weight: 600;
}
.student-meta {
  font-size: 0.78rem;
  color: var(--color-muted);
}
/* Sessions in the last 30 days: the one number that says "chase this one". */
.streak {
  margin-left: auto;
  flex: none;
  min-width: 28px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-size: 0.78rem;
  font-weight: 700;
  text-align: center;
}
.streak.low {
  background: color-mix(in srgb, var(--color-danger) 15%, transparent);
  color: var(--color-danger);
}
.kpis {
  list-style: none;
  margin: 0 0 var(--space-md);
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: var(--space-xs);
}
.kpi {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-surface-strong);
}
.kpi-value {
  font-size: 1.35rem;
  font-weight: 800;
  line-height: 1;
}
.kpi-value small {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-muted);
}
.kpi-label {
  font-size: 0.72rem;
  color: var(--color-muted);
}
.gain {
  margin-left: 6px;
  color: var(--color-accent);
  font-weight: 700;
}
/* Reserved space per chart (its height plus its legend, table toggle and, for
   strength, the per-exercise list). Holding the frame is what stops the panel
   from collapsing and springing back while the next student loads. */
.slot {
  transition: opacity 0.18s ease;
}
.slot.busy {
  opacity: 0.5;
  display: grid;
  place-items: center;
}
.slot.strength {
  min-height: 400px;
}
.slot.weight {
  min-height: 210px;
}
.slot.adherence {
  min-height: 200px;
}
@media (prefers-reduced-motion: reduce) {
  .slot {
    transition: none;
  }
}
.hint.error {
  color: var(--color-danger);
}
.detail {
  padding: var(--space-lg);
}
.hint {
  margin: 0;
  color: var(--color-muted);
}
.detail-name {
  margin: 0 0 var(--space-sm);
}
.section {
  margin: var(--space-md) 0 var(--space-xs);
  font-size: 0.95rem;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-sm);
}
.assigned {
  font-size: 0.75rem;
  color: var(--color-accent);
}
.progress-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.progress-row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-sm);
  padding: 6px 10px;
  background: var(--color-surface-strong);
  border-radius: var(--radius-sm);
  font-size: 0.88rem;
}
.stat {
  color: var(--color-muted);
}
.assignables {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--space-xs);
}
/* Each option is a selectable chip: the whole row is the hit area, and the
   native checkbox stays in the DOM (keyboard + screen readers) but hidden. */
.assignable {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  font-size: 0.85rem;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    background 0.18s ease;
}
.assignable:hover {
  border-color: var(--color-accent);
}
.assignable.on {
  border-color: var(--color-accent);
  background: var(--color-accent-soft);
}
.assignable input {
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
  background: var(--color-surface-strong);
  transition:
    background 0.18s ease,
    border-color 0.18s ease;
}
/* Checkmark drawn with a rotated rectangle, so no icon font is needed. */
.box::after {
  content: '';
  width: 5px;
  height: 9px;
  border: solid transparent;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg) translate(-1px, -1px);
  transition: border-color 0.18s ease;
}
.assignable.on .box {
  background: var(--gradient);
  border-color: transparent;
}
.assignable.on .box::after {
  border-color: #06121a;
}
.assignable input:focus-visible + .box {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
.ex-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.note {
  margin: var(--space-sm) 0 0;
  color: var(--color-muted);
  font-size: 0.82rem;
}
</style>
