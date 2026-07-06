<script setup lang="ts">
import type { Exercise } from '@/api/types'

defineProps<{
  muscleName: string | null
  exercises: Exercise[]
  loading: boolean
  error: string | null
}>()
</script>

<template>
  <section class="panel" aria-live="polite">
    <h2 v-if="muscleName" class="title">{{ muscleName }}</h2>
    <p v-else class="hint">Selecciona un músculo en el mapa para ver sus ejercicios.</p>

    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <p v-else-if="loading" class="hint">Cargando ejercicios…</p>
    <p v-else-if="muscleName && exercises.length === 0" class="hint">
      Todavía no hay ejercicios para este músculo.
    </p>

    <ul v-if="exercises.length" class="list">
      <li v-for="exercise in exercises" :key="exercise.id" class="card">
        <div class="card-head">
          <h3 class="card-title">{{ exercise.name }}</h3>
          <div class="badges">
            <span class="badge">{{ exercise.equipment }}</span>
            <span class="badge badge-soft">{{ exercise.difficulty }}</span>
          </div>
        </div>
        <p class="card-desc">{{ exercise.description }}</p>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.title {
  margin: 0;
  font-size: 1.4rem;
}
.hint {
  color: var(--color-muted);
  margin: 0;
}
.error {
  color: #b91c1c;
  margin: 0;
}
.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: var(--space-md);
  box-shadow: var(--shadow-sm);
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-sm);
  flex-wrap: wrap;
}
.card-title {
  margin: 0;
  font-size: 1.05rem;
}
.badges {
  display: flex;
  gap: var(--space-xs);
}
.badge {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-accent);
  color: #fff;
}
.badge-soft {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}
.card-desc {
  margin: var(--space-sm) 0 0;
  color: var(--color-muted);
}
</style>
