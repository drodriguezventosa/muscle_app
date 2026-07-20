<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import HealthDisclaimer from '@/components/HealthDisclaimer.vue'
import type { ActivityLevel, NutritionGoal } from '@/api/types'
import { useNutritionStore } from '@/stores/nutrition'

const { t } = useI18n()
const store = useNutritionStore()

const ACTIVITIES: ActivityLevel[] = ['sedentary', 'light', 'moderate', 'active', 'very_active']
const GOALS: NutritionGoal[] = ['lose_fat', 'maintain', 'gain_muscle']
const SEXES = ['male', 'female', 'other'] as const
</script>

<template>
  <section class="nutrition">
    <header class="intro animate-in">
      <p class="eyebrow">{{ t('nutrition.eyebrow') }}</p>
      <h1>
        <span class="gradient-text">{{ t('nutrition.titleHighlight') }}</span>
        {{ t('nutrition.titleRest') }}
      </h1>
      <p class="lead">{{ t('nutrition.lead') }}</p>
      <HealthDisclaimer />
      <p class="nutri-note" role="note">{{ t('nutrition.disclaimer') }}</p>
    </header>

    <div class="layout">
      <!-- Form -->
      <form
        class="card glass animate-in"
        style="animation-delay: 0.06s"
        @submit.prevent="store.calculate()"
      >
        <div class="grid2">
          <label>
            {{ t('nutrition.form.sex') }}
            <select v-model="store.sex">
              <option value="">{{ t('nutrition.form.sexUnset') }}</option>
              <option v-for="s in SEXES" :key="s" :value="s">{{ t(`nutrition.sex.${s}`) }}</option>
            </select>
          </label>
          <label>
            {{ t('nutrition.form.age') }}
            <input v-model.number="store.age" type="number" min="14" max="100" />
          </label>
          <label>
            {{ t('nutrition.form.height') }}
            <input v-model.number="store.heightCm" type="number" min="120" max="230" />
          </label>
          <label>
            {{ t('nutrition.form.weight') }}
            <input v-model.number="store.weightKg" type="number" min="30" max="300" />
          </label>
        </div>
        <label>
          {{ t('nutrition.form.activity') }}
          <select v-model="store.activity">
            <option v-for="a in ACTIVITIES" :key="a" :value="a">
              {{ t(`nutrition.activity.${a}`) }}
            </option>
          </select>
        </label>
        <label>
          {{ t('nutrition.form.goal') }}
          <select v-model="store.goal">
            <option v-for="g in GOALS" :key="g" :value="g">{{ t(`nutrition.goal.${g}`) }}</option>
          </select>
        </label>
        <button class="calc" type="submit" :disabled="store.loading">
          {{ store.loading ? t('nutrition.form.calculating') : t('nutrition.form.calculate') }}
        </button>
        <p v-if="store.error" class="error">{{ store.error }}</p>
      </form>

      <!-- Result -->
      <div class="card glass result animate-in" style="animation-delay: 0.12s">
        <p v-if="!store.result" class="hint">{{ t('nutrition.hint') }}</p>
        <template v-else>
          <p v-if="store.result.warning" class="warning">
            ⚠️ {{ t(`nutrition.warnings.${store.result.warning}`) }}
          </p>
          <div class="calories">
            <span class="n">{{ store.result.calories }}</span>
            <span class="u">{{ t('nutrition.kcalPerDay') }}</span>
            <span class="sub">
              {{ t(`nutrition.goal.${store.result.goal}`) }} · {{ t('nutrition.tdee') }}
              {{ store.result.tdee }} kcal
            </span>
          </div>
          <div class="macros">
            <div class="macro">
              <span class="mv">{{ store.result.proteinG }} g</span>
              <span class="ml">{{ t('nutrition.macros.protein') }}</span>
            </div>
            <div class="macro">
              <span class="mv">{{ store.result.carbsG }} g</span>
              <span class="ml">{{ t('nutrition.macros.carbs') }}</span>
            </div>
            <div class="macro">
              <span class="mv">{{ store.result.fatG }} g</span>
              <span class="ml">{{ t('nutrition.macros.fat') }}</span>
            </div>
          </div>
          <p class="bmi">
            {{ t('nutrition.bmi') }} <strong>{{ store.result.bmi }}</strong> ·
            {{ t(`nutrition.bmiCategory.${store.result.bmiCategory}`) }}
          </p>
        </template>
      </div>
    </div>
  </section>
</template>

<style scoped>
.nutrition {
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
  max-width: 60ch;
}
.nutri-note {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-muted);
  max-width: 70ch;
}
.layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-lg);
  align-items: start;
}
@media (min-width: 820px) {
  .layout {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }
}
.card {
  padding: var(--space-lg);
}
form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.grid2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
}
label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.85rem;
  color: var(--color-muted);
  min-width: 0;
}
input,
select {
  width: 100%;
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-input);
  color: var(--color-text);
  font: inherit;
}
input:focus,
select:focus {
  outline: none;
  border-color: var(--color-accent);
}
.calc {
  padding: 12px 16px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--gradient);
  color: #061018;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
.calc:disabled {
  opacity: 0.6;
  cursor: default;
}
.error {
  margin: 0;
  color: var(--color-danger);
  font-size: 0.9rem;
}
.result {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.hint {
  margin: 0;
  color: var(--color-muted);
}
.warning {
  margin: 0;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: rgba(251, 191, 36, 0.14);
  color: var(--color-warn, #fbbf24);
  font-size: 0.85rem;
}
.calories {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 2px;
}
.calories .n {
  font-size: 3rem;
  font-weight: 800;
  line-height: 1;
  background: var(--gradient);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.calories .u {
  color: var(--color-muted);
  font-size: 0.85rem;
  letter-spacing: 0.05em;
}
.calories .sub {
  color: var(--color-muted);
  font-size: 0.8rem;
  margin-top: 6px;
}
.macros {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-sm);
}
.macro {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--space-md) var(--space-sm);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}
.macro .mv {
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.macro .ml {
  color: var(--color-muted);
  font-size: 0.78rem;
}
.bmi {
  margin: 0;
  text-align: center;
  color: var(--color-muted);
  font-size: 0.9rem;
}
</style>
