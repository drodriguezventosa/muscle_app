<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

// A lightweight, dependency-free guided tour. Each step optionally navigates to
// a route and targets a DOM element (by CSS selector); the element is
// spotlighted and a tooltip is anchored to it. Steps without a target render
// centered (welcome / done).
export interface TourStep {
  route?: string // navigate here before showing the step
  target?: string // CSS selector to highlight
  targetMobile?: string // fallback selector on narrow viewports
  titleKey: string
  bodyKey: string
}

const props = defineProps<{ modelValue: boolean; steps: TourStep[] }>()
const emit = defineEmits<{ 'update:modelValue': [boolean]; finish: [boolean] }>()

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
// Where the user was when the tour opened, so we can return them on finish.
let returnPath = ''

const current = ref(0)
// Checked by default so simply closing the tour won't nag the user again;
// unchecking keeps it appearing on the next visit. The choice is reported on
// finish so the parent decides whether to persist the "seen" flag.
const dontShowAgain = ref(true)
const tip = ref<HTMLElement | null>(null)
const highlight = ref<{ top: number; left: number; width: number; height: number } | null>(null)
const tipStyle = ref<Record<string, string>>({})
const placement = ref<'center' | 'top' | 'bottom'>('center')

const isFirst = computed(() => current.value === 0)
const isLast = computed(() => current.value === props.steps.length - 1)
const step = computed(() => props.steps[current.value])

function isMobile(): boolean {
  return globalThis.matchMedia?.('(max-width: 820px)').matches ?? false
}

// Measure the active step's target and position both the spotlight and tooltip.
async function place(): Promise<void> {
  const s = step.value
  if (!s) return
  const selector = isMobile() && s.targetMobile ? s.targetMobile : s.target
  const el = selector ? document.querySelector<HTMLElement>(selector) : null

  if (!el) {
    // Centered step (no target): dim the whole screen, center the tooltip.
    highlight.value = null
    placement.value = 'center'
    tipStyle.value = {}
    return
  }

  const vh = globalThis.innerHeight
  const vw = globalThis.innerWidth

  // Scroll into view only when needed. Doing it unconditionally fires a scroll
  // event that re-enters place() (scroll listener) in a loop, which restarts the
  // spotlight's CSS transition every frame and leaves it visually stuck.
  const pre = el.getBoundingClientRect()
  if (pre.height > vh) {
    // A whole section is taller than the viewport: show its top rather than
    // centering it (which would hide the section's heading).
    if (globalThis.scrollY > 0) {
      globalThis.scrollTo({ top: 0 })
      await nextTick()
      if (step.value !== s) return
    }
  } else {
    const inView = pre.top >= 0 && pre.left >= 0 && pre.bottom <= vh && pre.right <= vw
    if (!inView) {
      el.scrollIntoView({ block: 'center', inline: 'center' })
      await nextTick()
      // The step may have advanced during the await (rapid clicks); a newer
      // place() is then responsible, so drop this stale computation.
      if (step.value !== s) return
    }
  }

  const r = el.getBoundingClientRect()
  const pad = 8
  const next = {
    top: r.top - pad,
    left: r.left - pad,
    width: r.width + pad * 2,
    height: r.height + pad * 2,
  }
  // Only reassign when the box actually moved, so repeated place() calls (resize
  // / scroll) don't restart the transition with an identical target.
  const cur = highlight.value
  if (
    !cur ||
    cur.top !== next.top ||
    cur.left !== next.left ||
    cur.width !== next.width ||
    cur.height !== next.height
  ) {
    highlight.value = next
  }

  const tipH = tip.value?.offsetHeight ?? 170
  const tipW = tip.value?.offsetWidth ?? 320

  let top: number
  if (r.bottom + 12 + tipH <= vh) {
    top = r.bottom + 12
    placement.value = 'bottom'
  } else if (r.top - 12 - tipH >= 0) {
    top = r.top - 12 - tipH
    placement.value = 'top'
  } else {
    top = Math.max(12, vh - tipH - 12)
    placement.value = 'bottom'
  }
  const left = Math.min(Math.max(12, r.left + r.width / 2 - tipW / 2), vw - tipW - 12)
  tipStyle.value = { top: `${top}px`, left: `${left}px` }
}

function reposition(): void {
  void place()
}

// Navigate to the current step's route (if any) and then position it. Routes
// are lazy-loaded, so we re-measure shortly after in case the view's layout
// settles a frame late.
async function activateStep(): Promise<void> {
  const s = step.value
  if (s?.route && route.path !== s.route) {
    try {
      await router.push(s.route)
    } catch {
      // navigation aborted (e.g. redundant) — ignore
    }
  }
  await nextTick()
  reposition()
  globalThis.setTimeout(reposition, 200)
}

async function next(): Promise<void> {
  if (isLast.value) finish()
  else {
    current.value += 1
    await activateStep()
  }
}
async function back(): Promise<void> {
  if (!isFirst.value) {
    current.value -= 1
    await activateStep()
  }
}
function finish(): void {
  emit('update:modelValue', false)
  emit('finish', dontShowAgain.value)
  // Return the user to wherever they were before the tour navigated around.
  if (returnPath && route.path !== returnPath) router.push(returnPath).catch(() => {})
}

function onKeydown(event: KeyboardEvent): void {
  if (!props.modelValue) return
  if (event.key === 'Escape') finish()
  else if (event.key === 'ArrowRight') next()
  else if (event.key === 'ArrowLeft') back()
}

// Step changes are driven by next()/back(), which call activateStep() directly;
// here we only handle open/close and keep the position fresh on resize/scroll.
watch(
  () => props.modelValue,
  async (open) => {
    if (open) {
      returnPath = route.path
      current.value = 0
      globalThis.addEventListener('resize', reposition)
      globalThis.addEventListener('scroll', reposition, true)
      globalThis.addEventListener('keydown', onKeydown)
      await nextTick()
      await activateStep()
      tip.value?.focus()
    } else {
      globalThis.removeEventListener('resize', reposition)
      globalThis.removeEventListener('scroll', reposition, true)
      globalThis.removeEventListener('keydown', onKeydown)
    }
  },
)

onBeforeUnmount(() => {
  globalThis.removeEventListener('resize', reposition)
  globalThis.removeEventListener('scroll', reposition, true)
  globalThis.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="modelValue" class="tour" aria-live="polite">
      <!-- Backdrop: dim for centered steps, transparent when a spotlight already
           dims the page. It only blocks interaction with the page underneath —
           closing requires the Skip button or finishing the tour, so an
           accidental outside click can't dismiss it (and mark it "seen"). -->
      <div class="tour-catch" :class="{ 'tour-catch--dim': !highlight }" @click.stop />
      <div
        v-if="highlight"
        class="tour-spotlight"
        :style="
          highlight
            ? {
                top: `${highlight.top}px`,
                left: `${highlight.left}px`,
                width: `${highlight.width}px`,
                height: `${highlight.height}px`,
              }
            : {}
        "
      />

      <div
        ref="tip"
        class="tour-tip glass"
        :class="`tour-tip--${placement}`"
        :style="placement === 'center' ? {} : tipStyle"
        role="dialog"
        aria-modal="true"
        :aria-label="t(step.titleKey)"
        tabindex="-1"
      >
        <p class="tour-step-count">{{ current + 1 }} / {{ steps.length }}</p>
        <h2 class="tour-title gradient-text">{{ t(step.titleKey) }}</h2>
        <p class="tour-body">{{ t(step.bodyKey) }}</p>
        <label class="tour-remember">
          <input v-model="dontShowAgain" type="checkbox" />
          <span>{{ t('tour.dontShowAgain') }}</span>
        </label>
        <div class="tour-actions">
          <button type="button" class="tour-skip" @click="finish">{{ t('tour.skip') }}</button>
          <div class="tour-nav">
            <button v-if="!isFirst" type="button" class="tour-btn ghost" @click="back">
              {{ t('tour.back') }}
            </button>
            <button type="button" class="tour-btn primary" @click="next">
              {{ isLast ? t('tour.done') : t('tour.next') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.tour {
  position: fixed;
  inset: 0;
  z-index: 1000;
}
.tour-catch {
  position: fixed;
  inset: 0;
}
.tour-catch--dim {
  background: rgba(2, 6, 23, 0.66);
}
/* The spotlight dims the rest of the page via a huge outer box-shadow. */
.tour-spotlight {
  position: fixed;
  border-radius: var(--radius-md, 12px);
  box-shadow: 0 0 0 9999px rgba(2, 6, 23, 0.66);
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
  pointer-events: none;
  transition:
    top 0.25s ease,
    left 0.25s ease,
    width 0.25s ease,
    height 0.25s ease;
}
.tour-tip {
  position: fixed;
  width: min(340px, calc(100vw - 24px));
  padding: var(--space-md) var(--space-lg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md, 14px);
  background: var(--color-elevated);
  box-shadow: var(--shadow-lg, 0 20px 50px rgba(0, 0, 0, 0.35));
  outline: none;
}
.tour-tip--center {
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.tour-step-count {
  margin: 0 0 4px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--color-muted);
}
.tour-title {
  margin: 0 0 var(--space-xs);
  font-size: 1.15rem;
}
.tour-body {
  margin: 0 0 var(--space-md);
  color: var(--color-text);
  font-size: 0.92rem;
  line-height: 1.5;
}
.tour-remember {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
  font-size: 0.82rem;
  color: var(--color-muted);
  cursor: pointer;
}
.tour-remember input {
  accent-color: var(--color-accent);
  cursor: pointer;
}
.tour-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
}
.tour-nav {
  display: flex;
  gap: var(--space-sm);
}
.tour-skip {
  background: none;
  border: none;
  color: var(--color-muted);
  font-size: 0.85rem;
  cursor: pointer;
  padding: 6px 4px;
}
.tour-skip:hover {
  color: var(--color-text);
}
.tour-btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--color-border);
}
.tour-btn.ghost {
  background: var(--color-surface);
  color: var(--color-text);
}
.tour-btn.ghost:hover {
  border-color: var(--color-accent);
}
.tour-btn.primary {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}
.tour-btn.primary:hover {
  filter: brightness(1.08);
}
@media (prefers-reduced-motion: reduce) {
  .tour-spotlight {
    transition: none;
  }
}
</style>
