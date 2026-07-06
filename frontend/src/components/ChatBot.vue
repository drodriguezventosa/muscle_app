<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Exercise } from '@/api/types'
import VideoModal from '@/components/VideoModal.vue'
import { useChatStore } from '@/stores/chat'
import { useExplorerStore } from '@/stores/explorer'

// Emitted when the user jumps to an exercise, so the widget can close its panel.
const emit = defineEmits<{ navigate: [] }>()

const store = useChatStore()
const explorer = useExplorerStore()
const { t } = useI18n()
const draft = ref('')
const activeVideo = ref<{ url: string; title: string } | null>(null)

function send(): void {
  const message = draft.value
  draft.value = ''
  void store.ask(message)
}

// Select the exercise's primary muscle in the explorer, scroll to it, close chat.
async function goToExercise(exercise: Exercise): Promise<void> {
  const target =
    exercise.targetedMuscles.find((m) => m.role === 'primary') ?? exercise.targetedMuscles[0]
  if (!target) return

  if (explorer.muscles.length === 0) await explorer.loadMuscles()
  const svgId = explorer.muscles.find((m) => m.id === target.muscleId)?.svgId
  if (!svgId) return

  await explorer.selectMuscle(svgId)
  emit('navigate')
  await nextTick()
  document.getElementById('explorer-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div class="chat">
    <p v-if="store.messages.length === 0" class="hint">{{ t('chat.intro') }}</p>

    <ol class="messages" aria-live="polite">
      <li v-for="(message, index) in store.messages" :key="index" :class="['msg', message.role]">
        <p class="bubble">{{ message.text }}</p>
        <ul v-if="message.exercises && message.exercises.length" class="suggestions">
          <li v-for="exercise in message.exercises" :key="exercise.id" class="suggestion">
            <button
              type="button"
              class="link"
              :title="t('chat.viewInExplorer', { name: exercise.name })"
              @click="goToExercise(exercise)"
            >
              {{ exercise.name }}
            </button>
            <span class="tag">{{ t(`equipment.${exercise.equipment}`) }}</span>
            <button
              v-if="exercise.videoUrl"
              type="button"
              class="watch-mini"
              @click="activeVideo = { url: exercise.videoUrl, title: exercise.name }"
            >
              <span aria-hidden="true">▶</span> {{ t('video.watch') }}
            </button>
          </li>
        </ul>
      </li>
    </ol>

    <p v-if="store.error" class="error" role="alert">{{ store.error }}</p>

    <form class="composer" @submit.prevent="send">
      <label class="sr-only" for="chat-input">{{ t('chat.inputLabel') }}</label>
      <input
        id="chat-input"
        v-model="draft"
        type="text"
        maxlength="500"
        :placeholder="t('chat.placeholder')"
        :disabled="store.sending"
      />
      <button type="submit" :disabled="store.sending || !draft.trim()">
        {{ store.sending ? '…' : '➤' }}
      </button>
    </form>

    <VideoModal
      v-if="activeVideo"
      :url="activeVideo.url"
      :title="activeVideo.title"
      @close="activeVideo = null"
    />
  </div>
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.hint {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.9rem;
}
.messages {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  max-height: 46vh;
  overflow-y: auto;
}
.msg {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  animation: fade-in-up 0.3s ease both;
}
.msg.user {
  align-items: flex-end;
}
.bubble {
  margin: 0;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  max-width: 92%;
  white-space: pre-line;
  font-size: 0.92rem;
}
.msg.user .bubble {
  background: var(--gradient);
  color: #06121a;
  font-weight: 600;
}
.msg.assistant .bubble {
  background: var(--color-surface-strong);
  border: 1px solid var(--color-border);
  color: var(--color-text);
}
.suggestions {
  list-style: none;
  margin: var(--space-xs) 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  font-size: 0.85rem;
}
.suggestion {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-xs);
}
.link {
  padding: 0;
  border: none;
  background: none;
  color: var(--color-text);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
  border-bottom: 1px solid transparent;
  transition:
    color 0.15s ease,
    border-color 0.15s ease;
}
.link:hover {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
}
.tag {
  font-size: 0.7rem;
  color: var(--color-accent);
}
.watch-mini {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-text);
  font: inherit;
  font-size: 0.72rem;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}
.watch-mini:hover {
  border-color: var(--color-accent);
  box-shadow: var(--glow);
}
.error {
  color: var(--color-danger);
  margin: 0;
  font-size: 0.9rem;
}
.composer {
  display: flex;
  gap: var(--space-sm);
}
.composer input {
  flex: 1;
  min-width: 0;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text);
  font: inherit;
}
.composer input:focus-visible {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: var(--glow);
}
.composer button {
  width: 44px;
  border: none;
  border-radius: 999px;
  background: var(--gradient);
  color: #06121a;
  font-size: 1rem;
  cursor: pointer;
}
.composer button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}
</style>
