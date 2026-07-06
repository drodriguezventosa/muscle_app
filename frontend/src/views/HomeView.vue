<script setup lang="ts">
import HealthDisclaimer from '@/components/HealthDisclaimer.vue'
</script>

<template>
  <section class="hero">
    <h1>Entrena cada músculo con criterio</h1>
    <p class="lead">
      Explora el cuerpo humano y descubre qué ejercicios trabajan cada músculo. Pregunta al
      asistente qué quieres entrenar y recibe recomendaciones.
    </p>
    <HealthDisclaimer />
  </section>
</template>

<style scoped>
.hero {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
h1 {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  margin: 0;
}
.lead {
  color: var(--color-muted);
  max-width: 60ch;
}
</style>
