import { defineStore } from 'pinia'
import { ref } from 'vue'

// Demo-only: active trainer subscriptions from the SIMULATED payment flow. There
// is no real charge and no card data is ever stored — only a fake payment
// reference, mirroring the future backend `PaymentPort` (mock → Stripe). Persisted
// in localStorage so the mockup keeps state; no backend, no accounts (ADR-0006/0012).

export interface Subscription {
  trainerId: number
  trainerName: string
  pricePerMonth: number
  paymentRef: string // fake reference, e.g. "SIM-Lš2K-000123"
  startedAt: string // ISO date
}

const KEY = 'muscleapp:subscriptions'

function load(): Record<number, Subscription> {
  try {
    const raw = globalThis.localStorage?.getItem(KEY)
    if (raw) return JSON.parse(raw) as Record<number, Subscription>
  } catch {
    // ignore malformed storage
  }
  return {}
}

export const useSubscriptionsStore = defineStore('subscriptions', () => {
  const active = ref<Record<number, Subscription>>(load())

  function persist(): void {
    globalThis.localStorage?.setItem(KEY, JSON.stringify(active.value))
  }

  function isActive(trainerId: number): boolean {
    return trainerId in active.value
  }

  function get(trainerId: number): Subscription | undefined {
    return active.value[trainerId]
  }

  function list(): Subscription[] {
    return Object.values(active.value)
  }

  // Records a subscription with a generated fake payment reference. Called only
  // after the simulated gateway "approves" — no real payment is processed.
  function subscribe(trainer: { id: number; name: string; pricePerMonth: number }): Subscription {
    const rand = Math.floor(Math.random() * 1e6)
      .toString()
      .padStart(6, '0')
    const sub: Subscription = {
      trainerId: trainer.id,
      trainerName: trainer.name,
      pricePerMonth: trainer.pricePerMonth,
      paymentRef: `SIM-${Date.now().toString(36).toUpperCase()}-${rand}`,
      startedAt: new Date().toISOString(),
    }
    active.value = { ...active.value, [trainer.id]: sub }
    persist()
    return sub
  }

  function cancel(trainerId: number): void {
    const next = { ...active.value }
    delete next[trainerId]
    active.value = next
    persist()
  }

  return { active, isActive, get, list, subscribe, cancel }
})
