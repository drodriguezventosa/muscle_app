import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { cancelTrainer, hireTrainer, myTrainer, type Trainer } from '@/api/coaching'
import { useAuthStore } from '@/stores/auth'

/**
 * The student's side of the coaching relationship, held server-side.
 *
 * A student has at most one trainer, and that link is what unlocks their plan —
 * so the answer has to come from the API, not from this browser: it decides what
 * the navigation shows and which routes they may enter.
 */
export const useCoachingStore = defineStore('coaching', () => {
  const trainer = ref<Trainer | null>(null)
  const loaded = ref(false)
  const loading = ref(false)

  const hasTrainer = computed(() => trainer.value !== null)

  /** Read the link once per session; `force` re-reads it after hiring elsewhere. */
  async function load(force = false): Promise<void> {
    const auth = useAuthStore()
    if (!auth.isSignedIn || auth.isTrainer) {
      trainer.value = null
      loaded.value = true
      return
    }
    if (loaded.value && !force) return
    loading.value = true
    try {
      trainer.value = await myTrainer()
      loaded.value = true
    } catch {
      // Leave it unknown rather than claiming they have none: a failed read
      // must not hide the plan of a student who does have a trainer.
      trainer.value = null
    } finally {
      loading.value = false
    }
  }

  async function hire(trainerId: number): Promise<void> {
    trainer.value = await hireTrainer(trainerId)
    loaded.value = true
  }

  async function cancel(): Promise<void> {
    await cancelTrainer()
    trainer.value = null
  }

  /** Called on sign-out: the next student must not inherit this one's trainer. */
  function reset(): void {
    trainer.value = null
    loaded.value = false
  }

  return { trainer, hasTrainer, loaded, loading, load, hire, cancel, reset }
})
