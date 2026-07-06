import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type { Muscle } from '@/api/types'
import BodyMap from '@/components/BodyMap.vue'

const muscles: Muscle[] = [
  { id: 1, name: 'Pectoralis major', muscleGroup: 'chest', svgId: 'chest', description: '' },
  { id: 2, name: 'Biceps brachii', muscleGroup: 'arms', svgId: 'biceps', description: '' },
]

describe('BodyMap', () => {
  it('renders one interactive region per available muscle', () => {
    const wrapper = mount(BodyMap, { props: { muscles, selected: null } })
    // Only the two provided muscles should be clickable, not all layout regions.
    expect(wrapper.findAll('[role="button"]')).toHaveLength(2)
  })

  it('labels regions with the muscle name (accessibility)', () => {
    const wrapper = mount(BodyMap, { props: { muscles, selected: null } })
    const labels = wrapper.findAll('[role="button"]').map((n) => n.attributes('aria-label'))
    expect(labels).toContain('Pectoralis major')
  })

  it('emits select with the svg id when a region is clicked', async () => {
    const wrapper = mount(BodyMap, { props: { muscles, selected: null } })
    await wrapper.get('[role="button"]').trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')?.[0]).toEqual(['chest'])
  })

  it('marks the selected region as pressed', () => {
    const wrapper = mount(BodyMap, { props: { muscles, selected: 'biceps' } })
    const pressed = wrapper
      .findAll('[role="button"]')
      .filter((n) => n.attributes('aria-pressed') === 'true')
    expect(pressed).toHaveLength(1)
    expect(pressed[0].attributes('aria-label')).toBe('Biceps brachii')
  })
})
