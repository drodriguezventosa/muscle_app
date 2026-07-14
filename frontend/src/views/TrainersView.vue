<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { ASSIGNABLE, STUDENTS, TRAINERS, type Student, type Trainer } from '@/data/coaching'
import { useCoachingStore } from '@/stores/coaching'

const { t } = useI18n()
const coaching = useCoachingStore()

const tab = ref<'hire' | 'coach'>('hire')
const hiring = ref<Trainer | null>(null)
const selected = ref<Student | null>(null)
</script>

<template>
  <section class="trainers">
    <header class="intro animate-in">
      <p class="eyebrow">
        {{ t('trainers.eyebrow') }} <span class="preview">{{ t('trainers.preview') }}</span>
      </p>
      <h1>
        <span class="gradient-text">{{ t('trainers.titleHighlight') }}</span>
        {{ t('trainers.titleRest') }}
      </h1>
      <p class="lead">{{ t('trainers.lead') }}</p>
    </header>

    <div class="tabs animate-in" style="animation-delay: 0.06s">
      <button type="button" class="tab" :class="{ on: tab === 'hire' }" @click="tab = 'hire'">
        {{ t('trainers.tabHire') }}
      </button>
      <button type="button" class="tab" :class="{ on: tab === 'coach' }" @click="tab = 'coach'">
        {{ t('trainers.tabCoach') }}
      </button>
    </div>

    <!-- Hire a trainer -->
    <ul v-if="tab === 'hire'" class="cards">
      <li v-for="tr in TRAINERS" :key="tr.id" class="card glass">
        <div class="avatar" aria-hidden="true">{{ tr.initials }}</div>
        <h2 class="name">{{ tr.name }}</h2>
        <span class="badge">{{ t(`goal.${tr.specialty}`) }}</span>
        <p class="rating">★ {{ tr.rating.toFixed(1) }}</p>
        <p class="price">
          {{ tr.pricePerMonth }} € <span>{{ t('trainers.perMonth') }}</span>
        </p>
        <button type="button" class="hire" @click="hiring = tr">{{ t('trainers.hire') }}</button>
      </li>
    </ul>

    <!-- Coach dashboard -->
    <div v-else class="coach">
      <ul class="students">
        <li v-for="st in STUDENTS" :key="st.id">
          <button
            type="button"
            class="student"
            :class="{ on: selected?.id === st.id }"
            @click="selected = st"
          >
            <span class="avatar sm" aria-hidden="true">{{ st.initials }}</span>
            <span class="student-info">
              <span class="student-name">{{ st.name }}</span>
              <span class="student-meta">
                {{ t(`goal.${st.goal}`) }} · {{ t(`difficulty.${st.level}`) }} ·
                {{ t('trainers.lastActive', { n: st.lastActiveDays }) }}
              </span>
            </span>
          </button>
        </li>
      </ul>

      <div class="detail glass">
        <p v-if="!selected" class="hint">{{ t('trainers.selectStudent') }}</p>
        <template v-else>
          <h2 class="detail-name">{{ selected.name }}</h2>

          <h3 class="section">{{ t('trainers.studentProgress') }}</h3>
          <ul class="progress-list">
            <li v-for="p in selected.progress" :key="p.exercise" class="progress-row">
              <span class="ex">{{ p.exercise }}</span>
              <span class="stat"
                >{{ t('trainers.best') }} {{ p.best }} kg · {{ p.sessions }}
                {{ t('trainers.sessions') }}</span
              >
            </li>
          </ul>

          <h3 class="section">
            {{ t('trainers.assign') }}
            <span class="assigned">{{
              t('trainers.assignedCount', { n: coaching.assigned(selected.id).length })
            }}</span>
          </h3>
          <div class="assignables">
            <label v-for="ex in ASSIGNABLE" :key="ex" class="assignable">
              <input
                type="checkbox"
                :checked="coaching.assigned(selected.id).includes(ex)"
                @change="coaching.toggle(selected.id, ex)"
              />
              {{ ex }}
            </label>
          </div>
          <p class="note">{{ t('trainers.assignNote') }}</p>
        </template>
      </div>
    </div>

    <!-- Hire (demo) modal -->
    <Teleport to="body">
      <div
        v-if="hiring"
        class="overlay"
        role="dialog"
        aria-modal="true"
        @click.self="hiring = null"
      >
        <div class="modal glass">
          <h2>{{ t('trainers.hireDemoTitle') }}</h2>
          <p>
            {{ t('trainers.hireDemoBody', { name: hiring.name, price: hiring.pricePerMonth }) }}
          </p>
          <button type="button" class="hire" @click="hiring = null">
            {{ t('trainers.close') }}
          </button>
        </div>
      </div>
    </Teleport>
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
.assignable {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  cursor: pointer;
}
.note {
  margin: var(--space-sm) 0 0;
  color: var(--color-muted);
  font-size: 0.82rem;
}
.overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md);
  background: rgba(4, 7, 15, 0.72);
  backdrop-filter: blur(6px);
}
.modal {
  max-width: 420px;
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  text-align: center;
}
.modal h2 {
  margin: 0;
}
.modal p {
  margin: 0;
  color: var(--color-muted);
}
.modal .hire {
  align-self: center;
}
</style>
