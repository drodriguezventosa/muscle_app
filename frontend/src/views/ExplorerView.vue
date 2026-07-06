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
    <header class="intro">
      <h1>Explora tus músculos</h1>
      <p class="lead">Pulsa un músculo del mapa para ver los ejercicios que lo trabajan.</p>
      <HealthDisclaimer />
    </header>

    <div class="layout">
      <div class="map">
        <BodyMap
          :muscles="store.muscles"
          :selected="store.selectedSvgId"
          @select="store.selectMuscle"
        />
      </div>
      <ExercisePanel
        class="results"
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
h1 {
  margin: 0;
  font-size: clamp(1.6rem, 4vw, 2.3rem);
}
.lead {
  margin: 0;
  color: var(--color-muted);
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
}
/* Two columns on wider screens: map beside results. */
@media (min-width: 760px) {
  .layout {
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  }
}
</style>
