<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <header class="app-header">
    <span class="brand">💪 MuscleApp</span>
  </header>
  <main class="app-main">
    <RouterView />
  </main>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}
.brand {
  font-weight: 600;
}
.app-main {
  max-width: 960px;
  margin: 0 auto;
  padding: var(--space-lg);
}
</style>
