<script setup lang="ts">
import { RouterView } from 'vue-router'

import ChatWidget from '@/components/ChatWidget.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
</script>

<template>
  <header class="app-header">
    <span class="brand">
      <span class="logo" aria-hidden="true">◆</span>
      <span class="gradient-text">MuscleApp</span>
    </span>
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
  background: rgba(7, 11, 22, 0.6);
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
