import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type { Exercise } from '@/api/types'
import ExercisePanel from '@/components/ExercisePanel.vue'
// Raw SFC source, used to assert a CSS invariant jsdom can't observe.
import exercisePanelSource from '@/components/ExercisePanel.vue?raw'
import { i18n } from '@/i18n'

const exercise: Exercise = {
  id: 1,
  name: 'Flexiones',
  description: 'desc',
  equipment: 'bodyweight',
  difficulty: 'beginner',
  videoUrl: 'https://www.youtube.com/watch?v=WDIpL0pjun0',
  targetedMuscles: [],
}

describe('ExercisePanel', () => {
  it('opens the video modal when "watch example" is clicked', async () => {
    const wrapper = mount(ExercisePanel, {
      props: { muscleName: 'Pecho', exercises: [exercise], loading: false, error: null },
      global: { plugins: [i18n], stubs: { teleport: true } },
    })
    expect(wrapper.find('.watch').exists()).toBe(true)
    await wrapper.get('.watch').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)
    expect(wrapper.find('iframe').exists()).toBe(true)
  })

  // Regression guard: the decorative `.card::before` gradient overlay is
  // absolutely positioned over the whole card, so without `pointer-events: none`
  // it swallows real mouse clicks on the "watch" button (jsdom can't catch this
  // because it does no layout/hit-testing — trigger('click') dispatches directly).
  it('keeps the decorative card overlay click-through', () => {
    const overlayRule = exercisePanelSource.slice(exercisePanelSource.indexOf('.card::before'))
    expect(overlayRule.slice(0, overlayRule.indexOf('}'))).toMatch(/pointer-events:\s*none/)
  })
})
