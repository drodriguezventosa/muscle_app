import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Exercise } from '@/api/types'

const exercise: Exercise = {
  id: 1,
  name: 'Push-up',
  description: 'Bodyweight press.',
  equipment: 'bodyweight',
  difficulty: 'beginner',
  videoUrl: 'https://www.youtube.com/watch?v=WDIpL0pjun0',
  targetedMuscles: [{ muscleId: 5, role: 'primary' }],
}

vi.mock('@/api/chat', () => ({
  recommend: vi.fn().mockResolvedValue({ reply: 'Aquí tienes tus ejercicios', exercises: [] }),
}))

vi.mock('@/api/explorer', () => ({
  listMuscles: vi
    .fn()
    .mockResolvedValue([
      { id: 5, name: 'Pecho', muscleGroup: 'chest', svgId: 'chest', description: '' },
    ]),
  getMuscleExercises: vi.fn().mockResolvedValue([]),
}))

import { recommend } from '@/api/chat'
import ChatBot from '@/components/ChatBot.vue'
import { i18n } from '@/i18n'
import { useExplorerStore } from '@/stores/explorer'

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

  it('lets the user watch a suggested exercise video and jump to the explorer', async () => {
    vi.mocked(recommend).mockResolvedValueOnce({ reply: 'Prueba esto', exercises: [exercise] })
    const wrapper = mount(ChatBot, {
      global: { plugins: [i18n], stubs: { teleport: true } },
    })
    await wrapper.get('input').setValue('pecho')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    // "Watch example" opens the shared video modal inside the chat.
    await wrapper.get('.watch-mini').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)
    expect(wrapper.find('iframe').exists()).toBe(true)

    // Clicking the exercise name selects its primary muscle and asks to close the chat.
    await wrapper.get('.link').trigger('click')
    await flushPromises()
    const explorer = useExplorerStore()
    expect(explorer.selectedSvgId).toBe('chest')
    expect(wrapper.emitted('navigate')).toBeTruthy()
  })
})
