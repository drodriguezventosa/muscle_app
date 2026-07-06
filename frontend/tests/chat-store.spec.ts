import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/chat', () => ({ recommend: vi.fn() }))

import { recommend } from '@/api/chat'
import { useChatStore } from '@/stores/chat'

describe('chat store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('appends a user message and the assistant reply', async () => {
    vi.mocked(recommend).mockResolvedValue({ reply: 'Te recomiendo…', exercises: [] })
    const store = useChatStore()
    await store.ask('quiero entrenar pecho')
    expect(store.messages.map((m) => m.role)).toEqual(['user', 'assistant'])
    expect(store.messages[1].text).toBe('Te recomiendo…')
    expect(store.sending).toBe(false)
  })

  it('ignores empty messages', async () => {
    const store = useChatStore()
    await store.ask('   ')
    expect(store.messages).toEqual([])
    expect(recommend).not.toHaveBeenCalled()
  })

  it('sets an error when the request fails', async () => {
    vi.mocked(recommend).mockRejectedValue(new Error('network'))
    const store = useChatStore()
    await store.ask('hola')
    expect(store.error).not.toBeNull()
    expect(store.sending).toBe(false)
  })
})
