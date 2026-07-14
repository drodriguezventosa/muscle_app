import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { getMuscleExercises, listActiveMuscles, listMuscles } from '@/api/explorer'
import type { Difficulty, Equipment, Exercise, Muscle } from '@/api/types'
import { i18n } from '@/i18n'
import { readCache, writeCache } from '@/lib/localCache'

// Which body figure(s) the map shows. Purely a view concern (front/back is a
// property of the muscle's location, not of an exercise).
export type BodyView = 'front' | 'back' | 'both'

export const useExplorerStore = defineStore('explorer', () => {
  const muscles = ref<Muscle[]>([])
  const selectedSvgId = ref<string | null>(null)
  const exercises = ref<Exercise[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Filters. `view` is client-only; equipment/difficulty are sent to the API.
  const view = ref<BodyView>('both')
  const equipment = ref<Equipment[]>([])
  const difficulty = ref<Difficulty[]>([])
  // svg ids of muscles that have exercises matching the current equipment/level.
  const activeSvgIds = ref<string[]>([])

  const selectedMuscle = computed<Muscle | null>(
    () => muscles.value.find((m) => m.svgId === selectedSvgId.value) ?? null,
  )

  function filters() {
    return { equipment: equipment.value, difficulty: difficulty.value }
  }

  async function refreshActive(): Promise<void> {
    // Highlights are non-critical, so failures are swallowed (the map still
    // renders). With no filters, serve the cached set instantly, then revalidate.
    const noFilters = !equipment.value.length && !difficulty.value.length
    const cacheKey = `active:${i18n.global.locale.value}`
    if (noFilters) {
      const cached = readCache<string[]>(cacheKey)
      if (cached) activeSvgIds.value = cached
    }
    try {
      const ids = (await listActiveMuscles(filters())).map((m) => m.svgId)
      activeSvgIds.value = ids
      if (noFilters) writeCache(cacheKey, ids)
    } catch {
      // keep whatever we have (cached or empty)
    }
  }

  async function loadMuscles(): Promise<void> {
    error.value = null
    // Stale-while-revalidate: paint cached muscles instantly (per locale), then
    // refresh. Only surface an error if we truly have nothing to show.
    const cacheKey = `muscles:${i18n.global.locale.value}`
    const cached = readCache<Muscle[]>(cacheKey)
    if (cached?.length) muscles.value = cached
    try {
      muscles.value = await listMuscles()
      writeCache(cacheKey, muscles.value)
      await refreshActive()
    } catch {
      if (!muscles.value.length) error.value = i18n.global.t('errors.loadMuscles')
    }
  }

  async function selectMuscle(svgId: string): Promise<void> {
    selectedSvgId.value = svgId
    exercises.value = []
    error.value = null
    loading.value = true
    try {
      exercises.value = await getMuscleExercises(svgId, filters())
    } catch {
      error.value = i18n.global.t('errors.loadExercises')
    } finally {
      loading.value = false
    }
  }

  // Re-query active muscles and (if a muscle is open) its filtered exercises.
  async function applyFilters(): Promise<void> {
    await refreshActive()
    if (selectedSvgId.value) await selectMuscle(selectedSvgId.value)
  }

  function toggleValue<T>(list: T[], value: T): T[] {
    return list.includes(value) ? list.filter((v) => v !== value) : [...list, value]
  }

  async function toggleEquipment(value: Equipment): Promise<void> {
    equipment.value = toggleValue(equipment.value, value)
    await applyFilters()
  }

  async function toggleDifficulty(value: Difficulty): Promise<void> {
    difficulty.value = toggleValue(difficulty.value, value)
    await applyFilters()
  }

  async function clearFilters(): Promise<void> {
    equipment.value = []
    difficulty.value = []
    await applyFilters()
  }

  function setView(next: BodyView): void {
    view.value = next
  }

  return {
    muscles,
    selectedSvgId,
    exercises,
    loading,
    error,
    view,
    equipment,
    difficulty,
    activeSvgIds,
    selectedMuscle,
    loadMuscles,
    selectMuscle,
    toggleEquipment,
    toggleDifficulty,
    clearFilters,
    setView,
  }
})
