# CLAUDE.md — MuscleApp

Guía para trabajar en este repositorio con Claude Code. Léela antes de hacer cambios.

## Qué es esto

Aplicación web de fitness (Trabajo Fin de Máster) con:

1. **Explorador de músculos interactivo** — cuerpo humano en SVG; al seleccionar un músculo se ven los ejercicios recomendados. **Acceso libre, sin login.**
2. **Chatbot de recomendaciones** — RAG híbrido (filtros SQL + `pgvector`) sobre un catálogo de ejercicios. **Uso libre, sin registro.**
3. **Auth + monetización (diferido)** — registro, suscripción y entrenadores personales; se añadirá más adelante y **no debe bloquear** el MVP.

Restricciones: coste **0/mínimo** (desplegable en free tiers), **arquitectura hexagonal**, **seguridad OWASP**, **tests + CI/CD**, y **buen rendimiento + diseño minimalista** en el front.

## Stack

| Área | Tecnología |
|------|-----------|
| Backend | FastAPI (Python 3.12+), arquitectura hexagonal |
| Frontend | Vue 3 + Vite + TypeScript (Composition API, Pinia) |
| BD | PostgreSQL + `pgvector` |
| IA (LLM) | `LLMPort` → Ollama (dev) / Gemini free tier (deploy) |
| Embeddings | `sentence-transformers` local (`all-MiniLM-L6-v2`, 384 dims) |
| Pagos | `PaymentPort` → adapter mock (Stripe en el futuro) |
| Infra | Docker Compose (dev); Cloud Run + Neon + Vercel (deploy, preparado) |

## Comandos habituales

```bash
# Levantar todo el entorno de desarrollo
docker compose up --build

# Backend (dentro de backend/)
pytest --cov=app --cov-report=term-missing   # tests + cobertura
ruff check . && ruff format --check .          # lint + formato
mypy app                                       # tipos
bandit -r app                                  # SAST
alembic revision --autogenerate -m "msg"       # nueva migración
alembic upgrade head                           # aplicar migraciones

# Frontend (dentro de frontend/)
npm run dev        # servidor Vite
npm run test       # Vitest
npm run lint       # ESLint + prettier
npm run test:e2e   # Playwright
```

## Arquitectura (backend hexagonal / ports & adapters)

```
app/domain/          # entidades y puertos (interfaces). SIN dependencias de framework/BD.
app/application/     # casos de uso; orquestan dominio + puertos.
app/infrastructure/  # adapters concretos: repos SQLAlchemy, LLM, embeddings, pagos.
app/api/             # routers FastAPI finos + schemas Pydantic + inyección de deps.
```

Reglas de dependencia (importante): `domain` no importa nada de `application`/`infrastructure`/`api`.
`application` solo depende de `domain` (puertos). `infrastructure`/`api` implementan/consumen puertos.
Para cambiar de LLM, pagos o BD **no se toca el dominio**: se crea/ajusta un adapter.

## Skills del proyecto (`.claude/skills/`)

**Usa la skill correspondiente antes de trabajar en cada área** — contienen las convenciones y el paso a paso concretos:

- **`backend-dev`** — cómo añadir una entidad, puerto, caso de uso, adapter o router respetando las capas hexagonales.
- **`frontend-dev`** — convenciones Vue 3 (Composition API), Pinia, cliente API tipado, componentes, diseño minimalista y accesible.
- **`db-migrations`** — flujo de Alembic (autogenerar, revisar, aplicar) y seeds.
- **`testing`** — cómo escribir y ejecutar tests (unit/integration/e2e), fixtures de BD y umbral de cobertura.
- **`security`** — checklist OWASP a aplicar en cada cambio y cómo correr Bandit / pip-audit / Trivy.
- **`docker-infra`** — uso de Docker Compose, añadir servicios y perfiles dev/prod.

## Convenciones y calidad

- **API versionada** bajo `/api/v1`; documentación OpenAPI automática.
- **Config 12-factor**: todo por variables de entorno vía `pydantic-settings` (`app/core/config.py`). Nunca secretos en el código.
- **Seguridad OWASP** siempre presente: validación con Pydantic, SQL parametrizado, security headers, CORS allowlist, rate limiting, sin PII/secretos en logs. Revisa la skill `security`.
- **Disclaimer de salud**: las recomendaciones no son consejo médico; debe mostrarse en explorador y chatbot.
- **Tests obligatorios** para todo cambio; cobertura mínima 80%. La CI bloquea el merge si fallan lint/tipos/tests/cobertura/SAST.
- Commits convencionales (`feat:`, `fix:`, `docs:`...). Ramas protegidas; PR revisado por CodeRabbit + SonarCloud.

## Qué NO hacer

- No implementar auth/monetización en el MVP (está diferido); pero mantener el modelo preparado para ello.
- No introducir dependencias de pago ni servicios que rompan el coste 0.
- No poner lógica de negocio en `api/` ni acceso a BD en `domain/`.
