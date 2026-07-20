<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import ChatBot from '@/components/ChatBot.vue'

const { t } = useI18n()
const open = ref(false)

function toggle(): void {
  open.value = !open.value
}
</script>

<template>
  <div class="widget">
    <Transition name="panel">
      <section v-if="open" class="panel glass" role="dialog" :aria-label="t('chat.title')">
        <header class="panel-head">
          <span class="status" aria-hidden="true"></span>
          <strong class="gradient-text">{{ t('chat.title') }}</strong>
          <button
            class="close"
            type="button"
            data-testid="chat-close"
            :aria-label="t('chat.close')"
            @click="toggle"
          >
            ✕
          </button>
        </header>
        <ChatBot @navigate="open = false" />
      </section>
    </Transition>

    <button
      class="bubble"
      type="button"
      data-testid="chat-toggle"
      :aria-expanded="open"
      :aria-label="t('chat.open')"
      @click="toggle"
    >
      <span class="bubble-icon">{{ open ? '✕' : '🤖' }}</span>
    </button>
  </div>
</template>

<style scoped>
.widget {
  position: fixed;
  right: clamp(1rem, 3vw, 2rem);
  bottom: clamp(1rem, 3vw, 2rem);
  z-index: 60;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-md);
}
.bubble {
  width: 60px;
  height: 60px;
  border: none;
  border-radius: 50%;
  background: var(--gradient);
  color: #06121a;
  font-size: 1.5rem;
  cursor: pointer;
  align-self: flex-end;
  box-shadow: var(--glow-violet);
  animation: pulse-glow 2.6s ease-out infinite;
  transition: transform 0.2s ease;
}
.bubble:hover {
  transform: scale(1.08) rotate(4deg);
}
.bubble-icon {
  display: inline-block;
  line-height: 1;
}
.panel {
  width: min(92vw, 380px);
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.panel-head {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 1.05rem;
}
.status {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 8px #34d399;
}
.close {
  margin-left: auto;
  background: transparent;
  border: none;
  color: var(--color-muted);
  font-size: 1rem;
  cursor: pointer;
}
.close:hover {
  color: var(--color-text);
}

/* Expand/collapse animation, anchored to the bottom-right bubble. */
.panel-enter-active,
.panel-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
  transform-origin: bottom right;
}
.panel-enter-from,
.panel-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.92);
}

@media (prefers-reduced-motion: reduce) {
  .bubble {
    animation: none;
  }
}
</style>
