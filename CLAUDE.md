# CLAUDE.md — MuscleApp

Guía para trabajar en este repositorio con Claude Code. Léela antes de hacer cambios.

## Qué es esto

Aplicación web de fitness (Trabajo Fin de Máster) con:

1. **Explorador de músculos interactivo** — cuerpo humano en SVG; al seleccionar un músculo se ven los ejercicios recomendados. **Acceso libre, sin login.**
2. **Chatbot de recomendaciones** — RAG híbrido (filtros SQL + `pgvector`) sobre un catálogo de ejercicios. **Uso libre, sin registro.**
3. **Nutrición** — calculadora de calorías y macros, catálogo de alimentos con menú diario y estimación de un plato por foto. **Uso libre, sin registro.**
4. **Entrenadores (área con login)** — construida y desplegada: un alumno tiene un entrenador y un entrenador muchos alumnos; calendario de entrenamiento en ambos lados y panel de evolución. **Sin registro público**: solo existen las cuentas demo sembradas.
5. **Monetización (pendiente)** — el cobro es una simulación etiquetada en el frontend, nunca pide datos de tarjeta. Una pasarela real entraría como un adaptador más detrás de un puerto nuevo.

Restricciones: coste **0/mínimo** (desplegable en free tiers), **arquitectura hexagonal**, **seguridad OWASP**, **tests + CI/CD**, y **buen rendimiento + diseño minimalista** en el front.

## Stack

| Área | Tecnología |
|------|-----------|
| Backend | FastAPI (Python 3.12+), arquitectura hexagonal |
| Frontend | Vue 3 + Vite + TypeScript (Composition API, Pinia) |
| BD | PostgreSQL + `pgvector` |
| IA (LLM) | `LLMPort` → `stub` (tests) / Ollama (dev) / **Groq** (deploy) / Gemini |
| Embeddings | `EmbeddingPort` → `fake` (tests) / **Jina** (deploy, 384 dims) / `sentence-transformers` o Gemini (dev) |
| Visión | `VisionPort` → `stub` (tests) / **OpenRouter** (deploy) / Gemini (dev) |
| Caché | `CachePort` → memoria (dev) / **Redis · Upstash** (deploy) |
| Auth | Argon2id + JWT; solo cuentas demo sembradas, sin registro público |
| Pagos | Simulación en el frontend, sin datos de tarjeta. **Aún no hay `PaymentPort`** |
| Infra | Docker Compose (dev); **Render + Neon + Vercel** (deploy real). Cloud Run descartado: exige tarjeta |

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

# Revisión de PRs y CI (gh CLI disponible y autenticado)
gh pr view <n>                                 # ver una PR (estado, mergeable, conflictos)
gh pr checks <n>                               # estado de los checks de CI
gh pr diff <n>                                 # diff de la PR
gh run list / gh run view <id> --log-failed    # logs de workflows fallidos
gh secret list                                 # secrets del repo
```

> **`gh` está disponible y autenticado**: úsalo para revisar PRs, checks de CI, diffs,
> logs de workflows fallidos y gestionar secrets. Para credenciales de servicios usa
> `gh secret set` (nunca hardcodear). Recuerda: **no hacer commits ni push** (eso es del usuario).

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
- Commits convencionales (`feat:`, `fix:`, `docs:`...). Ramas protegidas. Checks reales de cada PR: **CI** (backend y frontend), **CodeQL**, **Trivy** y el preview de **Vercel**; la cobertura sube a **Codecov**. CodeRabbit y SonarCloud siguen pendientes (ver `docs/roadmap-calidad-y-despliegue.md`).

## Qué NO hacer

- **No hacer commits ni push por tu cuenta**: la gestión de git (commit, push, PRs) la hace siempre el usuario. Aplica los cambios en el árbol de trabajo, valida, y deja que el usuario los commitee. Si un cambio debe llegar a la CI/PR, indica el comando (p.ej. `! git push ...`) en vez de ejecutarlo.
- No abrir registro público ni cobros reales: las cuentas son las demo sembradas y la pasarela es una simulación que nunca pide datos de tarjeta. El login solo protege el área de entrenadores; explorador, chatbot, entrenamientos y nutrición siguen siendo de acceso libre.
- No introducir dependencias de pago ni servicios que rompan el coste 0.
- No poner lógica de negocio en `api/` ni acceso a BD en `domain/`.
