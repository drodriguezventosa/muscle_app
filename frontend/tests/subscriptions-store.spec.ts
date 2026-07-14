import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { useSubscriptionsStore } from '@/stores/subscriptions'

describe('subscriptions store (simulated payments)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    globalThis.localStorage?.clear()
  })

  it('subscribe marks the trainer active with a fake payment reference', () => {
    const store = useSubscriptionsStore()
    expect(store.isActive(1)).toBe(false)

    const sub = store.subscribe({ id: 1, name: 'Ana López', pricePerMonth: 39 })

    expect(store.isActive(1)).toBe(true)
    expect(sub.paymentRef).toMatch(/^SIM-/) // simulated, never a real charge
    expect(store.get(1)?.pricePerMonth).toBe(39)
    expect(store.list()).toHaveLength(1)
  })

  it('cancel removes the subscription', () => {
    const store = useSubscriptionsStore()
    store.subscribe({ id: 2, name: 'Marco Ruiz', pricePerMonth: 45 })
    expect(store.isActive(2)).toBe(true)

    store.cancel(2)

    expect(store.isActive(2)).toBe(false)
    expect(store.list()).toHaveLength(0)
  })
})
