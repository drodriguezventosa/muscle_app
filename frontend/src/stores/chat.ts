import { defineStore } from 'pinia'
import { ref } from 'vue'

import { recommend } from '@/api/chat'
import { recommendMeals } from '@/api/nutrition'
import type { Exercise, Food } from '@/api/types'
import { i18n } from '@/i18n'

export type ChatMode = 'exercise' | 'meal'

export interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  exercises?: Exercise[]
  foods?: Food[]
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const sending = ref(false)
  const error = ref<string | null>(null)

  function reset(): void {
    messages.value = []
    error.value = null
  }

  async function ask(message: string, mode: ChatMode = 'exercise'): Promise<void> {
    const trimmed = message.trim()
    if (!trimmed || sending.value) return

    messages.value.push({ role: 'user', text: trimmed })
    sending.value = true
    error.value = null
    try {
      if (mode === 'meal') {
        const rec = await recommendMeals(trimmed)
        messages.value.push({ role: 'assistant', text: rec.reply, foods: rec.foods })
      } else {
        const rec = await recommend(trimmed)
        messages.value.push({ role: 'assistant', text: rec.reply, exercises: rec.exercises })
      }
    } catch {
      error.value = i18n.global.t('errors.recommend')
    } finally {
      sending.value = false
    }
  }

  return { messages, sending, error, ask, reset }
})
