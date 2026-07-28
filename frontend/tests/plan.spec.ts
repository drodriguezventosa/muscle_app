import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

import WeekCalendar from '@/components/WeekCalendar.vue'
import { i18n } from '@/i18n'
import PlanView from '@/views/PlanView.vue'
import { memoryStorage } from './support/memory-storage'

const global = { plugins: [i18n] }

// Hoisted: `vi.mock` factories run before the imports above are evaluated.
const { myPlan, reportPlanItem } = vi.hoisted(() => ({
  myPlan: vi.fn(),
  reportPlanItem: vi.fn(),
}))
vi.mock('@/api/plan', () => ({ myPlan, reportPlanItem }))

const MONDAY = '2026-07-27'
const WEDNESDAY = '2026-07-29'

// The calendar is built around "today", so the clock is pinned: otherwise these
// tests would pass this week and fail the next.
beforeAll(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true })
  vi.setSystemTime(new Date(`${WEDNESDAY}T10:00:00`))
})
afterAll(() => vi.useRealTimers())

function item(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    exerciseId: 5,
    exerciseName: 'Sentadilla con barra',
    scheduledOn: WEDNESDAY,
    targetSets: 3,
    targetReps: 8,
    targetWeightKg: 100,
    notes: null,
    doneWeightKg: null,
    doneReps: null,
    status: 'pending' as const,
    ...overrides,
  }
}

describe('WeekCalendar', () => {
  it('shows seven days and selects the one that is clicked', async () => {
    const wrapper = mount(WeekCalendar, {
      props: { weekStart: MONDAY, selectedDay: MONDAY },
      global,
    })

    const days = wrapper.findAll('.strip .day')
    expect(days).toHaveLength(7)

    await days[3].trigger('click')
    expect(wrapper.emitted('update:selectedDay')?.[0]).toEqual(['2026-07-30'])
  })

  it('marks each scheduled exercise with a dot carrying its status', () => {
    const wrapper = mount(WeekCalendar, {
      props: {
        weekStart: MONDAY,
        selectedDay: MONDAY,
        marks: { [MONDAY]: ['done', 'partial', 'pending'] },
      },
      global,
    })

    const dots = wrapper.findAll('.strip .day')[0].findAll('.dot')
    expect(dots).toHaveLength(3)
    expect(dots[0].classes()).toContain('done')
    expect(dots[1].classes()).toContain('partial')
  })

  it('counts the extra ones instead of drawing a wall of dots', () => {
    const wrapper = mount(WeekCalendar, {
      props: {
        weekStart: MONDAY,
        selectedDay: MONDAY,
        marks: { [MONDAY]: ['done', 'done', 'done', 'done', 'done', 'done'] },
      },
      global,
    })

    const day = wrapper.findAll('.strip .day')[0]
    expect(day.findAll('.dot')).toHaveLength(4)
    expect(day.find('.extra').text()).toBe('+2')
  })

  it('moves a week at a time', async () => {
    const wrapper = mount(WeekCalendar, {
      props: { weekStart: MONDAY, selectedDay: MONDAY },
      global,
    })

    await wrapper.findAll('.nav')[1].trigger('click')
    expect(wrapper.emitted('update:weekStart')?.[0]).toEqual(['2026-08-03'])

    await wrapper.findAll('.nav')[0].trigger('click')
    expect(wrapper.emitted('update:weekStart')?.[1]).toEqual(['2026-07-20'])
  })
})

describe('PlanView', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', memoryStorage())
    setActivePinia(createPinia())
    myPlan.mockReset()
    reportPlanItem.mockReset()
  })

  it('summarises the week and lists the selected day', async () => {
    myPlan.mockResolvedValue([
      item({ id: 1, scheduledOn: MONDAY, status: 'done', doneWeightKg: 100, doneReps: 8 }),
      item({ id: 2 }),
      item({ id: 3, exerciseName: 'Curl con barra' }),
    ])

    const wrapper = mount(PlanView, { global })
    await flushPromises()

    expect(wrapper.text()).toContain('1/3')
    // The day shown is today's, which in the fixture holds two exercises.
    await wrapper.findAll('.strip .day')[2].trigger('click')
    expect(wrapper.findAll('.items .item')).toHaveLength(2)
  })

  it('reports what was lifted and shows the status that came back', async () => {
    myPlan.mockResolvedValue([item()])
    reportPlanItem.mockResolvedValue(item({ status: 'partial', doneWeightKg: 92.5, doneReps: 8 }))

    const wrapper = mount(PlanView, { global })
    await flushPromises()
    await wrapper.findAll('.strip .day')[2].trigger('click')

    await wrapper.find('.report-btn').trigger('click')
    await wrapper.find('.report input[type="number"]').setValue(92.5)
    await wrapper.find('form.report').trigger('submit')
    await flushPromises()

    // Reps come from the target: the student says the weight, not the maths.
    expect(reportPlanItem).toHaveBeenCalledWith(1, 92.5, 8, true)
    expect(wrapper.find('.badge').classes()).toContain('partial')
    expect(wrapper.text()).toContain('92.5')
  })

  it('says the day is a rest day rather than showing an empty box', async () => {
    myPlan.mockResolvedValue([item({ scheduledOn: MONDAY })])

    const wrapper = mount(PlanView, { global })
    await flushPromises()
    await wrapper.findAll('.strip .day')[5].trigger('click') // Saturday

    expect(wrapper.find('.items').exists()).toBe(false)
    expect(wrapper.find('.empty').exists()).toBe(true)
  })
})
