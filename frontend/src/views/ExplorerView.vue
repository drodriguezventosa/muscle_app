<script setup lang="ts">
import { onMounted } from 'vue'

import BodyMap from '@/components/BodyMap.vue'
import ExercisePanel from '@/components/ExercisePanel.vue'
import HealthDisclaimer from '@/components/HealthDisclaimer.vue'
import { useExplorerStore } from '@/stores/explorer'

const store = useExplorerStore()

onMounted(() => {
  void store.loadMuscles()
})
</script>

<template>
  <section class="explorer">
    <header class="intro animate-in">
      <p class="eyebrow">Explorador muscular</p>
      <h1><span class="gradient-text">Entrena cada músculo</span> con criterio</h1>
      <p class="lead">Pulsa un músculo del mapa para descubrir los ejercicios que lo trabajan.</p>
      <HealthDisclaimer />
    </header>

    <div class="layout">
      <div class="map glass animate-in" style="animation-delay: 0.08s">
        <BodyMap
          :muscles="store.muscles"
          :selected="store.selectedSvgId"
          @select="store.selectMuscle"
        />
      </div>
      <ExercisePanel
        class="results glass animate-in"
        style="animation-delay: 0.16s"
        :muscle-name="store.selectedMuscle?.name ?? null"
        :exercises="store.exercises"
        :loading="store.loading"
        :error="store.error"
      />
    </div>
  </section>
</template>

<style scoped>
.explorer {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}
.intro {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.25em;
  font-size: 0.72rem;
  color: var(--color-accent);
}
h1 {
  margin: 0;
  font-size: clamp(1.9rem, 5vw, 3rem);
  font-weight: 800;
  line-height: 1.1;
}
.lead {
  margin: 0;
  color: var(--color-muted);
  max-width: 55ch;
}
.layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-lg);
  align-items: start;
}
.map {
  display: flex;
  justify-content: center;
  padding: var(--space-lg);
}
.results {
  padding: var(--space-lg);
}
/* Two columns on wider screens: map beside results. */
@media (min-width: 820px) {
  .layout {
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  }
}
</style>
