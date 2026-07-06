import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/chat', () => ({
  recommend: vi.fn().mockResolvedValue({ reply: '', exercises: [] }),
}))

import ChatWidget from '@/components/ChatWidget.vue'

describe('ChatWidget', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('is collapsed by default and toggles the floating panel', async () => {
    const wrapper = mount(ChatWidget)
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)

    await wrapper.get('button[aria-label="Abrir asistente de recomendaciones"]').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)

    await wrapper.get('.close').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
  })
})
