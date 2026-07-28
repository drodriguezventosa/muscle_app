<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useElementWidth } from '@/composables/useElementWidth'

export interface Bar {
  /** Short label under the column (kept sparse: only every other one is drawn). */
  label: string
  /** Long form for the tooltip and the table. */
  title: string
  value: number
}

const props = withDefaults(
  defineProps<{
    bars: Bar[]
    unit?: string
    height?: number
  }>(),
  { unit: '', height: 180 },
)

const { t } = useI18n()

const wrapper = ref<HTMLElement | null>(null)
const width = useElementWidth(wrapper)

const PAD = { top: 14, right: 8, bottom: 24, left: 30 }
// Marks stay thin, and a 2px surface gap does the separating between them.
const MAX_BAR = 24
const GAP = 2

const plotWidth = computed(() => Math.max(60, width.value - PAD.left - PAD.right))
const plotHeight = computed(() => Math.max(50, props.height - PAD.top - PAD.bottom))
const band = computed(() => plotWidth.value / Math.max(1, props.bars.length))
const barWidth = computed(() => Math.min(MAX_BAR, Math.max(4, band.value - GAP * 2)))

const maxValue = computed(() => Math.max(1, ...props.bars.map((b) => b.value)))

function x(index: number): number {
  return PAD.left + band.value * index + (band.value - barWidth.value) / 2
}

function heightOf(value: number): number {
  return (value / maxValue.value) * plotHeight.value
}

function y(value: number): number {
  return PAD.top + plotHeight.value - heightOf(value)
}

const yTicks = computed(() => {
  const top = Math.ceil(maxValue.value)
  return top <= 4 ? Array.from({ length: top + 1 }, (_, i) => i) : [0, top / 2, top]
})

const activeIndex = ref<number | null>(null)
const active = computed(() =>
  activeIndex.value === null ? null : (props.bars[activeIndex.value] ?? null),
)

const tooltipStyle = computed(() => {
  if (activeIndex.value === null) return {}
  const centre = x(activeIndex.value) + barWidth.value / 2
  return {
    left: `${centre}px`,
    transform: centre > width.value * 0.6 ? 'translateX(-100%)' : 'translateX(-0%)',
  }
})

function formatValue(value: number): string {
  return props.unit ? `${value} ${props.unit}` : String(value)
}
</script>

<template>
  <figure ref="wrapper" class="chart">
    <svg
      :width="width"
      :height="height"
      :viewBox="`0 0 ${width} ${height}`"
      role="img"
      :aria-label="t('charts.barLabel')"
    >
      <g class="grid">
        <line
          v-for="tick in yTicks"
          :key="`g${tick}`"
          :x1="PAD.left"
          :x2="PAD.left + plotWidth"
          :y1="y(tick)"
          :y2="y(tick)"
        />
      </g>
      <g class="axis">
        <text
          v-for="tick in yTicks"
          :key="`t${tick}`"
          :x="PAD.left - 6"
          :y="y(tick) + 4"
          text-anchor="end"
        >
          {{ tick }}
        </text>
      </g>

      <!-- The mark is the hit target; the hit area is wider than the mark. -->
      <!-- The mark is the hit target, and its hit area is the whole band. The
           transparent rect goes last so it sits above the bar and gets the
           pointer events. -->
      <g v-for="(bar, index) in bars" :key="bar.title">
        <rect
          class="bar"
          :class="{ on: activeIndex === index, zero: bar.value === 0 }"
          :x="x(index)"
          :y="bar.value === 0 ? PAD.top + plotHeight - 2 : y(bar.value)"
          :width="barWidth"
          :height="bar.value === 0 ? 2 : heightOf(bar.value)"
          rx="4"
        />
        <rect
          class="hit"
          :x="PAD.left + band * index"
          :y="PAD.top"
          :width="band"
          :height="plotHeight"
          tabindex="0"
          role="img"
          :aria-label="`${bar.title}: ${formatValue(bar.value)}`"
          @pointerenter="activeIndex = index"
          @pointerleave="activeIndex = null"
          @focus="activeIndex = index"
          @blur="activeIndex = null"
        />
      </g>

      <!-- Squared foot: the rounded end belongs to the data end, not the baseline. -->
      <rect
        v-for="(bar, index) in bars"
        :key="`foot${bar.title}`"
        class="bar foot"
        :class="{ on: activeIndex === index }"
        :x="x(index)"
        :y="PAD.top + plotHeight - Math.min(4, heightOf(bar.value))"
        :width="barWidth"
        :height="Math.min(4, heightOf(bar.value))"
      />

      <g class="axis">
        <text
          v-for="(bar, index) in bars"
          :key="`l${bar.title}`"
          :x="x(index) + barWidth / 2"
          :y="height - 8"
          text-anchor="middle"
        >
          {{ index % 2 === 0 ? bar.label : '' }}
        </text>
      </g>
    </svg>

    <div v-if="active" class="tooltip" :style="tooltipStyle" role="status">
      <strong>{{ formatValue(active.value) }}</strong>
      <span class="tip-name">{{ active.title }}</span>
    </div>

    <details class="data">
      <summary>{{ t('charts.showData') }}</summary>
      <div class="table-scroll">
        <table>
          <tbody>
            <tr v-for="bar in bars" :key="bar.title">
              <th scope="row">{{ bar.title }}</th>
              <td>{{ formatValue(bar.value) }}</td>
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
.axis text {
  fill: var(--color-muted);
  font-size: 0.68rem;
  font-variant-numeric: tabular-nums;
}
.bar {
  fill: var(--series-1);
  transition: opacity 0.15s ease;
}
/* A week with no sessions still gets a sliver, so the gap reads as "zero"
   rather than as missing data. */
.bar.zero {
  fill: var(--color-muted);
  opacity: 0.4;
}
.bar.on {
  opacity: 0.75;
}
.hit {
  fill: transparent;
  cursor: default;
}
.hit:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: -2px;
}
.tooltip {
  position: absolute;
  top: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-elevated);
  box-shadow: var(--shadow-sm);
  font-size: 0.78rem;
  pointer-events: none;
  white-space: nowrap;
}
.tip-name {
  color: var(--color-muted);
  font-size: 0.7rem;
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
  max-height: 220px;
  overflow-y: auto;
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
th {
  text-align: left;
  color: var(--color-muted);
  font-weight: 600;
}
td {
  text-align: right;
}
</style>
