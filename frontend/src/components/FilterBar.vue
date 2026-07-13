<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Difficulty, Equipment } from '@/api/types'
import FilterDropdown from '@/components/FilterDropdown.vue'
import { useExplorerStore, type BodyView } from '@/stores/explorer'

const { t } = useI18n()
const store = useExplorerStore()

// Equipment types present in the catalog (the filter only offers useful values).
const EQUIPMENT: Equipment[] = ['bodyweight', 'dumbbell', 'barbell', 'machine', 'cable']
const LEVELS: Difficulty[] = ['beginner', 'intermediate', 'advanced']
const VIEWS: BodyView[] = ['both', 'front', 'back']

const viewOptions = computed(() => VIEWS.map((v) => ({ value: v, label: t(`filters.view_${v}`) })))
const equipmentOptions = computed(() =>
  EQUIPMENT.map((e) => ({ value: e, label: t(`equipment.${e}`) })),
)
const levelOptions = computed(() => LEVELS.map((d) => ({ value: d, label: t(`difficulty.${d}`) })))

const hasFilters = computed(() => store.equipment.length > 0 || store.difficulty.length > 0)
</script>

<template>
  <section class="filters" :aria-label="t('filters.title')">
    <FilterDropdown
      :label="t('filters.view')"
      :options="viewOptions"
      :selected="[store.view]"
      @select="(v) => store.setView(v as BodyView)"
    />
    <FilterDropdown
      :label="t('filters.material')"
      :options="equipmentOptions"
      :selected="store.equipment"
      multiple
      @select="(e) => store.toggleEquipment(e as Equipment)"
    />
    <FilterDropdown
      :label="t('filters.level')"
      :options="levelOptions"
      :selected="store.difficulty"
      multiple
      @select="(d) => store.toggleDifficulty(d as Difficulty)"
    />

    <button v-if="hasFilters" type="button" class="clear" @click="store.clearFilters()">
      {{ t('filters.clear') }}
    </button>
  </section>
</template>

<style scoped>
.filters {
  position: relative;
  /* Above the body figure so the open dropdown overlays it. */
  z-index: 30;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--color-border);
}
.clear {
  margin-left: auto;
  padding: 6px 12px;
  border: none;
  background: transparent;
  color: var(--color-muted);
  font: inherit;
  font-size: 0.82rem;
  cursor: pointer;
  text-decoration: underline;
}
.clear:hover {
  color: var(--color-text);
}
</style>
