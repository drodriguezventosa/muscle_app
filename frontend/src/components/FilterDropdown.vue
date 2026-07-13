<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

interface Option {
  value: string
  label: string
}

const props = defineProps<{
  label: string
  options: Option[]
  selected: string[]
  // Single-select behaves like a radio group (e.g. the front/back view).
  multiple?: boolean
}>()

const emit = defineEmits<{ select: [value: string] }>()

const open = ref(false)
const root = ref<HTMLElement | null>(null)

function toggle(): void {
  open.value = !open.value
}

// Close when clicking outside (same pattern as LanguageSwitcher).
function onDocumentClick(event: MouseEvent): void {
  if (root.value && !root.value.contains(event.target as Node)) open.value = false
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))

function isSelected(value: string): boolean {
  return props.selected.includes(value)
}

function onPick(value: string): void {
  emit('select', value)
  if (!props.multiple) open.value = false
}
</script>

<template>
  <div ref="root" class="dropdown">
    <button
      type="button"
      class="trigger"
      :class="{ active: selected.length > 0 && multiple }"
      :aria-expanded="open"
      aria-haspopup="true"
      @click="toggle"
    >
      <span class="text">{{ label }}</span>
      <span v-if="multiple && selected.length" class="count">{{ selected.length }}</span>
      <span class="caret" aria-hidden="true">▾</span>
    </button>

    <Transition name="menu">
      <ul v-if="open" class="menu" role="menu">
        <li v-for="option in options" :key="option.value">
          <button
            type="button"
            class="option"
            role="menuitemcheckbox"
            :aria-checked="isSelected(option.value)"
            @click="onPick(option.value)"
          >
            <span class="box" :class="{ round: !multiple, on: isSelected(option.value) }">
              <span v-if="isSelected(option.value)" aria-hidden="true">✓</span>
            </span>
            {{ option.label }}
          </button>
        </li>
      </ul>
    </Transition>
  </div>
</template>

<style scoped>
.dropdown {
  position: relative;
}
.trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: var(--color-text);
  font: inherit;
  font-size: 0.85rem;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}
.trigger:hover,
.trigger[aria-expanded='true'] {
  border-color: var(--color-accent);
}
.trigger.active {
  border-color: var(--color-accent);
  box-shadow: var(--glow);
}
.count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--gradient);
  color: #06121a;
  font-size: 0.7rem;
  font-weight: 700;
}
.caret {
  font-size: 0.7rem;
  color: var(--color-muted);
}
.menu {
  position: absolute;
  z-index: 30;
  top: calc(100% + 6px);
  left: 0;
  min-width: 180px;
  margin: 0;
  padding: var(--space-xs);
  list-style: none;
  /* Opaque surface: a dropdown must not let content behind it show through. */
  background: #0e1626;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
}
.option {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  width: 100%;
  padding: 7px 10px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text);
  font: inherit;
  font-size: 0.85rem;
  text-align: left;
  cursor: pointer;
}
.option:hover {
  background: rgba(255, 255, 255, 0.06);
}
.box {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 0.7rem;
  color: #06121a;
  flex-shrink: 0;
}
.box.round {
  border-radius: 50%;
}
.box.on {
  background: var(--gradient);
  border-color: transparent;
}
.menu-enter-active,
.menu-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
  transform-origin: top;
}
.menu-enter-from,
.menu-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}
</style>
