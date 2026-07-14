# Roadmap — Fase 6 (calidad/hardening) y despliegue

> Nota de planificación para retomar más adelante. Regla transversal: **todo debe
> ser gratis de verdad** (open-source/self-host, o free tier solo si es gratis por
> repo público o por nuestro volumen mínimo y sin tarjeta/riesgo de cobro). El
> despliegue debe ser lo **más económico posible** (objetivo: 0 €/mes, sin tarjeta).

## Fase 6 — Herramientas de calidad y hardening

| Herramienta | Para qué sirve | Por qué es gratis para nosotros |
|---|---|---|
| **Lighthouse CI** | Audita rendimiento/accesibilidad/buenas prácticas/SEO del frontend en CI, con presupuesto (umbral) que bloquea si baja. | Open-source, corre en GitHub Actions. |
| **k6** | Pruebas de carga de la API (usuarios concurrentes, latencia, errores). Métricas para la memoria. | CLI open-source. Evitar "k6 Cloud" (de pago). |
| **SonarCloud** | Calidad estática: code smells, duplicación, seguridad, cobertura; quality gate en PRs. | Gratis para repos públicos. |
| **CodeRabbit** | Revisión de PRs con IA (comenta el diff, sugiere mejoras). | Plan gratis para repos públicos/open-source. |
| **CodeQL** | SAST de seguridad de GitHub (inyección, etc.). Ya en CI. | Gratis para repos públicos. |
| **Trivy** | Escaneo de imágenes Docker y dependencias (CVEs). Ya en uso. | Open-source. |
| **Codecov** | Reporte/evolución de cobertura en PRs. | Gratis para open-source. |
| **GlitchTip** (en vez de Sentry SaaS) | Captura de errores en producción, compatible con SDK de Sentry, pero self-host/OSS. Alternativa mínima: solo logs estructurados (ya los hay). | Open-source. |

### Documentación (material de TFM, coste 0)
- **ADRs** en `docs/adr/` — decisiones de arquitectura y su porqué.
- **Diagramas C4** en `docs/diagrams/` — contexto / contenedores / componentes (Mermaid).
- **CHANGELOG + SemVer** — historial de versiones legible.

### Estado (a 2026-07-14)
- ✅ Ya hecho en fases previas: security headers, CORS allowlist, rate limiting, validación
  Pydantic, logs estructurados (structlog), CI (lint/tipos/tests/cobertura ≥80% backend),
  CodeQL, Trivy, e2e básico (Playwright, home).
- ⏳ Pendiente: Lighthouse CI, k6, SonarCloud, CodeRabbit, Codecov, error tracking (GlitchTip
  o solo logs), ampliar e2e + cobertura frontend, ADRs nuevos + C4 completo, CHANGELOG/SemVer.

## Fase 7 — Despliegue (objetivo 0 €, sin tarjeta)

> Se descarta **Cloud Run** (exige cuenta de facturación de GCP con tarjeta) y
> **Hugging Face Docker Spaces** (ahora requieren el plan de pago Pro).
> **CD nativo**: tanto Vercel como Render autodesplegan en cada push a `main`
> (sin workflow de GitHub Actions ni tokens). Config en `render.yaml` y `vercel.json`.

| Parte | Opción gratis (elegida) | Notas |
|---|---|---|
| Frontend | **Vercel Hobby** | Hosting del SPA. Sin tarjeta, no factura. Autodespliega en cada push. |
| Base de datos | **Neon** (free) | Postgres + **pgvector**. Sin tarjeta; pausa si no se usa (no cobra). |
| Backend (API) | **Render free** | Sin tarjeta, CD nativo desde GitHub. "Duerme" tras inactividad (arranque frío ~1 min). |
| LLM del chatbot | **Groq API free** (Llama 3.3 70B) o *stub* | Free tier generoso sin tarjeta. Se eligió sobre Gemini porque su cuota de *chat* gratis es demasiado baja (429). |
| Embeddings | **Gemini embeddings** (API free) | Vectores reales sin `torch` (no cabría en los 512 MB de Render). Cuota aparte del chat. |

**Contrapartidas asumidas:** arranque en frío de Render tras inactividad y límites de
ritmo del LLM/embeddings gratis — irrelevantes para una demo de TFM.

## Ideas de producto

- ✅ **Progreso de entrenamiento** (hecho, localStorage — ADR-0011): registro de peso por
  sesión, récord/gráfica día a día y semana a semana, y sugerencia de peso por sobrecarga
  progresiva.
- ✅ **Entrenadores/coaching** (hecho como maqueta demo — ADR-0012): contratar entrenador
  (precios €) y panel del entrenador (alumnos, progreso, asignar ejercicios). Frontend, sin
  pagos/cuentas reales.
- ✅ **Modo claro/oscuro** (hecho — ADR-0013).
- ⏳ **Auth + monetización** (fase diferida): convertir la maqueta de entrenadores en real
  (cuentas, `PaymentPort`, asignaciones persistidas) y sincronizar el progreso al backend.

## Orden sugerido
1. Documentación (ADRs + C4) — *en curso*.
2. Despliegue gratuito (demo pública).
3. Métricas: Lighthouse + k6.
4. Integraciones de PR: SonarCloud + CodeRabbit + Codecov.
5. Observabilidad (GlitchTip o logs) + CHANGELOG/SemVer.
