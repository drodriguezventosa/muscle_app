<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  url: string
  title: string
}>()

const emit = defineEmits<{ close: [] }>()

const { t, locale } = useI18n()

// Extract the YouTube video id from a watch/share URL.
const videoId = computed(() => {
  const match = props.url.match(/(?:v=|youtu\.be\/|embed\/)([\w-]{11})/)
  return match ? match[1] : ''
})

// Privacy-friendly embed, autoplaying since the user explicitly opened it.
// Force captions in the UI language so a video in the "other" language still
// shows subtitles the user can follow (cc_lang_pref + cc_load_policy).
const embedSrc = computed(
  () =>
    `https://www.youtube-nocookie.com/embed/${videoId.value}` +
    `?autoplay=1&rel=0&cc_load_policy=1&cc_lang_pref=${locale.value}&hl=${locale.value}`,
)

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') emit('close')
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <div
      class="overlay"
      role="dialog"
      aria-modal="true"
      :aria-label="t('video.dialogLabel')"
      @click.self="emit('close')"
    >
      <div class="dialog glass">
        <header class="head">
          <strong class="title">{{ title }}</strong>
          <button class="close" type="button" :aria-label="t('video.close')" @click="emit('close')">
            ✕
          </button>
        </header>
        <div class="frame">
          <iframe
            :src="embedSrc"
            :title="title"
            allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen
            referrerpolicy="strict-origin-when-cross-origin"
          ></iframe>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-md);
  background: rgba(4, 7, 15, 0.72);
  backdrop-filter: blur(6px);
  animation: fade-in 0.2s ease both;
}
.dialog {
  width: min(92vw, 860px);
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  animation: pop-in 0.24s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.head {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.title {
  font-size: 1.05rem;
}
.close {
  margin-left: auto;
  background: transparent;
  border: none;
  color: var(--color-muted);
  font-size: 1.1rem;
  cursor: pointer;
}
.close:hover {
  color: var(--color-text);
}
.frame {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: #000;
}
.frame iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}
@keyframes fade-in {
  from {
    opacity: 0;
  }
}
@keyframes pop-in {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.96);
  }
}
@media (prefers-reduced-motion: reduce) {
  .overlay,
  .dialog {
    animation: none;
  }
}
</style>
