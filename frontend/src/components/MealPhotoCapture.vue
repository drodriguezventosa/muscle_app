<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'

// Take a meal photo with the device camera, or fall back to picking a file.
// getUserMedia works on desktop (webcam) and mobile (rear camera) over HTTPS or
// localhost; if it is unavailable or denied we show the file picker instead.
const emit = defineEmits<{ captured: [blob: Blob] }>()
// `busy` is owned by the parent (it runs the upload), so the buttons stay
// disabled until the analysis finishes and a double submit is impossible.
const props = withDefaults(defineProps<{ busy?: boolean }>(), { busy: false })

const { t } = useI18n()

// Downscale before uploading: keeps the request well under the server's 5 MB
// limit and cuts the provider's token cost, with no visible loss for food.
const MAX_EDGE = 1280
const JPEG_QUALITY = 0.85

const open = ref(false)
const starting = ref(false)
// Which button produced the photo, so the busy state is shown on that one.
const source = ref<'camera' | 'upload' | null>(null)
const error = ref<string | null>(null)
const video = ref<HTMLVideoElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
let stream: MediaStream | null = null

const supported = Boolean(globalThis.navigator?.mediaDevices?.getUserMedia)

function stop(): void {
  stream?.getTracks().forEach((track) => track.stop()) // release the camera light
  stream = null
}

function close(): void {
  stop()
  open.value = false
  error.value = null
}

async function start(): Promise<void> {
  error.value = null
  if (!supported) {
    pickFile()
    return
  }
  open.value = true
  starting.value = true
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1280 } },
      audio: false,
    })
    if (video.value) {
      video.value.srcObject = stream
      await video.value.play()
    }
  } catch {
    // Denied, in use, or no camera: offer the file picker as a way out.
    error.value = t('nutrition.photo.cameraError')
    stop()
  } finally {
    starting.value = false
  }
}

/** Draw the current frame, downscaled, and hand it over as a JPEG blob. */
function shoot(): void {
  const el = video.value
  if (!el || !el.videoWidth) return
  const scale = Math.min(1, MAX_EDGE / Math.max(el.videoWidth, el.videoHeight))
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(el.videoWidth * scale)
  canvas.height = Math.round(el.videoHeight * scale)
  canvas.getContext('2d')?.drawImage(el, 0, 0, canvas.width, canvas.height)
  canvas.toBlob(
    (blob) => {
      if (blob) {
        source.value = 'camera'
        emit('captured', blob)
      }
      close()
    },
    'image/jpeg',
    JPEG_QUALITY,
  )
}

/** True while the parent analyses a photo that came from this button. */
function busyOn(which: 'camera' | 'upload'): boolean {
  return props.busy && source.value === which
}

function pickFile(): void {
  fileInput.value?.click()
}

function onFile(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    // The picker is also reachable from the camera modal's error state, but the
    // photo came from a file either way.
    source.value = 'upload'
    emit('captured', file)
  }
  input.value = '' // allow re-picking the same file
  close()
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') close()
}

onBeforeUnmount(stop)
</script>

<template>
  <div class="capture">
    <button type="button" class="cap-btn primary" :disabled="props.busy" @click="start">
      <span v-if="busyOn('camera')" class="cap-spinner" aria-hidden="true"></span>
      <span v-else aria-hidden="true">📷</span>
      {{ busyOn('camera') ? t('nutrition.photo.analyzing') : t('nutrition.photo.take') }}
    </button>
    <button type="button" class="cap-btn" :disabled="props.busy" @click="pickFile">
      <span v-if="busyOn('upload')" class="cap-spinner on-light" aria-hidden="true"></span>
      <span v-else aria-hidden="true">🖼️</span>
      {{ busyOn('upload') ? t('nutrition.photo.analyzing') : t('nutrition.photo.upload') }}
    </button>
    <!-- `capture` hints the rear camera on mobile when used as the fallback -->
    <input
      ref="fileInput"
      class="sr-only"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      capture="environment"
      @change="onFile"
    />

    <Teleport to="body">
      <div v-if="open" class="cam-overlay" role="dialog" aria-modal="true" @keydown="onKeydown">
        <div class="cam-box glass">
          <video ref="video" class="cam-video" autoplay muted playsinline></video>
          <p v-if="starting" class="cam-hint">{{ t('nutrition.photo.starting') }}</p>
          <p v-if="error" class="cam-error" role="alert">{{ error }}</p>
          <div class="cam-actions">
            <button type="button" class="cap-btn" @click="close">
              {{ t('nutrition.photo.cancel') }}
            </button>
            <button v-if="error" type="button" class="cap-btn primary" @click="pickFile">
              {{ t('nutrition.photo.upload') }}
            </button>
            <button
              v-else
              type="button"
              class="cap-btn primary"
              :disabled="starting"
              @click="shoot"
            >
              {{ t('nutrition.photo.shoot') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.capture {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}
.cap-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: 8px 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
  font-size: 0.88rem;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}
.cap-btn:hover:not(:disabled) {
  border-color: var(--color-accent);
  box-shadow: var(--glow);
}
.cap-btn:disabled {
  opacity: 0.6;
  cursor: default;
}
.cap-btn.primary {
  background: var(--gradient);
  border-color: transparent;
  color: #06121a;
  font-weight: 700;
}
/* In-button spinner, tinted for the gradient background. */
.cap-spinner {
  display: inline-block;
  flex: none;
  width: 13px;
  height: 13px;
  border: 2px solid rgba(6, 18, 26, 0.3);
  border-top-color: #06121a;
  border-radius: 50%;
  animation: cap-rotate 0.7s linear infinite;
}
/* Same spinner on the secondary (light) button, tinted with the accent. */
.cap-spinner.on-light {
  border-color: var(--color-border);
  border-top-color: var(--color-accent);
}
@keyframes cap-rotate {
  to {
    transform: rotate(360deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .cap-spinner {
    animation-duration: 2s;
  }
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
.cam-overlay {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: var(--space-md);
  background: rgba(2, 6, 23, 0.72);
}
.cam-box {
  width: min(94vw, 560px);
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  background: var(--color-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md, 14px);
}
.cam-video {
  width: 100%;
  max-height: 60vh;
  border-radius: var(--radius-sm);
  background: #000;
  object-fit: cover;
}
.cam-hint {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.85rem;
}
.cam-error {
  margin: 0;
  color: var(--color-danger);
  font-size: 0.88rem;
}
.cam-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}
</style>
