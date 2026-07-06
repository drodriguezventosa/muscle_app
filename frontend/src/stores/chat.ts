import { defineStore } from 'pinia'
import { ref } from 'vue'

import { recommend } from '@/api/chat'
import type { Exercise } from '@/api/types'

export interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  exercises?: Exercise[]
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const sending = ref(false)
  const error = ref<string | null>(null)

  async function ask(message: string): Promise<void> {
    const trimmed = message.trim()
    if (!trimmed || sending.value) return

    messages.value.push({ role: 'user', text: trimmed })
    sending.value = true
    error.value = null
    try {
      const recommendation = await recommend(trimmed)
      messages.value.push({
        role: 'assistant',
        text: recommendation.reply,
        exercises: recommendation.exercises,
      })
    } catch {
      error.value = 'No se pudo obtener la recomendación. Inténtalo de nuevo.'
    } finally {
      sending.value = false
    }
  }

  return { messages, sending, error, ask }
})
