import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/nutrition', () => ({
  calculateNutrition: vi.fn().mockResolvedValue({
    bmr: 1700,
    tdee: 2600,
    calories: 2400,
    proteinG: 140,
    carbsG: 300,
    fatG: 70,
    bmi: 24,
    bmiCategory: 'normal',
    goal: 'maintain',
    warning: null,
  }),
  listFoods: vi.fn().mockResolvedValue([
    {
      id: 1,
      name: 'Olive oil',
      category: 'fats',
      kcal: 884,
      proteinG: 0,
      carbsG: 0,
      fatG: 100,
      emoji: '🫒',
      tags: [],
    },
  ]),
}))

import NutritionView from '@/views/NutritionView.vue'
import { i18n } from '@/i18n'
import { useNutritionStore } from '@/stores/nutrition'

describe('NutritionView macro progress', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('shows each macro as current/target with a percentage of the goal', async () => {
    const wrapper = mount(NutritionView, { global: { plugins: [i18n] } })
    await flushPromises() // loadFoods populates the catalog

    // Calculate targets (mocked), then add 100 g of olive oil (= 100 g fat).
    const store = useNutritionStore()
    store.age = 30
    store.heightCm = 178
    store.weightKg = 78
    await store.calculate()
    await flushPromises()

    await wrapper.get('.foods .food').trigger('click')
    await flushPromises()

    const rows = wrapper.findAll('.mp-row').map((r) => r.text().replace(/\s+/g, ' '))
    expect(rows).toHaveLength(3)
    // Fat: 100 g of 70 g target -> 143%.
    expect(rows.some((t) => /100 \/ 70 g/.test(t) && /143%/.test(t))).toBe(true)
    // Protein contributes nothing here -> 0 of 140 -> 0%.
    expect(rows.some((t) => /0 \/ 140 g/.test(t) && /0%/.test(t))).toBe(true)
  })
})
