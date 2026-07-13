<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import VideoModal from '@/components/VideoModal.vue'
import type { Exercise } from '@/api/types'

defineProps<{
  muscleName: string | null
  exercises: Exercise[]
  loading: boolean
  error: string | null
}>()

const { t } = useI18n()
const activeVideo = ref<{ url: string; title: string } | null>(null)
</script>

<template>
  <section class="panel" aria-live="polite">
    <h2 v-if="muscleName" class="title">{{ muscleName }}</h2>
    <p v-else class="hint">{{ t('panel.prompt') }}</p>

    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <p v-else-if="loading" class="hint">{{ t('panel.loading') }}</p>
    <p v-else-if="muscleName && exercises.length === 0" class="hint">
      {{ t('panel.empty') }}
    </p>

    <ul v-if="exercises.length" class="list">
      <li v-for="exercise in exercises" :key="exercise.id" class="card">
        <div class="card-head">
          <h3 class="card-title">{{ exercise.name }}</h3>
          <div class="badges">
            <span class="badge">{{ t(`equipment.${exercise.equipment}`) }}</span>
            <span class="badge badge-soft">{{ t(`difficulty.${exercise.difficulty}`) }}</span>
          </div>
        </div>
        <p class="card-desc">{{ exercise.description }}</p>
        <template v-if="exercise.videoUrl">
          <button
            class="watch"
            type="button"
            @click="activeVideo = { url: exercise.videoUrl, title: exercise.name }"
          >
            <span class="play" aria-hidden="true">▶</span> {{ t('video.watch') }}
          </button>
          <details v-if="exercise.steps.length" class="steps-toggle">
            <summary>{{ t('panel.steps') }}</summary>
            <ol class="steps-list">
              <li v-for="(step, i) in exercise.steps" :key="i">{{ step }}</li>
            </ol>
          </details>
        </template>
        <div v-else-if="exercise.steps.length" class="steps">
          <p class="steps-title">{{ t('panel.steps') }}</p>
          <ol class="steps-list">
            <li v-for="(step, i) in exercise.steps" :key="i">{{ step }}</li>
          </ol>
        </div>
      </li>
    </ul>

    <VideoModal
      v-if="activeVideo"
      :url="activeVideo.url"
      :title="activeVideo.title"
      @close="activeVideo = null"
    />
  </section>
</template>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.title {
  margin: 0;
  font-size: 1.4rem;
}
.hint {
  color: var(--color-muted);
  margin: 0;
}
.error {
  color: var(--color-danger);
  margin: 0;
}
.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  /* Scroll the cards internally so a long list doesn't stretch the page.
     This height is the reference the body card matches on desktop. */
  max-height: min(62vh, 620px);
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}
.list::-webkit-scrollbar {
  width: 6px;
}
.list::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 999px;
}
.card {
  position: relative;
  background: var(--color-surface-strong);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-md);
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
  animation: fade-in-up 0.4s ease both;
}
/* Gradient hairline that lights up on hover. */
.card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  /* Decorative gradient hairline: must never intercept clicks on the card's
     controls (it's positioned, so it would otherwise sit above the button). */
  pointer-events: none;
  padding: 1px;
  background: var(--gradient);
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0;
  transition: opacity 0.2s ease;
}
.card:hover {
  transform: translateY(-3px);
  box-shadow: var(--glow);
}
.card:hover::before {
  opacity: 1;
}
.card:nth-child(2) {
  animation-delay: 0.05s;
}
.card:nth-child(3) {
  animation-delay: 0.1s;
}
.card:nth-child(4) {
  animation-delay: 0.15s;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-sm);
  flex-wrap: wrap;
}
.card-title {
  margin: 0;
  font-size: 1.05rem;
}
.badges {
  display: flex;
  gap: var(--space-xs);
}
.badge {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--gradient);
  color: #06121a;
  font-weight: 700;
}
.badge-soft {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}
.card-desc {
  margin: var(--space-sm) 0 0;
  color: var(--color-muted);
}
.watch {
  margin-top: var(--space-sm);
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-text);
  font: inherit;
  font-size: 0.85rem;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}
.watch:hover {
  border-color: var(--color-accent);
  box-shadow: var(--glow);
  transform: translateY(-1px);
}
.play {
  display: inline-flex;
  width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--gradient);
  color: #06121a;
  font-size: 0.6rem;
}
.steps {
  margin-top: var(--space-sm);
}
.steps-toggle {
  margin-top: var(--space-sm);
}
.steps-toggle summary {
  cursor: pointer;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-accent);
  list-style: none;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.steps-toggle summary::-webkit-details-marker {
  display: none;
}
.steps-toggle summary::before {
  content: '▸';
  transition: transform 0.15s ease;
}
.steps-toggle[open] summary::before {
  transform: rotate(90deg);
}
.steps-toggle .steps-list {
  margin-top: var(--space-xs);
}
.steps-title {
  margin: 0 0 var(--space-xs);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-accent);
}
.steps-list {
  margin: 0;
  padding-left: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--color-muted);
  font-size: 0.88rem;
}
.steps-list li {
  padding-left: 2px;
}
.steps-list li::marker {
  color: var(--color-accent);
  font-weight: 700;
}
</style>
