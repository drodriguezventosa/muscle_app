<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useChatStore } from '@/stores/chat'

const store = useChatStore()
const { t } = useI18n()
const draft = ref('')

function send(): void {
  const message = draft.value
  draft.value = ''
  void store.ask(message)
}
</script>

<template>
  <div class="chat">
    <p v-if="store.messages.length === 0" class="hint">{{ t('chat.intro') }}</p>

    <ol class="messages" aria-live="polite">
      <li v-for="(message, index) in store.messages" :key="index" :class="['msg', message.role]">
        <p class="bubble">{{ message.text }}</p>
        <ul v-if="message.exercises && message.exercises.length" class="suggestions">
          <li v-for="exercise in message.exercises" :key="exercise.id">
            {{ exercise.name }} <span class="tag">{{ t(`equipment.${exercise.equipment}`) }}</span>
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
  margin: 0;
  padding-left: var(--space-md);
  font-size: 0.85rem;
  color: var(--color-muted);
}
.tag {
  font-size: 0.7rem;
  color: var(--color-accent);
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
