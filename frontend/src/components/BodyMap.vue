<script setup lang="ts">
import { computed } from 'vue'

import type { Muscle } from '@/api/types'

const props = defineProps<{
  muscles: Muscle[]
  selected: string | null
}>()

const emit = defineEmits<{ select: [svgId: string] }>()

interface Shape {
  cx: number
  cy: number
  rx: number
  ry: number
}

interface Region {
  svgId: string
  view: 'front' | 'back'
  shapes: Shape[]
}

// Stylized layout: front figure on the left, back figure on the right. The
// coordinates only need to read as a human body, not be anatomically exact.
const REGIONS: Region[] = [
  {
    svgId: 'delts',
    view: 'front',
    shapes: [
      { cx: 108, cy: 96, rx: 15, ry: 12 },
      { cx: 172, cy: 96, rx: 15, ry: 12 },
    ],
  },
  {
    svgId: 'chest',
    view: 'front',
    shapes: [
      { cx: 126, cy: 116, rx: 17, ry: 14 },
      { cx: 154, cy: 116, rx: 17, ry: 14 },
    ],
  },
  {
    svgId: 'biceps',
    view: 'front',
    shapes: [
      { cx: 92, cy: 132, rx: 11, ry: 20 },
      { cx: 188, cy: 132, rx: 11, ry: 20 },
    ],
  },
  { svgId: 'abs', view: 'front', shapes: [{ cx: 140, cy: 160, rx: 19, ry: 26 }] },
  {
    svgId: 'quads',
    view: 'front',
    shapes: [
      { cx: 124, cy: 250, rx: 15, ry: 40 },
      { cx: 156, cy: 250, rx: 15, ry: 40 },
    ],
  },
  { svgId: 'traps', view: 'back', shapes: [{ cx: 380, cy: 98, rx: 26, ry: 13 }] },
  {
    svgId: 'triceps',
    view: 'back',
    shapes: [
      { cx: 332, cy: 132, rx: 11, ry: 20 },
      { cx: 428, cy: 132, rx: 11, ry: 20 },
    ],
  },
  {
    svgId: 'lats',
    view: 'back',
    shapes: [
      { cx: 362, cy: 138, rx: 13, ry: 22 },
      { cx: 398, cy: 138, rx: 13, ry: 22 },
    ],
  },
  {
    svgId: 'glutes',
    view: 'back',
    shapes: [
      { cx: 366, cy: 198, rx: 16, ry: 14 },
      { cx: 394, cy: 198, rx: 16, ry: 14 },
    ],
  },
  {
    svgId: 'hamstrings',
    view: 'back',
    shapes: [
      { cx: 364, cy: 252, rx: 15, ry: 40 },
      { cx: 396, cy: 252, rx: 15, ry: 40 },
    ],
  },
]

// Only render regions for muscles the API actually returned.
const byId = computed(() => new Map(props.muscles.map((m) => [m.svgId, m])))
const regions = computed(() => REGIONS.filter((r) => byId.value.has(r.svgId)))

function labelFor(svgId: string): string {
  return byId.value.get(svgId)?.name ?? svgId
}

function onSelect(svgId: string): void {
  emit('select', svgId)
}
</script>

<template>
  <svg
    class="body-map"
    viewBox="0 0 520 320"
    role="group"
    aria-label="Mapa muscular interactivo: frente y espalda"
  >
    <defs>
      <linearGradient id="muscleGrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#22d3ee" />
        <stop offset="100%" stop-color="#a855f7" />
      </linearGradient>
    </defs>

    <!-- Non-interactive silhouettes for context -->
    <g class="silhouette" aria-hidden="true">
      <template v-for="cx in [140, 380]" :key="cx">
        <circle :cx="cx" :cy="52" r="22" />
        <rect :x="cx - 34" y="80" width="68" height="118" rx="26" />
        <rect :x="cx - 52" y="88" width="16" height="82" rx="8" />
        <rect :x="cx + 36" y="88" width="16" height="82" rx="8" />
        <rect :x="cx - 30" y="196" width="24" height="96" rx="11" />
        <rect :x="cx + 6" y="196" width="24" height="96" rx="11" />
      </template>
    </g>

    <text x="140" y="26" class="caption">Frente</text>
    <text x="380" y="26" class="caption">Espalda</text>

    <!-- Interactive muscle regions -->
    <g
      v-for="region in regions"
      :key="region.svgId"
      class="muscle"
      :class="{ selected: region.svgId === selected }"
      role="button"
      tabindex="0"
      :aria-label="labelFor(region.svgId)"
      :aria-pressed="region.svgId === selected"
      @click="onSelect(region.svgId)"
      @keydown.enter.prevent="onSelect(region.svgId)"
      @keydown.space.prevent="onSelect(region.svgId)"
    >
      <title>{{ labelFor(region.svgId) }}</title>
      <ellipse
        v-for="(shape, i) in region.shapes"
        :key="i"
        :cx="shape.cx"
        :cy="shape.cy"
        :rx="shape.rx"
        :ry="shape.ry"
      />
    </g>
  </svg>
</template>

<style scoped>
.body-map {
  width: 100%;
  height: auto;
  max-width: 560px;
}
.silhouette circle,
.silhouette rect {
  fill: rgba(255, 255, 255, 0.06);
  stroke: var(--color-border);
  stroke-width: 1;
}
.caption {
  fill: var(--color-muted);
  font-size: 13px;
  text-anchor: middle;
  font-weight: 700;
  letter-spacing: 0.08em;
}
.muscle {
  cursor: pointer;
  outline: none;
}
.muscle ellipse {
  fill: var(--color-accent-soft);
  stroke: var(--color-accent);
  stroke-width: 1.5;
  transition:
    fill 0.25s ease,
    filter 0.25s ease,
    transform 0.25s ease;
  transform-box: fill-box;
  transform-origin: center;
}
.muscle:hover ellipse,
.muscle:focus-visible ellipse {
  fill: url(#muscleGrad);
  filter: drop-shadow(0 0 6px rgba(34, 211, 238, 0.8));
}
.muscle.selected ellipse {
  fill: url(#muscleGrad);
  filter: drop-shadow(0 0 9px rgba(168, 85, 247, 0.9));
}
.muscle.selected {
  animation: muscle-pulse 1.8s ease-in-out infinite;
}
.muscle:focus-visible ellipse {
  stroke: #fff;
  stroke-width: 2.5;
}
@keyframes muscle-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.72;
  }
}
@media (prefers-reduced-motion: reduce) {
  .muscle ellipse {
    transition: none;
  }
  .muscle.selected {
    animation: none;
  }
}
</style>
