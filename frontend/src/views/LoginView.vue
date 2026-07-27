<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '@/stores/auth'

// There is no public sign-up: only the two seeded demo accounts exist, and their
// credentials are shown on purpose so the app can be tried without asking for
// any (they only ever hold demo data).
const DEMO_PASSWORD = 'muscleapp-demo'
const DEMO_TRAINER = 'entrenador@demo.muscleapp'
const DEMO_CLIENT = 'alumno@demo.muscleapp'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref(DEMO_TRAINER)
const password = ref(DEMO_PASSWORD)

/** Send the user where they were headed, or to the trainers area. */
async function afterSignIn(): Promise<void> {
  const redirect = route.query.redirect
  await router.push(typeof redirect === 'string' ? redirect : '/trainers')
}

async function submit(): Promise<void> {
  if (await auth.signIn(email.value, password.value)) await afterSignIn()
}

async function signInAs(demoEmail: string): Promise<void> {
  email.value = demoEmail
  password.value = DEMO_PASSWORD
  await submit()
}
</script>

<template>
  <section class="login">
    <header class="intro animate-in">
      <p class="eyebrow">{{ t('auth.eyebrow') }}</p>
      <h1>
        <span class="gradient-text">{{ t('auth.titleHighlight') }}</span>
        {{ t('auth.titleRest') }}
      </h1>
      <p class="lead">{{ t('auth.lead') }}</p>
    </header>

    <div class="card glass animate-in" style="animation-delay: 0.08s">
      <p class="demo-banner" role="note">{{ t('auth.demoBanner') }}</p>

      <!-- One click per role: the reviewer never has to type credentials. -->
      <div class="quick">
        <button
          type="button"
          class="quick-btn primary"
          :disabled="auth.loading"
          @click="signInAs(DEMO_TRAINER)"
        >
          <span aria-hidden="true">🧑‍🏫</span> {{ t('auth.asTrainer') }}
        </button>
        <button
          type="button"
          class="quick-btn"
          :disabled="auth.loading"
          @click="signInAs(DEMO_CLIENT)"
        >
          <span aria-hidden="true">🏋️</span> {{ t('auth.asClient') }}
        </button>
      </div>

      <p class="or">{{ t('auth.or') }}</p>

      <form class="form" @submit.prevent="submit">
        <label class="field">
          <span>{{ t('auth.email') }}</span>
          <input v-model="email" type="email" autocomplete="username" required />
        </label>
        <label class="field">
          <span>{{ t('auth.password') }}</span>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            required
            minlength="6"
          />
        </label>
        <p v-if="auth.error" class="error" role="alert">{{ auth.error }}</p>
        <button type="submit" class="submit" :disabled="auth.loading">
          <span v-if="auth.loading" class="spinner" aria-hidden="true"></span>
          {{ auth.loading ? t('auth.signingIn') : t('auth.signIn') }}
        </button>
      </form>

      <p class="hint">{{ t('auth.noSignup') }}</p>
    </div>
  </section>
</template>

<style scoped>
.login {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  max-width: 520px;
  margin: 0 auto;
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
  font-size: clamp(1.7rem, 4vw, 2.4rem);
  font-weight: 800;
  line-height: 1.1;
}
.lead {
  margin: 0;
  color: var(--color-muted);
}
.card {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-lg);
}
.demo-banner {
  margin: 0;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-size: 0.85rem;
}
.quick {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}
.quick-btn {
  flex: 1 1 200px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  padding: 10px 16px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
  font-size: 0.9rem;
  cursor: pointer;
}
.quick-btn:hover:not(:disabled) {
  border-color: var(--color-accent);
  box-shadow: var(--glow);
}
.quick-btn.primary {
  background: var(--gradient);
  border-color: transparent;
  color: #06121a;
  font-weight: 700;
}
.quick-btn:disabled {
  opacity: 0.6;
  cursor: default;
}
.or {
  margin: 0;
  text-align: center;
  color: var(--color-muted);
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  font-size: 0.85rem;
  color: var(--color-muted);
}
.field input {
  width: 100%;
  min-width: 0;
}
.error {
  margin: 0;
  color: var(--color-danger);
  font-size: 0.88rem;
}
.submit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  padding: 10px 18px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--gradient);
  color: #06121a;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
.submit:disabled {
  opacity: 0.7;
  cursor: default;
}
.spinner {
  display: inline-block;
  width: 13px;
  height: 13px;
  border: 2px solid rgba(6, 18, 26, 0.3);
  border-top-color: #06121a;
  border-radius: 50%;
  animation: login-rotate 0.7s linear infinite;
}
@keyframes login-rotate {
  to {
    transform: rotate(360deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation-duration: 2s;
  }
}
.hint {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.8rem;
}
</style>
