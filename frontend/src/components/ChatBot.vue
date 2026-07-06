<script setup lang="ts">
import { ref } from 'vue'

import { useChatStore } from '@/stores/chat'

const store = useChatStore()
const draft = ref('')

function send(): void {
  const message = draft.value
  draft.value = ''
  void store.ask(message)
}
</script>

<template>
  <section class="chat" aria-label="Asistente de recomendaciones">
    <h2 class="title">Asistente</h2>
    <p class="hint">Pregunta qué quieres entrenar y te recomiendo ejercicios.</p>

    <ol class="messages" aria-live="polite">
      <li v-for="(message, index) in store.messages" :key="index" :class="['msg', message.role]">
        <p class="bubble">{{ message.text }}</p>
        <ul v-if="message.exercises && message.exercises.length" class="suggestions">
          <li v-for="exercise in message.exercises" :key="exercise.id">
            {{ exercise.name }} <span class="tag">{{ exercise.equipment }}</span>
          </li>
        </ul>
      </li>
    </ol>

    <p v-if="store.error" class="error" role="alert">{{ store.error }}</p>

    <form class="composer" @submit.prevent="send">
      <label class="sr-only" for="chat-input">Tu consulta</label>
      <input
        id="chat-input"
        v-model="draft"
        type="text"
        maxlength="500"
        placeholder="p. ej. quiero entrenar pecho en casa sin material"
        :disabled="store.sending"
      />
      <button type="submit" :disabled="store.sending || !draft.trim()">
        {{ store.sending ? '…' : 'Enviar' }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: var(--space-md);
}
.title {
  margin: 0;
  font-size: 1.2rem;
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
  max-height: 320px;
  overflow-y: auto;
}
.msg {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.msg.user {
  align-items: flex-end;
}
.bubble {
  margin: 0;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius);
  max-width: 90%;
  white-space: pre-line;
}
.msg.user .bubble {
  background: var(--color-accent);
  color: #fff;
}
.msg.assistant .bubble {
  background: var(--color-accent-soft);
  color: var(--color-text);
}
.suggestions {
  margin: 0;
  padding-left: var(--space-md);
  font-size: 0.9rem;
}
.tag {
  font-size: 0.7rem;
  color: var(--color-muted);
}
.error {
  color: #b91c1c;
  margin: 0;
}
.composer {
  display: flex;
  gap: var(--space-sm);
}
.composer input {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font: inherit;
}
.composer button {
  padding: var(--space-sm) var(--space-md);
  border: none;
  border-radius: var(--radius);
  background: var(--color-accent);
  color: #fff;
  font: inherit;
  cursor: pointer;
}
.composer button:disabled {
  opacity: 0.5;
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
