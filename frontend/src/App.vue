<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

import ChatWidget from '@/components/ChatWidget.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'

const { t } = useI18n()
const route = useRoute()

// Mobile navigation menu (hamburger). Hidden on desktop via CSS.
const menuOpen = ref(false)

// Close the menu after navigating (covers link taps, including the active one).
watch(
  () => route.path,
  () => (menuOpen.value = false),
)

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') menuOpen.value = false
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <header class="app-header">
    <span class="brand">
      <span class="logo" aria-hidden="true">◆</span>
      <span class="gradient-text">MuscleApp</span>
    </span>
    <nav id="primary-nav" class="nav" :class="{ 'nav--open': menuOpen }" @click="menuOpen = false">
      <RouterLink to="/">{{ t('nav.explorer') }}</RouterLink>
      <RouterLink to="/workouts">{{ t('nav.workouts') }}</RouterLink>
      <RouterLink to="/nutrition">{{ t('nav.nutrition') }}</RouterLink>
      <RouterLink to="/progress">{{ t('nav.progress') }}</RouterLink>
      <RouterLink to="/trainers">{{ t('nav.trainers') }}</RouterLink>
    </nav>
    <ThemeToggle />
    <LanguageSwitcher />
    <button
      class="nav-toggle"
      type="button"
      :aria-label="t('nav.menu')"
      :aria-expanded="menuOpen"
      aria-controls="primary-nav"
      @click="menuOpen = !menuOpen"
    >
      <span aria-hidden="true">{{ menuOpen ? '✕' : '☰' }}</span>
    </button>
  </header>
  <main class="app-main">
    <RouterView />
  </main>

  <!-- Floating assistant, available on every page -->
  <ChatWidget />
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-header);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(var(--blur));
  -webkit-backdrop-filter: blur(var(--blur));
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  font-weight: 800;
  font-size: 1.15rem;
  letter-spacing: 0.02em;
}
.nav {
  display: flex;
  gap: var(--space-md);
  margin-right: auto;
  margin-left: var(--space-lg);
}
.nav a {
  color: var(--color-muted);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 600;
  padding: 4px 2px;
  border-bottom: 2px solid transparent;
  transition:
    color 0.15s ease,
    border-color 0.15s ease;
}
.nav a:hover {
  color: var(--color-text);
}
.nav a.router-link-active {
  color: var(--color-text);
  border-bottom-color: var(--color-accent);
}
.logo {
  color: var(--color-accent);
  filter: drop-shadow(var(--glow));
  animation: spin 8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
/* Hamburger button: hidden on desktop, shown on mobile. */
.nav-toggle {
  display: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 1.15rem;
  line-height: 1;
  cursor: pointer;
}
.nav-toggle:hover {
  border-color: var(--color-accent);
}
.app-main {
  max-width: 1040px;
  margin: 0 auto;
  padding: var(--space-lg);
}

/* Mobile / tablet portrait: collapse the nav behind a hamburger menu. */
@media (max-width: 820px) {
  .app-header {
    gap: var(--space-sm);
    padding: var(--space-sm) var(--space-md);
  }
  .brand {
    margin-right: auto;
    font-size: 1.05rem;
  }
  .nav-toggle {
    display: inline-flex;
  }
  /* Dropdown panel below the header; the sticky header is its containing block. */
  .nav {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    display: none;
    flex-direction: column;
    gap: var(--space-xs);
    margin: 0;
    padding: var(--space-sm);
    background: var(--color-elevated);
    border-bottom: 1px solid var(--color-border);
    box-shadow: var(--shadow-sm);
  }
  .nav--open {
    display: flex;
  }
  .nav a {
    padding: var(--space-sm) var(--space-md);
    border-bottom: none;
    border-radius: var(--radius-sm);
  }
  .nav a.router-link-active {
    background: var(--color-accent-soft);
  }
  .app-main {
    padding: var(--space-md);
  }
}
</style>
