import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

// vi.mock is hoisted, so the spy must be created with vi.hoisted to exist by then.
const { analyzeMealPhoto } = vi.hoisted(() => ({ analyzeMealPhoto: vi.fn() }))

vi.mock('@/api/nutrition', () => ({
  calculateNutrition: vi.fn(),
  listFoods: vi.fn().mockResolvedValue([]),
  analyzeMealPhoto,
}))

import NutritionView from '@/views/NutritionView.vue'
import { i18n } from '@/i18n'

describe('NutritionView meal photo', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    analyzeMealPhoto.mockReset()
  })

  it('adds photo-estimated foods as editable menu items with per-100 g macros', async () => {
    // The API returns TOTALS for the estimated grams; the menu stores per-100 g so
    // that editing the grams rescales the macros like any catalog food.
    analyzeMealPhoto.mockResolvedValue({
      note: 'Estimación aproximada',
      available: true,
      items: [{ name: 'huevo frito', grams: 50, kcal: 90, proteinG: 6, carbsG: 0.5, fatG: 7 }],
    })
    const wrapper = mount(NutritionView, { global: { plugins: [i18n] } })
    await flushPromises()

    wrapper.getComponent({ name: 'MealPhotoCapture' }).vm.$emit('captured', new Blob(['x']))
    await flushPromises()

    // Shown in the menu with the estimated portion...
    const row = wrapper.get('.menu-item')
    expect(row.text()).toContain('huevo frito')
    expect((row.get('input[type="number"]').element as HTMLInputElement).value).toBe('50')
    // ...and its kcal for that portion match the estimate (90 for 50 g).
    expect(row.get('.mi-kcal').text()).toContain('90')
    expect(wrapper.text()).toContain('Estimación aproximada')

    // Doubling the grams doubles the calories (per-100 g conversion is correct).
    await row.get('input[type="number"]').setValue(100)
    expect(wrapper.get('.menu-item .mi-kcal').text()).toContain('180')
  })

  it('shows an error message when the analysis fails', async () => {
    analyzeMealPhoto.mockRejectedValue(new Error('boom'))
    const wrapper = mount(NutritionView, { global: { plugins: [i18n] } })
    await flushPromises()

    wrapper.getComponent({ name: 'MealPhotoCapture' }).vm.$emit('captured', new Blob(['x']))
    await flushPromises()

    expect(wrapper.find('.photo-msg.error').exists()).toBe(true)
    expect(wrapper.find('.menu-item').exists()).toBe(false)
  })
})
