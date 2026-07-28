<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useElementWidth } from '@/composables/useElementWidth'

export interface ScatterPoint {
  key: string | number
  /** Two or three characters drawn beside the dot: identity without colour. */
  initials: string
  name: string
  x: number
  y: number
  /** Category the colour encodes; capped at three (all-pairs CVD limit). */
  group: string
  groupLabel: string
  color: string
}

const props = withDefaults(
  defineProps<{
    points: ScatterPoint[]
    xLabel: string
    yLabel: string
    height?: number
    /** Reference band on the y axis (e.g. a healthy BMI range). */
    yBand?: [number, number] | null
    yBandLabel?: string
  }>(),
  { height: 220, yBand: null, yBandLabel: '' },
)

const { t } = useI18n()

const wrapper = ref<HTMLElement | null>(null)
const width = useElementWidth(wrapper)

const PAD = { top: 16, right: 20, bottom: 30, left: 36 }

const plotWidth = computed(() => Math.max(80, width.value - PAD.left - PAD.right))
const plotHeight = computed(() => Math.max(70, props.height - PAD.top - PAD.bottom))

function domain(values: number[], band: [number, number] | null): [number, number] {
  const all = band ? [...values, ...band] : values
  const min = Math.min(...all)
  const max = Math.max(...all)
  if (min === max) return [min - 2, max + 2]
  const margin = (max - min) * 0.15
  return [min - margin, max + margin]
}

const xDomain = computed(() =>
  domain(
    props.points.map((p) => p.x),
    null,
  ),
)
const yDomain = computed(() =>
  domain(
    props.points.map((p) => p.y),
    props.yBand,
  ),
)

function x(value: number): number {
  const [min, max] = xDomain.value
  return PAD.left + ((value - min) / (max - min)) * plotWidth.value
}

function y(value: number): number {
  const [min, max] = yDomain.value
  return PAD.top + plotHeight.value - ((value - min) / (max - min)) * plotHeight.value
}

/** Ticks on round numbers (…5, 10, 25…), so the axis reads at a glance. */
function ticks([min, max]: [number, number]): number[] {
  const rough = (max - min) / 3
  const magnitude = 10 ** Math.floor(Math.log10(rough))
  const step =
    [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= rough) ?? magnitude * 10
  const first = Math.ceil(min / step) * step
  const values: number[] = []
  for (let value = first; value <= max; value += step) values.push(Number(value.toFixed(2)))
  return values
}

/** One legend entry per category, in first-seen order (never by rank). */
const groups = computed(() => {
  const seen = new Map<string, { label: string; color: string }>()
  for (const point of props.points) {
    if (!seen.has(point.group))
      seen.set(point.group, { label: point.groupLabel, color: point.color })
  }
  return [...seen.entries()].map(([group, value]) => ({ group, ...value }))
})

const activeKey = ref<string | number | null>(null)
const active = computed(() => props.points.find((p) => p.key === activeKey.value) ?? null)

const tooltipStyle = computed(() => {
  if (!active.value) return {}
  const at = x(active.value.x)
  return {
    left: `${at}px`,
    top: `${y(active.value.y)}px`,
    transform: at > width.value * 0.6 ? 'translate(-100%, -120%)' : 'translate(0, -120%)',
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
      :aria-label="t('charts.scatterLabel', { x: xLabel, y: yLabel })"
    >
      <!-- Reference band first, so the dots sit on top of it. -->
      <rect
        v-if="yBand"
        class="band"
        :x="PAD.left"
        :y="y(yBand[1])"
        :width="plotWidth"
        :height="Math.max(0, y(yBand[0]) - y(yBand[1]))"
      />
      <text
        v-if="yBand && yBandLabel"
        class="band-label"
        :x="PAD.left + plotWidth - 4"
        :y="y(yBand[1]) - 4"
        text-anchor="end"
      >
        {{ yBandLabel }}
      </text>

      <g class="grid">
        <line
          v-for="tick in ticks(yDomain)"
          :key="`g${tick}`"
          :x1="PAD.left"
          :x2="PAD.left + plotWidth"
          :y1="y(tick)"
          :y2="y(tick)"
        />
      </g>
      <g class="axis">
        <text
          v-for="tick in ticks(yDomain)"
          :key="`ty${tick}`"
          :x="PAD.left - 6"
          :y="y(tick) + 4"
          text-anchor="end"
        >
          {{ tick }}
        </text>
        <text
          v-for="tick in ticks(xDomain)"
          :key="`tx${tick}`"
          :x="x(tick)"
          :y="height - 14"
          text-anchor="middle"
        >
          {{ tick }}
        </text>
        <text class="axis-title" :x="PAD.left + plotWidth / 2" :y="height - 1" text-anchor="middle">
          {{ xLabel }}
        </text>
      </g>

      <!-- 24px transparent hit area (an 8px dot is a pinpoint nobody hits),
           drawn last so it sits above the dot and receives the pointer. -->
      <g v-for="point in points" :key="point.key">
        <circle class="dot" :cx="x(point.x)" :cy="y(point.y)" r="5" :fill="point.color" />
        <text class="initials" :x="x(point.x) + 9" :y="y(point.y) + 4">{{ point.initials }}</text>
        <circle
          class="hit"
          :cx="x(point.x)"
          :cy="y(point.y)"
          r="12"
          tabindex="0"
          role="img"
          :aria-label="`${point.name}, ${point.groupLabel}: ${xLabel} ${point.x}, ${yLabel} ${point.y}`"
          @pointerenter="activeKey = point.key"
          @pointerleave="activeKey = null"
          @focus="activeKey = point.key"
          @blur="activeKey = null"
        />
      </g>
    </svg>

    <div v-if="active" class="tooltip" :style="tooltipStyle" role="status">
      <strong>{{ active.name }}</strong>
      <span class="tip-row">{{ xLabel }}: {{ active.x }}</span>
      <span class="tip-row">{{ yLabel }}: {{ active.y }}</span>
      <span class="tip-group">{{ active.groupLabel }}</span>
    </div>

    <figcaption class="legend">
      <span v-for="group in groups" :key="group.group" class="legend-item">
        <span class="swatch" :style="{ background: group.color }" aria-hidden="true"></span>
        {{ group.label }}
      </span>
    </figcaption>

    <details class="data">
      <summary>{{ t('charts.showData') }}</summary>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">{{ t('charts.student') }}</th>
              <th scope="col">{{ xLabel }}</th>
              <th scope="col">{{ yLabel }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="point in points" :key="point.key">
              <th scope="row">{{ point.name }} · {{ point.groupLabel }}</th>
              <td>{{ point.x }}</td>
              <td>{{ point.y }}</td>
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
}
.grid line {
  stroke: var(--viz-grid);
  stroke-width: 1;
}
.band {
  fill: var(--color-muted);
  opacity: 0.08;
}
.band-label,
.axis text {
  fill: var(--color-muted);
  font-size: 0.68rem;
  font-variant-numeric: tabular-nums;
}
.axis-title {
  font-size: 0.68rem;
}
.dot {
  stroke: var(--viz-surface);
  stroke-width: 2;
}
.initials {
  fill: var(--color-text);
  font-size: 0.66rem;
  font-weight: 600;
}
.hit {
  fill: transparent;
}
.hit:focus-visible {
  outline: 2px solid var(--color-accent);
}
.tooltip {
  position: absolute;
  z-index: 2;
  display: flex;
  flex-direction: column;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-elevated);
  box-shadow: var(--shadow-sm);
  font-size: 0.76rem;
  pointer-events: none;
  white-space: nowrap;
}
.tip-row {
  color: var(--color-text);
}
.tip-group {
  color: var(--color-muted);
  font-size: 0.7rem;
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
  width: 10px;
  height: 10px;
  border-radius: 50%;
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
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}
thead th,
tbody th {
  text-align: left;
  color: var(--color-muted);
  font-weight: 600;
}
td {
  text-align: right;
}
</style>
