import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import MealPhotoCapture from '@/components/MealPhotoCapture.vue'
import { i18n } from '@/i18n'

function mountCapture() {
  return mount(MealPhotoCapture, {
    props: { busy: false },
    global: { plugins: [i18n], stubs: { teleport: true } },
  })
}

describe('MealPhotoCapture', () => {
  it('shows the busy spinner on the upload button when the photo came from a file', async () => {
    const wrapper = mountCapture()
    const [cameraBtn, uploadBtn] = wrapper.findAll('.cap-btn')

    // Simulate picking a file, then the parent starting the analysis.
    const input = wrapper.get('input[type="file"]')
    const file = new File(['x'], 'meal.jpg', { type: 'image/jpeg' })
    Object.defineProperty(input.element, 'files', { value: [file], configurable: true })
    await input.trigger('change')
    expect(wrapper.emitted('captured')).toBeTruthy()

    await wrapper.setProps({ busy: true })

    expect(uploadBtn.find('.cap-spinner').exists()).toBe(true)
    expect(cameraBtn.find('.cap-spinner').exists()).toBe(false)
    // Both stay disabled so a second photo cannot be sent meanwhile.
    expect(cameraBtn.attributes('disabled')).toBeDefined()
    expect(uploadBtn.attributes('disabled')).toBeDefined()
  })

  it('does not show any spinner before a photo is taken', async () => {
    const wrapper = mountCapture()
    await wrapper.setProps({ busy: true })
    expect(wrapper.find('.cap-spinner').exists()).toBe(false)
  })
})
