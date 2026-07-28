<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '@/stores/auth'
import { useProgressStore } from '@/stores/progress'

// There is no public sign-up: only these two seeded accounts exist, and their
// credentials are shown on purpose so the app can be reviewed without asking
// for any. They only ever hold demo data.
const DEMO_PASSWORD = 'muscleapp-demo'
const ACCOUNTS = {
  client: { email: 'alumno@demo.muscleapp', icon: '🏋️' },
  trainer: { email: 'entrenador@demo.muscleapp', icon: '🧑‍🏫' },
} as const
type AccountKind = keyof typeof ACCOUNTS

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()

const { t } = useI18n()
const auth = useAuthStore()
const progress = useProgressStore()
const router = useRouter()

// Signing in as a student is the common case, so it is the default.
const kind = ref<AccountKind>('client')
// Typed explicitly: ACCOUNTS is `as const`, so inference would pin the ref to
// the client's literal email and reject the trainer's.
const email = ref<string>(ACCOUNTS.client.email)
const password = ref<string>(DEMO_PASSWORD)
const dialog = ref<HTMLElement | null>(null)

/** Picking a role refills the credentials, so either account is one click away. */
function choose(next: AccountKind): void {
  kind.value = next
  email.value = ACCOUNTS[next].email
  password.value = DEMO_PASSWORD
  auth.error = null
}

function close(): void {
  emit('update:modelValue', false)
}

async function submit(): Promise<void> {
  if (!(await auth.signIn(email.value, password.value))) return
  close()
  // Whatever the browser recorded before signing in belongs to this account now.
  void progress.sync()
  // Land on the area for the role: a trainer manages their students, a student
  // sees what they have to train today. A blocked route (from the guard) wins.
  const target = auth.consumeRedirect() ?? (auth.isTrainer ? '/students' : '/plan')
  await router.push(target)
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') close()
}

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    auth.error = null
    choose(kind.value) // refresh the fields in case they were edited and cancelled
    await nextTick()
    dialog.value?.querySelector('input')?.focus()
  },
)
</script>

<template>
  <Teleport to="body">
    <Transition name="login">
      <div v-if="modelValue" class="overlay" @click.self="close" @keydown="onKeydown">
        <div
          ref="dialog"
          class="dialog glass"
          role="dialog"
          aria-modal="true"
          :aria-label="t('auth.title')"
          tabindex="-1"
          @keydown="onKeydown"
        >
          <header class="head">
            <strong class="title gradient-text">{{ t('auth.title') }}</strong>
            <button class="close" type="button" :aria-label="t('auth.close')" @click="close">
              ✕
            </button>
          </header>

          <p class="demo-banner" role="note">{{ t('auth.demoBanner') }}</p>

          <!-- Role picker: switching also refills the credentials below. -->
          <p id="role-caption" class="roles-caption">{{ t('auth.howToEnter') }}</p>
          <div class="roles" role="radiogroup" aria-labelledby="role-caption">
            <button
              v-for="(account, key) in ACCOUNTS"
              :key="key"
              type="button"
              class="role"
              :class="{ active: kind === key }"
              role="radio"
              :aria-checked="kind === key"
              @click="choose(key)"
            >
              <span class="role-icon" aria-hidden="true">{{ account.icon }}</span>
              {{ key === 'client' ? t('auth.roleClient') : t('auth.roleTrainer') }}
            </button>
          </div>

          <form class="form" @submit.prevent="submit">
            <!-- Floating labels: the field reads as a single object, and the
                 label never disappears once something is typed. -->
            <div class="field">
              <input
                id="login-email"
                v-model="email"
                type="email"
                placeholder=" "
                autocomplete="username"
                required
              />
              <label for="login-email">{{ t('auth.email') }}</label>
            </div>
            <div class="field">
              <input
                id="login-password"
                v-model="password"
                type="password"
                placeholder=" "
                autocomplete="current-password"
                required
                minlength="6"
              />
              <label for="login-password">{{ t('auth.password') }}</label>
            </div>

            <p v-if="auth.error" class="error" role="alert">{{ auth.error }}</p>

            <button type="submit" class="submit" :disabled="auth.loading">
              <span v-if="auth.loading" class="spinner" aria-hidden="true"></span>
              {{ auth.loading ? t('auth.signingIn') : t('auth.signIn') }}
            </button>
          </form>

          <p class="hint">{{ t('auth.noSignup') }}</p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: grid;
  place-items: center;
  padding: var(--space-md);
  background: rgba(2, 6, 23, 0.6);
  backdrop-filter: blur(2px);
}
.dialog {
  width: min(94vw, 420px);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md, 16px);
  background: var(--color-elevated);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.4);
  outline: none;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
}
.title {
  font-size: 1.15rem;
}
.close {
  border: none;
  background: none;
  color: var(--color-muted);
  font-size: 1rem;
  cursor: pointer;
}
.close:hover {
  color: var(--color-text);
}
.demo-banner {
  margin: 0;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-size: 0.82rem;
}
/* Segmented control: two mutually exclusive ways in. */
.roles-caption {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.78rem;
}
.roles {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  padding: 4px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
}
.role {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  /* Fixed height and a single line: the active state turns bold, which would
     otherwise re-wrap the other label and make it jump. */
  min-height: 38px;
  white-space: nowrap;
  padding: 8px 10px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--color-muted);
  font: inherit;
  font-size: 0.85rem;
  cursor: pointer;
  transition:
    background 0.18s ease,
    color 0.18s ease;
}
.role:hover {
  color: var(--color-text);
}
.role.active {
  background: var(--gradient);
  color: #06121a;
  font-weight: 700;
}
.role-icon {
  font-size: 1rem;
}
.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
/* Floating-label field: the label sits inside until the input has content. */
.field {
  position: relative;
}
.field input {
  width: 100%;
  min-width: 0;
  padding: 18px 14px 8px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}
.field input:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-soft);
}
.field label {
  position: absolute;
  left: 14px;
  top: 14px;
  color: var(--color-muted);
  font-size: 0.92rem;
  pointer-events: none;
  transition:
    top 0.15s ease,
    font-size 0.15s ease,
    color 0.15s ease;
}
.field input:focus + label,
.field input:not(:placeholder-shown) + label {
  top: 5px;
  font-size: 0.7rem;
  color: var(--color-accent);
  letter-spacing: 0.02em;
}
.error {
  margin: 0;
  color: var(--color-danger);
  font-size: 0.85rem;
}
.submit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  padding: 11px 18px;
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
.hint {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.76rem;
}
.login-enter-active,
.login-leave-active {
  transition: opacity 0.18s ease;
}
.login-enter-active .dialog,
.login-leave-active .dialog {
  transition: transform 0.18s cubic-bezier(0.22, 1, 0.36, 1);
}
.login-enter-from,
.login-leave-to {
  opacity: 0;
}
.login-enter-from .dialog,
.login-leave-to .dialog {
  transform: translateY(10px) scale(0.97);
}
@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation-duration: 2s;
  }
  .login-enter-active,
  .login-leave-active,
  .login-enter-active .dialog,
  .login-leave-active .dialog {
    transition: none;
  }
}
</style>
