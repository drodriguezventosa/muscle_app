<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useElementWidth } from '@/composables/useElementWidth'

export interface LinePoint {
  /** ISO day (YYYY-MM-DD): the x scale is time, not the index. */
  on: string
  value: number
}

export interface LineSeries {
  key: string | number
  name: string
  /** Categorical slot, assigned by entity so filtering never repaints it. */
  color: string
  points: LinePoint[]
}

const props = withDefaults(
  defineProps<{
    series: LineSeries[]
    unit?: string
    height?: number
    /** A soft wash under a single series; off for multi-series (it would muddy). */
    area?: boolean
    decimals?: number
  }>(),
  { unit: '', height: 220, area: false, decimals: 1 },
)

const { t, locale } = useI18n()

const wrapper = ref<HTMLElement | null>(null)
const width = useElementWidth(wrapper)

// Room for the y labels on the left and the direct series labels on the right.
const PAD = { top: 14, bottom: 26, left: 44 }
const LABEL_LINE_HEIGHT = 14
// Rough advance width of the label font: enough to decide how many characters
// fit, so a long exercise name is shortened deliberately instead of clipped.
const LABEL_CHAR_WIDTH = 5.6

// Below this width a truncated end label says less than the legend already
// does, so the plot takes the space instead.
const MIN_WIDTH_FOR_END_LABELS = 420

const showEndLabels = computed(
  () => props.series.length > 1 && width.value >= MIN_WIDTH_FOR_END_LABELS,
)

/** Gutter reserved for the end labels — a share of the width, within reason. */
const labelWidth = computed(() =>
  showEndLabels.value ? Math.min(150, Math.max(64, width.value * 0.26)) : 12,
)
const padRight = computed(() => labelWidth.value + 10)

function shorten(name: string): string {
  const max = Math.floor(labelWidth.value / LABEL_CHAR_WIDTH)
  return name.length > max ? `${name.slice(0, max - 1).trimEnd()}…` : name
}

const plotWidth = computed(() => Math.max(80, width.value - PAD.left - padRight.value))
const plotHeight = computed(() => Math.max(60, props.height - PAD.top - PAD.bottom))

function toTime(day: string): number {
  return new Date(`${day}T00:00:00`).getTime()
}

const allPoints = computed(() => props.series.flatMap((s) => s.points))

const xDomain = computed<[number, number]>(() => {
  const times = allPoints.value.map((p) => toTime(p.on))
  const min = Math.min(...times)
  const max = Math.max(...times)
  // A single day would divide by zero; give it a nominal width instead.
  return min === max ? [min - 86_400_000, max + 86_400_000] : [min, max]
})

const yDomain = computed<[number, number]>(() => {
  const values = allPoints.value.map((p) => p.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  if (min === max) return [min - 1, max + 1]
  // A little headroom so the extremes do not touch the frame.
  const margin = (max - min) * 0.12
  return [min - margin, max + margin]
})

function x(day: string): number {
  const [from, to] = xDomain.value
  return PAD.left + ((toTime(day) - from) / (to - from)) * plotWidth.value
}

function y(value: number): number {
  const [min, max] = yDomain.value
  return PAD.top + plotHeight.value - ((value - min) / (max - min)) * plotHeight.value
}

function path(points: LinePoint[]): string {
  return points.map((p, i) => `${i ? 'L' : 'M'}${x(p.on)},${y(p.value)}`).join(' ')
}

function areaPath(points: LinePoint[]): string {
  if (!points.length) return ''
  const base = PAD.top + plotHeight.value
  return `${path(points)} L${x(points[points.length - 1].on)},${base} L${x(points[0].on)},${base} Z`
}

/** Y ticks on round numbers (…5, 10, 25…) rather than raw domain fractions. */
const yTicks = computed(() => {
  const [min, max] = yDomain.value
  const rough = (max - min) / 3
  const magnitude = 10 ** Math.floor(Math.log10(rough))
  const step =
    [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= rough) ?? magnitude * 10
  const ticks: number[] = []
  for (let value = Math.ceil(min / step) * step; value <= max; value += step) {
    ticks.push(Number(value.toFixed(2)))
  }
  return ticks
})

const xTicks = computed(() => {
  const days = [...new Set(allPoints.value.map((p) => p.on))].sort()
  if (days.length <= 3) return days
  return [days[0], days[Math.floor(days.length / 2)], days[days.length - 1]]
})

function formatValue(value: number): string {
  const rounded = Number(value.toFixed(props.decimals))
  return props.unit ? `${rounded} ${props.unit}` : String(rounded)
}

function formatDay(day: string): string {
  return new Date(`${day}T00:00:00`).toLocaleDateString(locale.value, {
    day: 'numeric',
    month: 'short',
  })
}

/**
 * End labels, pushed apart when series converge.
 *
 * Stacking labels detaches them from their line, so each keeps a leader line
 * back to its own endpoint (see the dataviz guidance on converging series).
 */
const endLabels = computed(() => {
  const labels = props.series
    .filter((s) => s.points.length)
    .map((s) => {
      const last = s.points[s.points.length - 1]
      return {
        key: s.key,
        name: shorten(s.name),
        color: s.color,
        anchor: y(last.value),
        at: y(last.value),
      }
    })
    .sort((a, b) => a.anchor - b.anchor)

  for (let i = 1; i < labels.length; i += 1) {
    const gap = labels[i].at - labels[i - 1].at
    if (gap < LABEL_LINE_HEIGHT) labels[i].at = labels[i - 1].at + LABEL_LINE_HEIGHT
  }
  return labels
})

// -- hover / focus ---------------------------------------------------------

/** Every x present in any series, so the crosshair can snap to a real day. */
const days = computed(() => [...new Set(allPoints.value.map((p) => p.on))].sort())
const activeIndex = ref<number | null>(null)

const active = computed(() => {
  if (activeIndex.value === null) return null
  const day = days.value[activeIndex.value]
  const rows = props.series
    .map((s) => ({ series: s, point: s.points.find((p) => p.on === day) }))
    .filter((row): row is { series: LineSeries; point: LinePoint } => Boolean(row.point))
  return rows.length ? { day, rows, at: x(day) } : null
})

function nearestIndex(clientX: number): number {
  const box = wrapper.value?.getBoundingClientRect()
  if (!box) return 0
  const target = clientX - box.left
  let best = 0
  days.value.forEach((day, index) => {
    if (Math.abs(x(day) - target) < Math.abs(x(days.value[best]) - target)) best = index
  })
  return best
}

function onPointerMove(event: PointerEvent): void {
  activeIndex.value = nearestIndex(event.clientX)
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
  event.preventDefault()
  const step = event.key === 'ArrowRight' ? 1 : -1
  const current = activeIndex.value ?? (step > 0 ? -1 : days.value.length)
  activeIndex.value = Math.min(days.value.length - 1, Math.max(0, current + step))
}

/** Keep the tooltip inside the card instead of letting it spill off the edge. */
const tooltipStyle = computed(() => {
  if (!active.value) return {}
  const flip = active.value.at > width.value * 0.6
  return {
    left: `${active.value.at}px`,
    transform: flip ? 'translateX(-100%) translateX(-10px)' : 'translateX(10px)',
  }
})
</script>

<template>
  <figure ref="wrapper" class="chart">
    <svg
      :width="width"
      :height="height"
      :viewBox="`0 0 ${width} ${height}`"
      role="img"
      tabindex="0"
      :aria-label="t('charts.lineLabel', { n: series.length })"
      @pointermove="onPointerMove"
      @pointerleave="activeIndex = null"
      @keydown="onKeydown"
      @blur="activeIndex = null"
    >
      <!-- Recessive frame: hairline grid, no chart junk. -->
      <g class="grid">
        <line
          v-for="tick in yTicks"
          :key="`y${tick}`"
          :x1="PAD.left"
          :x2="PAD.left + plotWidth"
          :y1="y(tick)"
          :y2="y(tick)"
        />
      </g>
      <g class="axis">
        <text
          v-for="tick in yTicks"
          :key="`yt${tick}`"
          :x="PAD.left - 8"
          :y="y(tick) + 4"
          text-anchor="end"
        >
          {{ Number(tick.toFixed(decimals)) }}
        </text>
        <text
          v-for="day in xTicks"
          :key="`xt${day}`"
          :x="x(day)"
          :y="height - 8"
          text-anchor="middle"
        >
          {{ formatDay(day) }}
        </text>
      </g>

      <g v-if="active" class="crosshair">
        <line :x1="active.at" :x2="active.at" :y1="PAD.top" :y2="PAD.top + plotHeight" />
      </g>

      <g v-for="s in series" :key="s.key">
        <path v-if="area" class="area" :d="areaPath(s.points)" :fill="s.color" />
        <path class="line" :d="path(s.points)" :stroke="s.color" />
        <!-- End marker with a surface ring, so crossing lines stay readable. -->
        <circle
          v-if="s.points.length"
          :cx="x(s.points[s.points.length - 1].on)"
          :cy="y(s.points[s.points.length - 1].value)"
          r="4"
          :fill="s.color"
        />
      </g>

      <g v-if="active" class="active-dots">
        <circle
          v-for="row in active.rows"
          :key="row.series.key"
          :cx="active.at"
          :cy="y(row.point.value)"
          r="4.5"
          :fill="row.series.color"
        />
      </g>

      <!-- Direct labels: identity without relying on colour alone. -->
      <g v-if="showEndLabels" class="end-labels">
        <template v-for="label in endLabels" :key="label.key">
          <polyline
            v-if="Math.abs(label.at - label.anchor) > 1"
            class="leader"
            :points="`${PAD.left + plotWidth + 3},${label.anchor} ${PAD.left + plotWidth + 8},${label.at - 4}`"
            :stroke="label.color"
          />
          <text :x="PAD.left + plotWidth + 10" :y="label.at + 3">{{ label.name }}</text>
        </template>
      </g>
    </svg>

    <div v-if="active" class="tooltip" :style="tooltipStyle" role="status">
      <span class="tip-day">{{ formatDay(active.day) }}</span>
      <span v-for="row in active.rows" :key="row.series.key" class="tip-row">
        <span class="key" :style="{ background: row.series.color }" aria-hidden="true"></span>
        <strong>{{ formatValue(row.point.value) }}</strong>
        <span class="tip-name">{{ row.series.name }}</span>
      </span>
    </div>

    <!-- Legend for two or more series; a single one is named by the card title. -->
    <figcaption v-if="series.length > 1" class="legend">
      <span v-for="s in series" :key="s.key" class="legend-item">
        <span class="swatch" :style="{ background: s.color }" aria-hidden="true"></span>
        {{ s.name }}
      </span>
    </figcaption>

    <!-- Table view: every plotted value, reachable without hovering. -->
    <details class="data">
      <summary>{{ t('charts.showData') }}</summary>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">{{ t('charts.date') }}</th>
              <th v-for="s in series" :key="s.key" scope="col">{{ s.name }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="day in days" :key="day">
              <th scope="row">{{ formatDay(day) }}</th>
              <td v-for="s in series" :key="s.key">
                {{
                  s.points.find((p) => p.on === day)
                    ? formatValue(s.points.find((p) => p.on === day)!.value)
                    : '—'
                }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </details>
  </figure>
</template>

<style scoped>
.chart {
  position: relative;
  margin: 0;
  width: 100%;
}
svg {
  display: block;
  width: 100%;
  touch-action: pan-y;
}
svg:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}
.grid line {
  stroke: var(--viz-grid);
  stroke-width: 1;
}
.axis text {
  fill: var(--color-muted);
  font-size: 0.68rem;
  font-variant-numeric: tabular-nums;
}
.crosshair line {
  stroke: var(--color-muted);
  stroke-width: 1;
  opacity: 0.5;
}
.line {
  fill: none;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.area {
  opacity: 0.1;
  stroke: none;
}
circle {
  stroke: var(--viz-surface);
  stroke-width: 2;
}
.leader {
  fill: none;
  stroke-width: 1;
  opacity: 0.6;
}
.end-labels text {
  fill: var(--color-muted);
  font-size: 0.68rem;
}
.tooltip {
  position: absolute;
  top: 6px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-elevated);
  box-shadow: var(--shadow-sm);
  font-size: 0.78rem;
  pointer-events: none;
  white-space: nowrap;
}
.tip-day {
  color: var(--color-muted);
  font-size: 0.7rem;
}
.tip-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.key {
  width: 12px;
  height: 2px;
  border-radius: 2px;
}
.tip-name {
  color: var(--color-muted);
}
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: 4px;
  color: var(--color-muted);
  font-size: 0.75rem;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.swatch {
  width: 14px;
  height: 3px;
  border-radius: 2px;
}
.data {
  margin-top: var(--space-xs);
  font-size: 0.78rem;
}
.data summary {
  color: var(--color-muted);
  cursor: pointer;
}
.table-scroll {
  overflow-x: auto;
  margin-top: var(--space-xs);
}
table {
  border-collapse: collapse;
  width: 100%;
  font-variant-numeric: tabular-nums;
}
th,
td {
  padding: 4px 8px;
  text-align: right;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}
thead th,
tbody th {
  text-align: left;
  color: var(--color-muted);
  font-weight: 600;
}
</style>
