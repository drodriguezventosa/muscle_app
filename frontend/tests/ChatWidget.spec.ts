import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

vi.mock('@/api/chat', () => ({
  recommend: vi.fn().mockResolvedValue({ reply: '', exercises: [] }),
}))

// ChatWidget embeds ChatBot, which reads the current route, so a router is needed.
const router = createRouter({
  history: createMemoryHistory(),
  routes: [{ path: '/:pathMatch(.*)*', component: { template: '<div />' } }],
})

import ChatWidget from '@/components/ChatWidget.vue'
import { i18n } from '@/i18n'

describe('ChatWidget', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('is collapsed by default and toggles the floating panel', async () => {
    const wrapper = mount(ChatWidget, { global: { plugins: [i18n, router] } })
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)

    await wrapper.get('[data-testid="chat-toggle"]').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)

    await wrapper.get('[data-testid="chat-close"]').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
  })

  it('mirrors the current section on the closed bubble', async () => {
    await router.push('/nutrition')
    await flushPromises()
    const wrapper = mount(ChatWidget, { global: { plugins: [i18n, router] } })
    expect(wrapper.get('[data-testid="chat-toggle"]').text()).toContain('🍗')
  })
})
