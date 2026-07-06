import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { getMuscleExercises, listMuscles } from '@/api/explorer'
import type { Exercise, Muscle } from '@/api/types'
import { i18n } from '@/i18n'

export const useExplorerStore = defineStore('explorer', () => {
  const muscles = ref<Muscle[]>([])
  const selectedSvgId = ref<string | null>(null)
  const exercises = ref<Exercise[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const selectedMuscle = computed<Muscle | null>(
    () => muscles.value.find((m) => m.svgId === selectedSvgId.value) ?? null,
  )

  async function loadMuscles(): Promise<void> {
    error.value = null
    try {
      muscles.value = await listMuscles()
    } catch {
      error.value = i18n.global.t('errors.loadMuscles')
    }
  }

  async function selectMuscle(svgId: string): Promise<void> {
    selectedSvgId.value = svgId
    exercises.value = []
    error.value = null
    loading.value = true
    try {
      exercises.value = await getMuscleExercises(svgId)
    } catch {
      error.value = i18n.global.t('errors.loadExercises')
    } finally {
      loading.value = false
    }
  }

  return {
    muscles,
    selectedSvgId,
    exercises,
    loading,
    error,
    selectedMuscle,
    loadMuscles,
    selectMuscle,
  }
})
