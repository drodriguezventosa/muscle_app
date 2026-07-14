<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Muscle, MuscleGroup } from '@/api/types'
import type { BodyView } from '@/stores/explorer'

const { t } = useI18n()

const props = defineProps<{
  muscles: Muscle[]
  selected: string | null
  activeSvgIds: string[]
  view: BodyView
}>()

const emit = defineEmits<{ select: [svgId: string] }>()

interface Region {
  group: MuscleGroup
  view: 'front' | 'back'
  paths: string[]
}

// Anatomical-ish muscle shapes drawn as SVG paths. Front figure centred at
// x≈130, back at x≈390. Each region maps to a muscle GROUP; clicking one with
// several muscles opens a popup to pick the specific muscle.
const SILHOUETTE: Record<'front' | 'back', string> = {
  front:
    'M130 62 C116 62 108 71 107 84 L96 92 C86 99 82 114 85 133 L92 146 C95 131 99 121 106 114 ' +
    'L104 150 C102 168 101 184 103 198 L100 250 C99 280 103 300 106 314 L120 314 C122 296 124 268 126 236 ' +
    'C127 220 129 210 130 210 C131 210 133 220 134 236 C136 268 138 296 140 314 L154 314 C157 300 161 280 160 250 ' +
    'L157 198 C159 184 158 168 156 150 L154 114 C161 121 165 131 168 146 L175 133 C178 114 174 99 164 92 ' +
    'L153 84 C152 71 144 62 130 62 Z',
  back:
    'M390 62 C376 62 368 71 367 84 L356 92 C346 99 342 114 345 133 L352 146 C355 131 359 121 366 114 ' +
    'L364 150 C362 168 361 184 363 198 L360 250 C359 280 363 300 366 314 L380 314 C382 296 384 268 386 236 ' +
    'C387 220 389 210 390 210 C391 210 393 220 394 236 C396 268 398 296 400 314 L414 314 C417 300 421 280 420 250 ' +
    'L417 198 C419 184 418 168 416 150 L414 114 C421 121 425 131 428 146 L435 133 C438 114 434 99 424 92 ' +
    'L413 84 C412 71 404 62 390 62 Z',
}

const REGIONS: Region[] = [
  // --- Front ---
  {
    group: 'shoulders',
    view: 'front',
    paths: [
      'M108 88 C98 88 92 96 93 106 C94 114 102 117 110 113 C116 110 117 98 114 92 C113 89 111 88 108 88 Z',
      'M152 88 C162 88 168 96 167 106 C166 114 158 117 150 113 C144 110 143 98 146 92 C147 89 149 88 152 88 Z',
    ],
  },
  {
    group: 'chest',
    view: 'front',
    paths: [
      'M128 100 C116 100 106 104 105 116 C104 127 114 133 127 131 C129 130 129 130 129 128 L129 102 C129 100 128 100 128 100 Z',
      'M132 100 C144 100 154 104 155 116 C156 127 146 133 133 131 C131 130 131 130 131 128 L131 102 C131 100 132 100 132 100 Z',
    ],
  },
  {
    group: 'arms',
    view: 'front',
    paths: [
      'M92 108 C84 110 82 120 84 134 L88 158 C90 166 100 166 102 158 L104 132 C104 116 100 106 92 108 Z',
      'M168 108 C176 110 178 120 176 134 L172 158 C170 166 160 166 158 158 L156 132 C156 116 160 106 168 108 Z',
    ],
  },
  {
    group: 'core',
    view: 'front',
    paths: [
      'M118 138 C126 135 134 135 142 138 L143 152 L117 152 Z',
      'M117 156 L143 156 L143 172 C134 176 126 176 117 172 Z',
    ],
  },
  {
    group: 'legs',
    view: 'front',
    paths: [
      'M108 190 C102 196 102 214 104 232 L110 268 C112 276 122 276 124 268 L126 220 C126 202 120 190 108 190 Z',
      'M152 190 C158 196 158 214 156 232 L150 268 C148 276 138 276 136 268 L134 220 C134 202 140 190 152 190 Z',
    ],
  },
  // --- Back ---
  {
    group: 'back',
    view: 'back',
    paths: [
      // traps
      'M390 86 C378 86 372 92 370 100 C380 96 400 96 410 100 C408 92 402 86 390 86 Z',
      // lats (left + right wings)
      'M366 108 C360 116 360 134 364 152 C372 156 378 150 378 140 L378 114 C378 108 372 106 366 108 Z',
      'M414 108 C420 116 420 134 416 152 C408 156 402 150 402 140 L402 114 C402 108 408 106 414 108 Z',
    ],
  },
  {
    group: 'arms',
    view: 'back',
    paths: [
      'M352 108 C344 110 342 120 344 134 L348 158 C350 166 360 166 362 158 L364 132 C364 116 360 106 352 108 Z',
      'M428 108 C436 110 438 120 436 134 L432 158 C430 166 420 166 418 158 L416 132 C416 116 420 106 428 108 Z',
    ],
  },
  {
    group: 'glutes',
    view: 'back',
    paths: [
      'M388 176 C378 176 372 184 373 196 C374 206 384 210 390 204 L390 178 C390 176 389 176 388 176 Z',
      'M392 176 C402 176 408 184 407 196 C406 206 396 210 390 204 L390 178 C390 176 391 176 392 176 Z',
    ],
  },
  {
    group: 'legs',
    view: 'back',
    paths: [
      'M368 210 C362 216 362 232 364 250 L370 282 C372 290 382 290 384 282 L386 238 C386 222 380 210 368 210 Z',
      'M412 210 C418 216 418 232 416 250 L410 282 C408 290 398 290 396 282 L394 238 C394 222 400 210 412 210 Z',
    ],
  },
]

const activeSet = computed(() => new Set(props.activeSvgIds))

// muscles grouped by their group, keeping only those matching the filters.
const activeByGroup = computed(() => {
  const map = new Map<MuscleGroup, Muscle[]>()
  for (const m of props.muscles) {
    if (!activeSet.value.has(m.svgId)) continue
    const list = map.get(m.muscleGroup) ?? []
    list.push(m)
    map.set(m.muscleGroup, list)
  }
  return map
})

function musclesOf(group: MuscleGroup): Muscle[] {
  return activeByGroup.value.get(group) ?? []
}

// A figure's regions that have at least one matching muscle.
function regionsFor(view: 'front' | 'back'): Region[] {
  return REGIONS.filter((r) => r.view === view && musclesOf(r.group).length > 0)
}

const figures = computed(() =>
  [
    {
      side: 'front' as const,
      show: props.view !== 'back',
      transform: props.view === 'front' ? 'translate(130, 0)' : '',
      caption: t('bodyMap.front'),
    },
    {
      side: 'back' as const,
      show: props.view !== 'front',
      transform: props.view === 'back' ? 'translate(-130, 0)' : '',
      caption: t('bodyMap.back'),
    },
  ].filter((f) => f.show),
)

function captionX(side: 'front' | 'back'): number {
  return side === 'front' ? 130 : 390
}

function isSelected(group: MuscleGroup): boolean {
  return musclesOf(group).some((m) => m.svgId === props.selected)
}

// Popup for choosing a specific muscle within a multi-muscle group.
const popup = ref<{ muscles: Muscle[]; x: number; y: number } | null>(null)

function onGroupClick(region: Region, event: MouseEvent | KeyboardEvent): void {
  const muscles = musclesOf(region.group)
  if (muscles.length === 1) {
    emit('select', muscles[0].svgId)
    return
  }
  // Position the popup at the cursor, or the region centre for keyboard use.
  let x: number
  let y: number
  if (event instanceof MouseEvent && event.clientX) {
    x = event.clientX
    y = event.clientY
  } else {
    const rect = (event.currentTarget as Element).getBoundingClientRect()
    x = rect.left + rect.width / 2
    y = rect.top + rect.height / 2
  }
  popup.value = { muscles, x, y }
}

function pick(svgId: string): void {
  emit('select', svgId)
  popup.value = null
}

function onDocumentClick(): void {
  popup.value = null
}
function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') popup.value = null
}
onMounted(() => {
  document.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <svg class="body-map" viewBox="0 0 520 340" role="group" :aria-label="t('bodyMap.label')">
    <defs>
      <linearGradient id="muscleGrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#22d3ee" />
        <stop offset="100%" stop-color="#a855f7" />
      </linearGradient>
    </defs>

    <g v-for="figure in figures" :key="figure.side" :transform="figure.transform">
      <path class="silhouette" :d="SILHOUETTE[figure.side]" aria-hidden="true" />
      <circle class="silhouette" :cx="captionX(figure.side)" :cy="42" r="18" aria-hidden="true" />
      <text :x="captionX(figure.side)" y="20" class="caption">{{ figure.caption }}</text>

      <g
        v-for="region in regionsFor(figure.side)"
        :key="region.group"
        class="muscle"
        :class="{ selected: isSelected(region.group) }"
        role="button"
        tabindex="0"
        :aria-label="t(`groups.${region.group}`)"
        :aria-pressed="isSelected(region.group)"
        @click="onGroupClick(region, $event)"
        @keydown.enter.prevent="onGroupClick(region, $event)"
        @keydown.space.prevent="onGroupClick(region, $event)"
      >
        <title>{{ t(`groups.${region.group}`) }}</title>
        <path v-for="(d, i) in region.paths" :key="i" :d="d" />
      </g>
    </g>
  </svg>

  <!-- Popup to choose a specific muscle within a group -->
  <Teleport to="body">
    <div v-if="popup" class="popup-overlay" @click="onDocumentClick">
      <div
        class="popup glass"
        role="menu"
        :aria-label="t('bodyMap.chooseMuscle')"
        :style="{ left: `${popup.x}px`, top: `${popup.y}px` }"
        @click.stop
      >
        <p class="popup-title">{{ t('bodyMap.chooseMuscle') }}</p>
        <button
          v-for="m in popup.muscles"
          :key="m.svgId"
          type="button"
          class="popup-item"
          role="menuitem"
          @click="pick(m.svgId)"
        >
          {{ m.name }}
        </button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.body-map {
  width: 100%;
  height: auto;
  max-width: 560px;
}
.silhouette {
  fill: var(--color-surface-strong);
  stroke: var(--color-border);
  stroke-width: 1;
}
.caption {
  fill: var(--color-muted);
  font-size: 12px;
  text-anchor: middle;
  font-weight: 700;
  letter-spacing: 0.08em;
}
.muscle {
  cursor: pointer;
  outline: none;
}
.muscle path {
  fill: var(--color-accent-soft);
  stroke: var(--color-accent);
  stroke-width: 1.2;
  transition:
    fill 0.25s ease,
    filter 0.25s ease;
}
.muscle:hover path,
.muscle:focus-visible path {
  fill: url(#muscleGrad);
  filter: drop-shadow(0 0 5px rgba(34, 211, 238, 0.8));
}
.muscle.selected path {
  fill: url(#muscleGrad);
  filter: drop-shadow(0 0 8px rgba(168, 85, 247, 0.9));
}
.muscle:focus-visible path {
  stroke: #fff;
  stroke-width: 2;
}

.popup-overlay {
  position: fixed;
  inset: 0;
  z-index: 70;
}
.popup {
  position: fixed;
  transform: translate(-50%, 12px);
  min-width: 160px;
  padding: var(--space-xs);
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--color-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55);
  animation: pop 0.16s ease both;
}
.popup-title {
  margin: 0;
  padding: 4px 10px;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-muted);
}
.popup-item {
  padding: 8px 10px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text);
  font: inherit;
  font-size: 0.9rem;
  text-align: left;
  cursor: pointer;
}
.popup-item:hover {
  background: var(--gradient);
  color: #06121a;
  font-weight: 600;
}
@keyframes pop {
  from {
    opacity: 0;
    transform: translate(-50%, 4px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .popup {
    animation: none;
  }
}
</style>
