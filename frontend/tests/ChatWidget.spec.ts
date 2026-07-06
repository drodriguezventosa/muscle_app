import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/chat', () => ({
  recommend: vi.fn().mockResolvedValue({ reply: '', exercises: [] }),
}))

import ChatWidget from '@/components/ChatWidget.vue'
import { i18n } from '@/i18n'

describe('ChatWidget', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('is collapsed by default and toggles the floating panel', async () => {
    const wrapper = mount(ChatWidget, { global: { plugins: [i18n] } })
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)

    await wrapper.get('[data-testid="chat-toggle"]').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)

    await wrapper.get('[data-testid="chat-close"]').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
  })
})
