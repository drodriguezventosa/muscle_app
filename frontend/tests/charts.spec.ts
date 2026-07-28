import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import BarChart from '@/components/charts/BarChart.vue'
import LineChart from '@/components/charts/LineChart.vue'
import ScatterChart from '@/components/charts/ScatterChart.vue'
import { i18n } from '@/i18n'

const global = { plugins: [i18n] }

const STRENGTH = [
  {
    key: 1,
    name: 'Sentadilla con barra',
    color: 'var(--series-1)',
    points: [
      { on: '2026-05-11', value: 100 },
      { on: '2026-06-11', value: 110 },
      { on: '2026-07-11', value: 120 },
    ],
  },
  {
    key: 2,
    name: 'Press de banca',
    color: 'var(--series-2)',
    points: [
      { on: '2026-05-11', value: 60 },
      { on: '2026-07-11', value: 70 },
    ],
  },
]

describe('LineChart', () => {
  it('draws one line per series and lists them in the legend', () => {
    const wrapper = mount(LineChart, { props: { series: STRENGTH, unit: 'kg' }, global })

    expect(wrapper.findAll('path.line')).toHaveLength(2)
    expect(wrapper.findAll('.legend-item')).toHaveLength(2)
    expect(wrapper.text()).toContain('Sentadilla con barra')
  })

  it('drops the legend for a single series: the card title already names it', () => {
    const wrapper = mount(LineChart, { props: { series: [STRENGTH[0]] }, global })

    expect(wrapper.find('.legend').exists()).toBe(false)
    expect(wrapper.findAll('path.line')).toHaveLength(1)
  })

  it('keeps every plotted value reachable in the table view', () => {
    const wrapper = mount(LineChart, { props: { series: STRENGTH, unit: 'kg' }, global })

    // Three distinct days across both series, one row each.
    expect(wrapper.findAll('tbody tr')).toHaveLength(3)
    expect(wrapper.find('tbody').text()).toContain('120 kg')
    // A series with no point that day is a dash, never an invented value.
    expect(wrapper.find('tbody').text()).toContain('—')
  })

  it('shows a reading for every series when the crosshair moves', async () => {
    const wrapper = mount(LineChart, { props: { series: STRENGTH, unit: 'kg' }, global })

    await wrapper.find('svg').trigger('keydown', { key: 'ArrowRight' })

    const tooltip = wrapper.find('.tooltip')
    expect(tooltip.exists()).toBe(true)
    expect(tooltip.text()).toContain('100 kg')
    expect(tooltip.text()).toContain('60 kg')
  })
})

describe('BarChart', () => {
  const BARS = [
    { label: '11 may', title: 'Semana del 11 may 2026', value: 3 },
    { label: '18 may', title: 'Semana del 18 may 2026', value: 0 },
  ]

  it('draws one bar per week and keeps a zero week visible', () => {
    const wrapper = mount(BarChart, { props: { bars: BARS }, global })

    expect(wrapper.findAll('rect.bar.zero')).toHaveLength(1)
    expect(wrapper.findAll('rect.hit')).toHaveLength(2)
  })

  it('labels each bar for screen readers and lists the values', () => {
    const wrapper = mount(BarChart, { props: { bars: BARS }, global })

    expect(wrapper.find('rect.hit').attributes('aria-label')).toBe('Semana del 11 may 2026: 3')
    expect(wrapper.findAll('tbody tr')).toHaveLength(2)
  })
})

describe('ScatterChart', () => {
  const POINTS = [
    {
      key: 1,
      initials: 'JM',
      name: 'Javier M.',
      x: 29,
      y: 24.6,
      group: 'hypertrophy',
      groupLabel: 'Hipertrofia',
      color: 'var(--series-2)',
    },
    {
      key: 2,
      initials: 'LP',
      name: 'Lucía P.',
      x: 34,
      y: 26.4,
      group: 'fat_loss',
      groupLabel: 'Pérdida de grasa',
      color: 'var(--series-1)',
    },
    {
      key: 3,
      initials: 'MS',
      name: 'Marta S.',
      x: 25,
      y: 21.1,
      group: 'hypertrophy',
      groupLabel: 'Hipertrofia',
      color: 'var(--series-2)',
    },
  ]

  it('labels every dot, so identity never depends on colour alone', () => {
    const wrapper = mount(ScatterChart, {
      props: { points: POINTS, xLabel: 'Edad', yLabel: 'IMC' },
      global,
    })

    expect(wrapper.findAll('circle.dot')).toHaveLength(3)
    expect(wrapper.findAll('text.initials').map((n) => n.text())).toEqual(['JM', 'LP', 'MS'])
  })

  it('shows one legend entry per group, not per point', () => {
    const wrapper = mount(ScatterChart, {
      props: { points: POINTS, xLabel: 'Edad', yLabel: 'IMC' },
      global,
    })

    expect(wrapper.findAll('.legend-item')).toHaveLength(2)
  })

  it('draws the reference band only when one is given', () => {
    const plain = mount(ScatterChart, {
      props: { points: POINTS, xLabel: 'Edad', yLabel: 'IMC' },
      global,
    })
    const banded = mount(ScatterChart, {
      props: {
        points: POINTS,
        xLabel: 'Edad',
        yLabel: 'IMC',
        yBand: [18.5, 25] as [number, number],
        yBandLabel: 'IMC saludable',
      },
      global,
    })

    expect(plain.find('rect.band').exists()).toBe(false)
    expect(banded.find('rect.band').exists()).toBe(true)
    expect(banded.text()).toContain('IMC saludable')
  })
})
