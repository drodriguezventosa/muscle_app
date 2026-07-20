<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import HealthDisclaimer from '@/components/HealthDisclaimer.vue'
import type { ActivityLevel, Food, NutritionGoal } from '@/api/types'
import { useNutritionStore } from '@/stores/nutrition'

const { t, locale } = useI18n()
const store = useNutritionStore()

const ACTIVITIES: ActivityLevel[] = ['sedentary', 'light', 'moderate', 'active', 'very_active']
const GOALS: NutritionGoal[] = ['lose_fat', 'maintain', 'gain_muscle']
const SEXES = ['male', 'female', 'other'] as const

// Menu builder: pick foods (grams) and see the running macro totals.
interface MenuItem {
  food: Food
  grams: number
}
const search = ref('')
const menu = reactive<MenuItem[]>([])

onMounted(() => void store.loadFoods())
watch(locale, () => void store.loadFoods()) // re-localize food names

const filteredFoods = computed(() => {
  const q = search.value.trim().toLowerCase()
  const list = q ? store.foods.filter((f) => f.name.toLowerCase().includes(q)) : store.foods
  return list.slice(0, 12)
})

function addFood(food: Food): void {
  const existing = menu.find((m) => m.food.id === food.id)
  if (existing) existing.grams += 100
  else menu.push({ food, grams: 100 })
}
function removeItem(index: number): void {
  menu.splice(index, 1)
}

// Meal recommendation chat (RAG over foods).
const chatInput = ref('')
function ask(): void {
  void store.recommend(chatInput.value)
}

const totals = computed(() => {
  const acc = { kcal: 0, protein: 0, carbs: 0, fat: 0 }
  for (const { food, grams } of menu) {
    const k = grams / 100
    acc.kcal += food.kcal * k
    acc.protein += food.proteinG * k
    acc.carbs += food.carbsG * k
    acc.fat += food.fatG * k
  }
  return {
    kcal: Math.round(acc.kcal),
    protein: Math.round(acc.protein),
    carbs: Math.round(acc.carbs),
    fat: Math.round(acc.fat),
  }
})
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

    <!-- Menu builder -->
    <div class="card glass menu-builder animate-in" style="animation-delay: 0.18s">
      <h2 class="mb-title">{{ t('nutrition.menu.title') }}</h2>
      <p class="mb-lead">{{ t('nutrition.menu.lead') }}</p>
      <input
        v-model="search"
        class="search"
        type="search"
        :placeholder="t('nutrition.menu.search')"
      />
      <ul class="foods">
        <li v-for="f in filteredFoods" :key="f.id">
          <button type="button" class="food" @click="addFood(f)">
            <span class="food-emoji" aria-hidden="true">{{ f.emoji }}</span>
            <span class="food-text">
              <span class="food-name">{{ f.name }}</span>
              <span class="food-kcal">{{ f.kcal }} {{ t('nutrition.menu.per100') }}</span>
            </span>
            <span class="add" aria-hidden="true">+</span>
          </button>
        </li>
      </ul>

      <div v-if="menu.length" class="menu">
        <div v-for="(item, i) in menu" :key="item.food.id" class="menu-item">
          <span class="mi-emoji" aria-hidden="true">{{ item.food.emoji }}</span>
          <span class="mi-name">{{ item.food.name }}</span>
          <label class="mi-grams">
            <input v-model.number="item.grams" type="number" min="0" step="10" />
            g
          </label>
          <span class="mi-kcal">{{ Math.round((item.food.kcal * item.grams) / 100) }} kcal</span>
          <button
            type="button"
            class="rm"
            :aria-label="t('nutrition.menu.remove')"
            @click="removeItem(i)"
          >
            ✕
          </button>
        </div>
        <div class="totals">
          <strong>{{ totals.kcal }} kcal</strong>
          <span
            >{{ t('nutrition.macros.protein') }} {{ totals.protein }}g ·
            {{ t('nutrition.macros.carbs') }} {{ totals.carbs }}g · {{ t('nutrition.macros.fat') }}
            {{ totals.fat }}g</span
          >
          <span v-if="store.result" class="vs">
            {{
              t('nutrition.menu.ofTarget', {
                n: Math.round((totals.kcal / store.result.calories) * 100),
              })
            }}
          </span>
        </div>
      </div>
      <p v-else class="hint">{{ t('nutrition.menu.empty') }}</p>
    </div>

    <!-- Meal recommendation chat (RAG) -->
    <div class="card glass animate-in" style="animation-delay: 0.24s">
      <h2 class="mb-title">{{ t('nutrition.chat.title') }}</h2>
      <p class="mb-lead">{{ t('nutrition.chat.lead') }}</p>
      <form class="chat-form" @submit.prevent="ask">
        <input v-model="chatInput" type="text" :placeholder="t('nutrition.chat.placeholder')" />
        <button type="submit" class="calc" :disabled="store.chatLoading">
          {{ store.chatLoading ? t('nutrition.chat.thinking') : t('nutrition.chat.ask') }}
        </button>
      </form>
      <p v-if="store.chatReply" class="chat-reply">{{ store.chatReply }}</p>
      <ul v-if="store.chatFoods.length" class="foods">
        <li v-for="f in store.chatFoods" :key="f.id">
          <button type="button" class="food" @click="addFood(f)">
            <span class="food-emoji" aria-hidden="true">{{ f.emoji }}</span>
            <span class="food-text">
              <span class="food-name">{{ f.name }}</span>
              <span class="food-kcal">{{ f.kcal }} {{ t('nutrition.menu.per100') }}</span>
            </span>
            <span class="add" aria-hidden="true">+</span>
          </button>
        </li>
      </ul>
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
.menu-builder {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.mb-title {
  margin: 0;
  font-size: 1.15rem;
}
.mb-lead {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.9rem;
}
.foods {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--space-sm);
}
.food {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  width: 100%;
  height: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
  cursor: pointer;
  text-align: left;
}
.food:hover {
  border-color: var(--color-accent);
}
.food-emoji {
  font-size: 1.5rem;
  line-height: 1;
  flex: none;
}
.food-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}
.food-name {
  font-weight: 600;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.food-kcal {
  color: var(--color-muted);
  font-size: 0.75rem;
}
.add {
  color: var(--color-accent);
  font-weight: 800;
  flex: none;
}
.menu {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-md);
}
.menu-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.mi-emoji {
  font-size: 1.2rem;
  line-height: 1;
  flex: none;
}
.mi-name {
  flex: 1;
  min-width: 0;
}
.mi-grams {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-muted);
  font-size: 0.85rem;
}
.mi-grams input {
  width: 68px;
}
.mi-kcal {
  color: var(--color-muted);
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
}
.rm {
  border: none;
  background: none;
  color: var(--color-muted);
  cursor: pointer;
}
.rm:hover {
  color: var(--color-danger);
}
.totals {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-sm) var(--space-md);
  padding-top: var(--space-sm);
  border-top: 1px dashed var(--color-border);
}
.totals strong {
  font-size: 1.1rem;
}
.totals span {
  color: var(--color-muted);
  font-size: 0.85rem;
}
.totals .vs {
  color: var(--color-accent);
}
.chat-form {
  display: flex;
  gap: var(--space-sm);
}
.chat-form input {
  flex: 1;
}
.chat-form .calc {
  width: auto;
  white-space: nowrap;
}
.chat-reply {
  margin: 0;
  white-space: pre-line;
  color: var(--color-text);
  font-size: 0.92rem;
}
</style>
