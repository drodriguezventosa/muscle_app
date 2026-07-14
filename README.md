# MuscleApp 💪

Aplicación web para explorar los músculos del cuerpo y descubrir qué ejercicios trabajarlos, con un **chatbot de recomendaciones** basado en IA (RAG). Proyecto de Trabajo Fin de Máster.

> ⚕️ **Aviso**: las recomendaciones de ejercicio son orientativas y **no constituyen consejo médico**. Consulta a un profesional antes de iniciar cualquier programa de entrenamiento.

## Características (MVP)

- 🗺️ **Explorador interactivo** del cuerpo humano (SVG) con figura anatómica, popup por
  grupo muscular y **filtros** (vista frente/espalda, material, nivel) — sin registro.
- 🎬 Cada ejercicio con **vídeo de ejemplo** (subtítulos en tu idioma) o **pasos** paso a paso.
- 🤖 **Chatbot** que recomienda ejercicios según tu objetivo, músculo y material disponible.
- 🏋️ **Generador de rutinas** por objetivo (pérdida de grasa / hipertrofia / fuerza) a partir
  de tus datos (altura, peso, nivel), con IMC.
- 📈 **Progreso**: registra el peso por ejercicio y sigue tu evolución con sobrecarga
  progresiva (guardado en tu dispositivo).
- 👤 **Entrenadores** (vista previa): contratar un entrenador y panel para gestionar alumnos.
- 🌗 **Modo claro/oscuro** y 🌍 **bilingüe** (ES/EN).
- 🎨 Interfaz **moderna, minimalista y responsive**.

_Auth, suscripciones y entrenadores personales (reales) están planificados como fase futura._

## Stack

FastAPI · Vue 3 + Vite · PostgreSQL + pgvector · Ollama/Gemini · Docker

## Arranque rápido (desarrollo)

```bash
cp .env.example .env
docker compose up --build
# Frontend: http://localhost:5173
# API + docs: http://localhost:8000/api/v1 · http://localhost:8000/docs
```

## Arquitectura

Backend en **arquitectura hexagonal** (ports & adapters). Ver [`docs/`](docs/) para ADRs y diagramas C4, y [`CLAUDE.md`](CLAUDE.md) para convenciones.

## Desarrollo

Consulta [`CONTRIBUTING.md`](CONTRIBUTING.md) y las skills en [`.claude/skills/`](.claude/skills/).

## Licencia

[MIT](LICENSE)
