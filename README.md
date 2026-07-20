# MuscleApp 💪

Aplicación web para explorar los músculos del cuerpo y descubrir qué ejercicios trabajarlos, con un **chatbot de recomendaciones** basado en IA (RAG). Proyecto de Trabajo Fin de Máster.

> ⚕️ **Aviso**: las recomendaciones de ejercicio son orientativas y **no constituyen consejo médico**. Consulta a un profesional antes de iniciar cualquier programa de entrenamiento.

## Características (MVP)

- 🗺️ **Explorador interactivo** del cuerpo humano (SVG) con figura anatómica, popup por
  grupo muscular y **filtros** (vista frente/espalda, material, nivel) — sin registro.
- 🎬 Cada ejercicio con **vídeo de ejemplo** (subtítulos en tu idioma) o **pasos** paso a paso.
- 🤖 **Asistente con IA** (RAG) que recomienda ejercicios según tu objetivo, músculo y material.
  Es **contextual**: en Nutrición sugiere ideas de comidas del catálogo, y el icono de la
  burbuja refleja la sección en la que estás.
- 🏋️ **Generador de rutinas** por objetivo (pérdida de grasa / hipertrofia / fuerza) a partir
  de tus datos (altura, peso, nivel), con IMC.
- 🍽️ **Nutrición**: calculadora de **calorías y macros** diarios (Mifflin-St Jeor, TDEE, IMC),
  **catálogo de alimentos** con buscador, **constructor de menú** frente a tus objetivos y
  **chat de comidas** (RAG) — con aviso de que no sustituye a un dietista-nutricionista.
- 📈 **Progreso**: registra el peso por ejercicio y sigue tu evolución con sobrecarga
  progresiva (guardado en tu dispositivo).
- 👤 **Entrenadores** (vista previa): contratar un entrenador y panel para gestionar alumnos.
- 🧭 **Tutorial guiado** en la primera visita (saltable y repetible desde el botón «?»): recorre
  y **navega** por cada sección explicándola brevemente.
- 🌗 **Modo claro/oscuro** y 🌍 **bilingüe** (ES/EN).
- 🎨 Interfaz **moderna, minimalista y responsive**.

_Auth, suscripciones y entrenadores personales (reales) están planificados como fase futura._

## Stack

FastAPI · Vue 3 + Vite · PostgreSQL + pgvector · Groq / Gemini (embeddings) / Ollama · Docker

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

Publicado bajo la **[PolyForm Noncommercial License 1.0.0](LICENSE)**: puedes usarlo,
estudiarlo, modificarlo y compartirlo **con fines no comerciales** (uso personal,
educativo, investigación, ONG e instituciones públicas). **El uso comercial no está
permitido** salvo autorización expresa del autor.

Es una licencia _source-available_ (no es «open source» según la OSI, ya que restringe
el uso comercial). © 2026 Daniel Rodríguez Ventosa — para licencias comerciales,
contacta con el autor.
