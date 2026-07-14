<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useI18n } from 'vue-i18n'

import ChatWidget from '@/components/ChatWidget.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'

const { t } = useI18n()
</script>

<template>
  <header class="app-header">
    <span class="brand">
      <span class="logo" aria-hidden="true">◆</span>
      <span class="gradient-text">MuscleApp</span>
    </span>
    <nav class="nav">
      <RouterLink to="/">{{ t('nav.explorer') }}</RouterLink>
      <RouterLink to="/workouts">{{ t('nav.workouts') }}</RouterLink>
      <RouterLink to="/progress">{{ t('nav.progress') }}</RouterLink>
      <RouterLink to="/trainers">{{ t('nav.trainers') }}</RouterLink>
    </nav>
    <ThemeToggle />
    <LanguageSwitcher />
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
.app-main {
  max-width: 1040px;
  margin: 0 auto;
  padding: var(--space-lg);
}
</style>
