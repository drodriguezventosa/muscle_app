<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Difficulty, Goal, WorkoutItem } from '@/api/types'
import HealthDisclaimer from '@/components/HealthDisclaimer.vue'
import VideoModal from '@/components/VideoModal.vue'
import { useProgressStore } from '@/stores/progress'
import { useWorkoutsStore, type Place } from '@/stores/workouts'

const { t } = useI18n()
const store = useWorkoutsStore()
const progress = useProgressStore()

const GOALS: Goal[] = ['fat_loss', 'hypertrophy', 'strength']
const LEVELS: Difficulty[] = ['beginner', 'intermediate', 'advanced']
const PLACES: Place[] = ['gym', 'home']

const activeVideo = ref<{ url: string; title: string } | null>(null)

// Per-exercise input state for logging a session.
const weightInput = reactive<Record<number, number | null>>({})
const allSetsDone = reactive<Record<number, boolean>>({})

function fmtRest(seconds: number): string {
  return seconds >= 60 ? `${Math.round(seconds / 60)} min` : `${seconds}s`
}

function logItem(item: WorkoutItem): void {
  const id = item.exercise.id
  const weight = weightInput[id] ?? progress.suggested(id)
  if (weight == null || weight < 0) return
  progress.log(id, item.exercise.name, weight, allSetsDone[id] ?? true)
  weightInput[id] = null
}

// Default the "all sets" checkbox to checked for each exercise in a new routine.
watch(
  () => store.result,
  (result) => {
    for (const item of result?.items ?? []) {
      if (allSetsDone[item.exercise.id] === undefined) allSetsDone[item.exercise.id] = true
    }
  },
)
</script>

<template>
  <section class="workouts">
    <header class="intro animate-in">
      <p class="eyebrow">{{ t('workouts.eyebrow') }}</p>
      <h1>
        <span class="gradient-text">{{ t('workouts.titleHighlight') }}</span>
        {{ t('workouts.titleRest') }}
      </h1>
      <p class="lead">{{ t('workouts.lead') }}</p>
      <HealthDisclaimer />
    </header>

    <form
      class="form glass animate-in"
      style="animation-delay: 0.06s"
      @submit.prevent="store.generate()"
    >
      <div class="field">
        <span class="label">{{ t('workouts.form.goal') }}</span>
        <div class="chips">
          <button
            v-for="g in GOALS"
            :key="g"
            type="button"
            class="chip"
            :class="{ on: store.goal === g }"
            @click="store.goal = g"
          >
            {{ t(`goal.${g}`) }}
          </button>
        </div>
      </div>

      <div class="field">
        <span class="label">{{ t('workouts.form.level') }}</span>
        <div class="chips">
          <button
            v-for="l in LEVELS"
            :key="l"
            type="button"
            class="chip"
            :class="{ on: store.experience === l }"
            @click="store.experience = l"
          >
            {{ t(`difficulty.${l}`) }}
          </button>
        </div>
      </div>

      <div class="field">
        <span class="label">{{ t('workouts.form.place') }}</span>
        <div class="chips">
          <button
            v-for="p in PLACES"
            :key="p"
            type="button"
            class="chip"
            :class="{ on: store.place === p }"
            @click="store.place = p"
          >
            {{ t(`place.${p}`) }}
          </button>
        </div>
      </div>

      <div class="numbers">
        <label class="num">
          <span class="label">{{ t('workouts.form.height') }}</span>
          <input
            v-model.number="store.heightCm"
            type="number"
            min="120"
            max="230"
            inputmode="numeric"
          />
        </label>
        <label class="num">
          <span class="label">{{ t('workouts.form.weight') }}</span>
          <input
            v-model.number="store.weightKg"
            type="number"
            min="30"
            max="300"
            inputmode="numeric"
          />
        </label>
        <label class="num">
          <span class="label">{{ t('workouts.form.age') }}</span>
          <input v-model.number="store.age" type="number" min="12" max="99" inputmode="numeric" />
        </label>
      </div>

      <p v-if="store.error" class="error" role="alert">{{ store.error }}</p>

      <button class="generate" type="submit" :disabled="store.loading">
        {{ store.loading ? t('workouts.form.generating') : t('workouts.form.generate') }}
      </button>
    </form>

    <section v-if="store.result" class="result glass animate-in" aria-live="polite">
      <header class="result-head">
        <div>
          <h2 class="title">{{ store.result.name }}</h2>
          <p class="desc">{{ store.result.description }}</p>
        </div>
        <div class="bmi">
          <span class="bmi-value">{{ store.result.bmi }}</span>
          <span class="bmi-label"
            >{{ t('workouts.result.bmi') }} · {{ t(`bmi.${store.result.bmiCategory}`) }}</span
          >
        </div>
      </header>

      <ol class="items">
        <li v-for="(item, i) in store.result.items" :key="i" class="item">
          <span class="idx">{{ i + 1 }}</span>
          <div class="item-body">
            <div class="item-top">
              <span class="item-name">{{ item.exercise.name }}</span>
              <span class="badge">{{ t(`equipment.${item.exercise.equipment}`) }}</span>
            </div>
            <p class="prescription">
              {{ item.sets }} × {{ item.reps }} · {{ t('workouts.result.rest') }}
              {{ fmtRest(item.restSeconds) }}
            </p>
            <div class="log">
              <input
                class="log-weight"
                type="number"
                min="0"
                step="0.5"
                inputmode="decimal"
                :aria-label="t('progress.weight')"
                :placeholder="
                  progress.suggested(item.exercise.id) != null
                    ? String(progress.suggested(item.exercise.id))
                    : t('progress.weight')
                "
                v-model.number="weightInput[item.exercise.id]"
              />
              <span class="kg">kg</span>
              <label class="done">
                <input type="checkbox" v-model="allSetsDone[item.exercise.id]" />
                {{ t('progress.allSets') }}
              </label>
              <button type="button" class="log-btn" @click="logItem(item)">
                {{ t('progress.log') }}
              </button>
              <span v-if="progress.last(item.exercise.id)" class="last">
                {{ t('progress.last') }} {{ progress.last(item.exercise.id)?.weight }} kg ·
                {{ t('progress.best') }} {{ progress.best(item.exercise.id) }} kg
                <span
                  v-if="
                    progress.best(item.exercise.id) > 0 &&
                    progress.last(item.exercise.id)?.weight === progress.best(item.exercise.id)
                  "
                  aria-hidden="true"
                  >⭐</span
                >
              </span>
            </div>
          </div>
          <button
            v-if="item.exercise.videoUrl"
            type="button"
            class="watch"
            :aria-label="t('video.watch')"
            @click="activeVideo = { url: item.exercise.videoUrl, title: item.exercise.name }"
          >
            <span aria-hidden="true">▶</span>
          </button>
        </li>
      </ol>
    </section>

    <VideoModal
      v-if="activeVideo"
      :url="activeVideo.url"
      :title="activeVideo.title"
      @close="activeVideo = null"
    />
  </section>
</template>

<style scoped>
.workouts {
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
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-lg);
}
.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-muted);
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}
.chip {
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-text);
  font: inherit;
  font-size: 0.85rem;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}
.chip:hover {
  border-color: var(--color-accent);
}
.chip.on {
  background: var(--gradient);
  color: #06121a;
  font-weight: 700;
  border-color: transparent;
  box-shadow: var(--glow);
}
.numbers {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
}
.num {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.num input {
  width: 120px;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-input);
  color: var(--color-text);
  font: inherit;
}
.num input:focus-visible {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: var(--glow);
}
.error {
  margin: 0;
  color: var(--color-danger);
  font-size: 0.9rem;
}
.generate {
  align-self: flex-start;
  padding: 10px 22px;
  border: none;
  border-radius: 999px;
  background: var(--gradient);
  color: #06121a;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  box-shadow: var(--glow);
  transition: transform 0.15s ease;
}
.generate:hover {
  transform: translateY(-1px);
}
.generate:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.result {
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.result-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  flex-wrap: wrap;
}
.result .title {
  margin: 0;
  font-size: 1.3rem;
}
.result .desc {
  margin: var(--space-xs) 0 0;
  color: var(--color-muted);
  max-width: 55ch;
}
.bmi {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  text-align: right;
}
.bmi-value {
  font-size: 1.5rem;
  font-weight: 800;
}
.bmi-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-accent);
}
.items {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-surface-strong);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}
.idx {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-weight: 700;
  font-size: 0.85rem;
}
.item-body {
  flex: 1;
  min-width: 0;
}
.item-top {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}
.item-name {
  font-weight: 600;
}
.badge {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-accent-soft);
  color: var(--color-accent);
}
.prescription {
  margin: 2px 0 0;
  color: var(--color-muted);
  font-size: 0.88rem;
}
.log {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-top: var(--space-sm);
  font-size: 0.82rem;
}
.log-weight {
  width: 72px;
  padding: 4px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-input);
  color: var(--color-text);
  font: inherit;
}
.log-weight:focus-visible {
  outline: none;
  border-color: var(--color-accent);
}
.kg {
  color: var(--color-muted);
  margin-right: var(--space-xs);
}
.done {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-muted);
  cursor: pointer;
}
.log-btn {
  padding: 4px 12px;
  border: 1px solid var(--color-accent);
  border-radius: 999px;
  background: transparent;
  color: var(--color-accent);
  font: inherit;
  font-size: 0.8rem;
  cursor: pointer;
}
.log-btn:hover {
  background: var(--color-accent-soft);
}
.last {
  color: var(--color-muted);
}
.watch {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border: none;
  border-radius: 50%;
  background: var(--gradient);
  color: #06121a;
  font-size: 0.75rem;
  cursor: pointer;
}
</style>
