<script setup lang="ts">
// Legally-relevant notice: exercise guidance is not medical advice.
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <p class="disclaimer" role="note">⚕️ {{ t('disclaimer') }}</p>
</template>

<style scoped>
.disclaimer {
  font-size: 0.85rem;
  color: var(--color-muted);
  background: var(--color-accent-soft);
  border-radius: var(--radius);
  padding: var(--space-sm) var(--space-md);
  margin: 0;
}
</style>
