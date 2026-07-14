<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Trainer } from '@/data/coaching'
import { useSubscriptionsStore } from '@/stores/subscriptions'

const props = defineProps<{ trainer: Trainer }>()
const emit = defineEmits<{ close: []; success: [] }>()

const { t, locale } = useI18n()
const subs = useSubscriptionsStore()

type Step = 'summary' | 'payment' | 'processing' | 'success' | 'declined'
const step = ref<Step>('summary')

// Well-known test cards (Stripe convention). This is a SIMULATION: nothing is
// sent anywhere and no real charge happens. The declined card demonstrates the
// gateway's error path.
const SUCCESS_CARD = '4242 4242 4242 4242'
const DECLINED_CARD = '4000 0000 0000 0002'

const card = reactive({
  name: 'DEMO USER',
  number: SUCCESS_CARD,
  expiry: '12 / 34',
  cvc: '123',
})

const receipt = ref<{ ref: string; date: string; next: string } | null>(null)

const onlyDigits = (value: string): string => value.replace(/\D/g, '')

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(locale.value, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function useTestCard(): void {
  card.name = 'DEMO USER'
  card.number = SUCCESS_CARD
  card.expiry = '12 / 34'
  card.cvc = '123'
}

function pay(): void {
  step.value = 'processing'
  // Simulated gateway latency — no network request, no real payment.
  globalThis.setTimeout(() => {
    if (onlyDigits(card.number) === onlyDigits(DECLINED_CARD)) {
      step.value = 'declined'
      return
    }
    const sub = subs.subscribe(props.trainer)
    const next = new Date(sub.startedAt)
    next.setMonth(next.getMonth() + 1)
    receipt.value = {
      ref: sub.paymentRef,
      date: formatDate(sub.startedAt),
      next: formatDate(next.toISOString()),
    }
    step.value = 'success'
    emit('success')
  }, 1600)
}
</script>

<template>
  <Teleport to="body">
    <div class="overlay" role="dialog" aria-modal="true" @click.self="emit('close')">
      <div class="checkout glass">
        <button type="button" class="x" :aria-label="t('checkout.close')" @click="emit('close')">
          ✕
        </button>

        <p class="demo-banner">🔒 {{ t('checkout.demoBanner') }}</p>

        <!-- Step 1: plan summary -->
        <template v-if="step === 'summary'">
          <h2>{{ t('checkout.title') }}</h2>
          <div class="plan">
            <span class="avatar" aria-hidden="true">{{ trainer.initials }}</span>
            <div>
              <p class="plan-name">{{ trainer.name }}</p>
              <p class="plan-goal">{{ t(`goal.${trainer.specialty}`) }}</p>
            </div>
            <p class="plan-price">
              {{ trainer.pricePerMonth }} €<span>{{ t('trainers.perMonth') }}</span>
            </p>
          </div>
          <ul class="includes">
            <li>{{ t('checkout.included1') }}</li>
            <li>{{ t('checkout.included2') }}</li>
            <li>{{ t('checkout.included3') }}</li>
          </ul>
          <button type="button" class="primary" @click="step = 'payment'">
            {{ t('checkout.continue') }}
          </button>
        </template>

        <!-- Step 2: simulated payment form -->
        <template v-else-if="step === 'payment'">
          <h2>{{ t('checkout.payTitle') }}</h2>
          <form class="card-form" @submit.prevent="pay">
            <label>
              {{ t('checkout.cardName') }}
              <input v-model="card.name" type="text" autocomplete="off" />
            </label>
            <label>
              {{ t('checkout.cardNumber') }}
              <input v-model="card.number" type="text" inputmode="numeric" autocomplete="off" />
            </label>
            <div class="row">
              <label>
                {{ t('checkout.cardExpiry') }}
                <input v-model="card.expiry" type="text" autocomplete="off" />
              </label>
              <label>
                {{ t('checkout.cardCvc') }}
                <input v-model="card.cvc" type="text" inputmode="numeric" autocomplete="off" />
              </label>
            </div>
            <p class="hint">
              {{ t('checkout.testHint') }}
              <button type="button" class="link" @click="useTestCard">
                {{ t('checkout.useTestCard') }}
              </button>
            </p>
            <button type="submit" class="primary">
              {{ t('checkout.payButton', { price: trainer.pricePerMonth }) }}
            </button>
          </form>
        </template>

        <!-- Step 3: processing -->
        <template v-else-if="step === 'processing'">
          <div class="center">
            <span class="spinner" aria-hidden="true"></span>
            <p>{{ t('checkout.processing') }}</p>
          </div>
        </template>

        <!-- Step 4: success + receipt -->
        <template v-else-if="step === 'success'">
          <div class="center">
            <span class="tick" aria-hidden="true">✓</span>
            <h2>{{ t('checkout.successTitle') }}</h2>
            <p>{{ t('checkout.successBody', { name: trainer.name }) }}</p>
          </div>
          <dl v-if="receipt" class="receipt">
            <div>
              <dt>{{ t('checkout.amount') }}</dt>
              <dd>{{ trainer.pricePerMonth }} €{{ t('trainers.perMonth') }}</dd>
            </div>
            <div>
              <dt>{{ t('checkout.receiptRef') }}</dt>
              <dd>{{ receipt.ref }}</dd>
            </div>
            <div>
              <dt>{{ t('checkout.receiptDate') }}</dt>
              <dd>{{ receipt.date }}</dd>
            </div>
            <div>
              <dt>{{ t('checkout.receiptNext') }}</dt>
              <dd>{{ receipt.next }}</dd>
            </div>
          </dl>
          <button type="button" class="primary" @click="emit('close')">
            {{ t('checkout.done') }}
          </button>
        </template>

        <!-- Step 5: declined -->
        <template v-else>
          <div class="center">
            <span class="cross" aria-hidden="true">✕</span>
            <h2>{{ t('checkout.declinedTitle') }}</h2>
            <p>{{ t('checkout.declinedBody') }}</p>
          </div>
          <button type="button" class="primary" @click="((step = 'payment'), useTestCard())">
            {{ t('checkout.retry') }}
          </button>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
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
.checkout {
  position: relative;
  width: 100%;
  max-width: 420px;
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.x {
  position: absolute;
  top: var(--space-sm);
  right: var(--space-sm);
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: var(--color-surface);
  color: var(--color-muted);
  cursor: pointer;
}
.demo-banner {
  margin: 0;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-size: 0.78rem;
  font-weight: 600;
  text-align: center;
}
h2 {
  margin: 0;
  font-size: 1.25rem;
}
.plan {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}
.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--gradient);
  color: #061018;
  font-weight: 800;
}
.plan-name {
  margin: 0;
  font-weight: 700;
}
.plan-goal {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.85rem;
}
.plan-price {
  margin: 0;
  font-weight: 800;
  font-size: 1.15rem;
}
.plan-price span {
  font-size: 0.75rem;
  color: var(--color-muted);
  font-weight: 600;
}
.includes {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--color-muted);
  font-size: 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.card-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.card-form label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.8rem;
  color: var(--color-muted);
  min-width: 0; /* let grid/flex items shrink below the input's intrinsic size */
}
.card-form input {
  width: 100%;
  min-width: 0; /* otherwise the Expiry/CVC inputs overflow the modal on mobile */
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-input);
  color: var(--color-text);
  font-size: 0.95rem;
}
.card-form input:focus {
  outline: none;
  border-color: var(--color-accent);
}
.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-sm);
}
.hint {
  margin: 0;
  font-size: 0.78rem;
  color: var(--color-muted);
}
.link {
  border: none;
  background: none;
  padding: 0;
  color: var(--color-accent);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
.primary {
  padding: 12px 16px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--gradient);
  color: #061018;
  font-weight: 700;
  cursor: pointer;
}
.center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  text-align: center;
  padding: var(--space-sm) 0;
}
.spinner {
  width: 38px;
  height: 38px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.tick,
.cross {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  font-size: 1.5rem;
  font-weight: 800;
}
.tick {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}
.cross {
  background: rgba(251, 113, 133, 0.15);
  color: var(--color-danger);
}
.receipt {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: var(--space-md);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}
.receipt div {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
}
.receipt dt {
  color: var(--color-muted);
}
.receipt dd {
  margin: 0;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
  }
}
</style>
