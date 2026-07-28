<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { listTrainers, type Trainer } from '@/api/coaching'
import CheckoutModal from '@/components/CheckoutModal.vue'
import { useAuthStore } from '@/stores/auth'
import { useCoachingStore } from '@/stores/coaching'

const { t } = useI18n()
const auth = useAuthStore()
const coaching = useCoachingStore()

const trainers = ref<Trainer[]>([])
const loading = ref(true)
const error = ref(false)
const hiring = ref<Trainer | null>(null)

onMounted(async () => {
  try {
    trainers.value = await listTrainers()
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
  // Whether they already have one decides what every card offers.
  await coaching.load()
})

const hired = computed(() => coaching.trainer)

/** Two initials, the same shorthand the student avatars use. */
function initialsOf(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
}

// Hiring another trainer replaces the current one, so the button says so.
const hireLabel = computed(() => {
  if (!auth.isSignedIn) return t('trainers.hireSignIn')
  return hired.value ? t('trainers.switch') : t('trainers.hire')
})

// Browsing the trainers is open to everyone; hiring one is what needs an
// account, which is exactly the moment worth asking for one.
function hire(trainer: Trainer): void {
  // Only a student can hire, so the sign-in offers only that: a trainer
  // signing in here would land somewhere they cannot do what they came for.
  if (auth.isSignedIn) hiring.value = trainer
  else auth.promptSignIn('/trainers', 'client')
}
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

    <!-- A trainer has their own area; point them there instead of hiring. -->
    <p v-if="auth.isTrainer" class="notice animate-in">
      {{ t('trainers.youAreTrainer') }}
      <RouterLink to="/students">{{ t('trainers.goToStudents') }}</RouterLink>
    </p>
    <!-- Anyone can browse; hiring is what asks for an account. -->
    <p v-else-if="!auth.isSignedIn" class="notice animate-in">{{ t('trainers.signInToHire') }}</p>

    <!-- Already hired someone: say who, since only one at a time is possible. -->
    <p v-if="hired" class="notice animate-in">
      {{ t('trainers.yourTrainer', { name: hired.name }) }}
      <RouterLink to="/plan">{{ t('trainers.goToPlan') }}</RouterLink>
    </p>

    <p v-if="loading" class="notice">{{ t('trainers.loading') }}</p>
    <p v-else-if="error" class="notice error" role="alert">{{ t('trainers.error') }}</p>

    <!-- Hire a trainer -->
    <ul v-else class="cards">
      <li v-for="tr in trainers" :key="tr.id" class="card glass">
        <div class="avatar" aria-hidden="true">{{ initialsOf(tr.name) }}</div>
        <h2 class="name">{{ tr.name }}</h2>
        <span class="badge">{{ t(`goal.${tr.specialty}`) }}</span>
        <p class="rating">★ {{ tr.rating.toFixed(1) }}</p>
        <p v-if="tr.bio" class="bio">{{ tr.bio }}</p>
        <p class="students">{{ t('trainers.studentsCount', tr.students) }}</p>
        <p class="price">
          {{ tr.pricePerMonth }} € <span>{{ t('trainers.perMonth') }}</span>
        </p>
        <template v-if="hired?.id === tr.id">
          <p class="active-badge">✓ {{ t('trainers.active') }}</p>
          <button type="button" class="cancel" @click="coaching.cancel()">
            {{ t('trainers.cancel') }}
          </button>
        </template>
        <button v-else type="button" class="hire" @click="hire(tr)">
          {{ hireLabel }}
        </button>
      </li>
    </ul>

    <!-- Hire flow: simulated payment gateway (no real charge) -->
    <CheckoutModal v-if="hiring" :trainer="hiring" @close="hiring = null" />
  </section>
</template>

<style scoped>
.notice {
  margin: 0;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-muted);
  font-size: 0.86rem;
}
.notice a {
  color: var(--color-accent);
  font-weight: 600;
}
.notice.error {
  color: var(--color-danger);
}
.bio {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.8rem;
}
.students {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.74rem;
}
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
</style>
