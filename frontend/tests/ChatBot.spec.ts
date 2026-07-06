import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/chat', () => ({
  recommend: vi.fn().mockResolvedValue({ reply: 'Aquí tienes tus ejercicios', exercises: [] }),
}))

import ChatBot from '@/components/ChatBot.vue'
import { i18n } from '@/i18n'

describe('ChatBot', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('sends the query and renders both the question and the reply', async () => {
    const wrapper = mount(ChatBot, { global: { plugins: [i18n] } })
    await wrapper.get('input').setValue('quiero entrenar pecho')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('quiero entrenar pecho')
    expect(wrapper.text()).toContain('Aquí tienes tus ejercicios')
  })
})
