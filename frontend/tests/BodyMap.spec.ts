import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type { Muscle } from '@/api/types'
import BodyMap from '@/components/BodyMap.vue'
import { i18n } from '@/i18n'

const muscles: Muscle[] = [
  { id: 1, name: 'Pectoralis major', muscleGroup: 'chest', svgId: 'chest', description: '' },
  { id: 2, name: 'Biceps brachii', muscleGroup: 'arms', svgId: 'biceps', description: '' },
  { id: 3, name: 'Triceps brachii', muscleGroup: 'arms', svgId: 'triceps', description: '' },
]

function mountMap(overrides: Partial<InstanceType<typeof BodyMap>['$props']> = {}) {
  return mount(BodyMap, {
    props: {
      muscles,
      selected: null,
      activeSvgIds: ['chest', 'biceps', 'triceps'],
      view: 'both' as const,
      ...overrides,
    },
    global: { plugins: [i18n], stubs: { teleport: true } },
  })
}

function labels(wrapper: ReturnType<typeof mountMap>): string[] {
  return wrapper.findAll('[role="button"]').map((n) => n.attributes('aria-label') ?? '')
}

describe('BodyMap', () => {
  it('renders a clickable region per active muscle group', () => {
    const wrapper = mountMap()
    // Chest (front) plus Arms (front biceps + back triceps region).
    expect(labels(wrapper)).toContain('Chest')
    expect(labels(wrapper)).toContain('Arms')
  })

  it('selects directly when the group has a single active muscle', async () => {
    const wrapper = mountMap()
    const chest = wrapper.findAll('[role="button"]').find((n) => n.attributes('aria-label') === 'Chest')
    await chest!.trigger('click')
    expect(wrapper.emitted('select')?.[0]).toEqual(['chest'])
    expect(wrapper.find('.popup').exists()).toBe(false)
  })

  it('opens a popup to choose a muscle when the group has several', async () => {
    const wrapper = mountMap()
    const arms = wrapper.findAll('[role="button"]').find((n) => n.attributes('aria-label') === 'Arms')
    await arms!.trigger('click')
    const popup = wrapper.find('.popup')
    expect(popup.exists()).toBe(true)
    const items = popup.findAll('.popup-item')
    expect(items.map((i) => i.text())).toEqual(['Biceps brachii', 'Triceps brachii'])

    await items[1].trigger('click')
    expect(wrapper.emitted('select')?.[0]).toEqual(['triceps'])
  })

  it('hides groups whose muscles have no matching exercises', () => {
    const wrapper = mountMap({ activeSvgIds: ['chest'] })
    expect(labels(wrapper)).toEqual(['Chest'])
  })

  it('marks the selected group as pressed', () => {
    const wrapper = mountMap({ selected: 'chest' })
    const pressed = wrapper
      .findAll('[role="button"]')
      .filter((n) => n.attributes('aria-pressed') === 'true')
      .map((n) => n.attributes('aria-label'))
    expect(pressed).toEqual(['Chest'])
  })
})
