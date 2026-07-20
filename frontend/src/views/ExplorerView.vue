<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BodyMap from '@/components/BodyMap.vue'
import ExercisePanel from '@/components/ExercisePanel.vue'
import FilterBar from '@/components/FilterBar.vue'
import HealthDisclaimer from '@/components/HealthDisclaimer.vue'
import { useExplorerStore } from '@/stores/explorer'

const store = useExplorerStore()
const { t, locale } = useI18n()

onMounted(() => {
  void store.loadMuscles()
})

// Re-fetch localized content when the language changes.
watch(locale, () => {
  void store.loadMuscles()
  if (store.selectedSvgId) {
    // Force: same muscle, but its exercises must be re-fetched in the new locale.
    void store.selectMuscle(store.selectedSvgId, true)
  }
})
</script>

<template>
  <section class="explorer">
    <header class="intro animate-in">
      <p class="eyebrow">{{ t('explorer.eyebrow') }}</p>
      <h1>
        <span class="gradient-text">{{ t('explorer.titleHighlight') }}</span>
        {{ t('explorer.titleRest') }}
      </h1>
      <p class="lead">{{ t('explorer.lead') }}</p>
      <HealthDisclaimer />
    </header>

    <div class="layout">
      <div class="map glass animate-in" style="animation-delay: 0.08s">
        <FilterBar />
        <div class="map-body">
          <BodyMap
            :muscles="store.muscles"
            :selected="store.selectedSvgId"
            :active-svg-ids="store.activeSvgIds"
            :view="store.view"
            @select="store.selectMuscle"
          />
        </div>
      </div>
      <ExercisePanel
        id="explorer-panel"
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
  /* Filters sit as a header inside the body card; the figure centres below. */
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: visible;
}
/* On desktop keep the body card in view while the exercise list scrolls, and
   stretch both columns to the same height (driven by the exercise list). */
@media (min-width: 820px) {
  .layout {
    align-items: stretch;
  }
  .map {
    position: sticky;
    top: var(--space-md);
  }
}
.map-body {
  flex: 1;
  display: flex;
  align-items: center;
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
