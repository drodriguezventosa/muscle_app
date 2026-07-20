import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter, type Router } from 'vue-router'

import GuidedTour, { type TourStep } from '@/components/GuidedTour.vue'
import { i18n } from '@/i18n'

const steps: TourStep[] = [
  { route: '/', titleKey: 'tour.steps.welcome.title', bodyKey: 'tour.steps.welcome.body' },
  {
    route: '/workouts',
    target: '[data-tour="main"]',
    titleKey: 'tour.steps.workouts.title',
    bodyKey: 'tour.steps.workouts.body',
  },
  { titleKey: 'tour.steps.done.title', bodyKey: 'tour.steps.done.body' },
]

function makeRouter(): Router {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/workouts', component: { template: '<div />' } },
      { path: '/nutrition', component: { template: '<div />' } },
    ],
  })
}

async function openTour(router: Router) {
  const wrapper = mount(GuidedTour, {
    props: { modelValue: false, steps },
    global: { plugins: [i18n, router], stubs: { teleport: true } },
  })
  // The tour initializes on the false -> true transition (as in the real app).
  await wrapper.setProps({ modelValue: true })
  await flushPromises()
  return wrapper
}

describe('GuidedTour', () => {
  it('walks the steps, navigating to each step route', async () => {
    const router = makeRouter()
    router.push('/nutrition')
    await router.isReady()

    const wrapper = await openTour(router)
    expect(wrapper.find('.tour-tip').exists()).toBe(true)
    expect(wrapper.find('.tour-step-count').text()).toBe('1 / 3')
    // Opening navigated to the first step's route.
    expect(router.currentRoute.value.path).toBe('/')

    await wrapper.get('.tour-btn.primary').trigger('click')
    await flushPromises()
    expect(wrapper.find('.tour-step-count').text()).toBe('2 / 3')
    expect(router.currentRoute.value.path).toBe('/workouts')
  })

  it('does not close when the backdrop is clicked', async () => {
    const router = makeRouter()
    const wrapper = await openTour(router)

    await wrapper.get('.tour-catch').trigger('click')
    await flushPromises()
    expect(wrapper.emitted('finish')).toBeFalsy()
    expect(wrapper.find('.tour-tip').exists()).toBe(true)
  })

  it('finishes on the last step and reports the "don\'t show again" choice', async () => {
    const router = makeRouter()
    const wrapper = await openTour(router)

    await wrapper.get('.tour-btn.primary').trigger('click') // -> 2
    await flushPromises()
    await wrapper.get('.tour-btn.primary').trigger('click') // -> 3 (last)
    await flushPromises()
    expect(wrapper.find('.tour-step-count').text()).toBe('3 / 3')

    await wrapper.get('.tour-btn.primary').trigger('click') // finish
    expect(wrapper.emitted('finish')?.[0]).toEqual([true])
    expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual([false])
  })

  it('reports false when the user unchecks "don\'t show again"', async () => {
    const router = makeRouter()
    const wrapper = await openTour(router)

    await wrapper.get('.tour-remember input').setValue(false)
    await wrapper.get('.tour-skip').trigger('click')
    expect(wrapper.emitted('finish')?.[0]).toEqual([false])
  })
})
