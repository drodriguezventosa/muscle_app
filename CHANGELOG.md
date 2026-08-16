# Changelog

Todos los cambios notables de este proyecto se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [1.0.0] — 2026-08-16

Versión entregada como Trabajo Fin de Máster, desplegada y en funcionamiento en
[muscle-app-swart.vercel.app](https://muscle-app-swart.vercel.app). El *porqué* de cada
decisión está en los [26 ADR](docs/adr/) y los [diagramas C4](docs/diagrams/).

### Added

**Explorador de músculos** (sin registro)

- Mapa anatómico del cuerpo en SVG, vista frontal y trasera, con selección por grupo
  muscular y popup de desambiguación cuando el grupo tiene varios músculos.
- Filtros de vista, material y nivel que actúan a la vez sobre la lista de ejercicios
  **y sobre la propia figura**: los grupos sin resultados desaparecen del mapa.
- Catálogo de 42 ejercicios sobre 10 grupos musculares, cada uno con vídeo de YouTube
  (subtítulos forzados en el idioma de la interfaz) e instrucciones paso a paso.
- Endpoints públicos `/api/v1/muscles`, `/muscles/{svg_id}`, `/muscles/active`,
  `/muscles/{svg_id}/exercises` y `/exercises/{id}`.

**Asistente con IA (RAG híbrido)**

- Recomendación de ejercicios en lenguaje natural: la consulta se vectoriza, se recuperan
  los vecinos más cercanos con `pgvector` filtrando por material y nivel, y el modelo
  redacta **solo con lo recuperado**. Puertos `EmbeddingPort` y `LLMPort`.
- Guardas anti *prompt-injection* en la capa de aplicación y aviso de salud en cada
  respuesta. Rate limiting en el endpoint.
- Asistente consciente de la sección: en Nutrición recomienda comidas del catálogo.

**Entrenamiento y progreso**

- Generador de rutinas **sin estado** por objetivo (pérdida de grasa, hipertrofia, fuerza)
  a partir de altura, peso y nivel, con cálculo de IMC.
- Registro de peso por ejercicio con sugerencia de sobrecarga progresiva, guardado en
  `localStorage`: sin cuenta, sin servidor y privado.

**Nutrición**

- Calculadora de calorías y macros (Mifflin-St Jeor → TDEE → objetivo) con salvaguardas:
  sin déficit en bajo peso y con mínimo calórico.
- Catálogo de 111 alimentos, constructor de menú con progreso por macro y chat de comidas
  que reutiliza el mismo RAG sobre otro corpus.
- **Estimación de alimentos a partir de una foto** del plato (`VisionPort`), devueltos
  como lista **editable** que la persona confirma antes de añadir.

**Coaching entrenador ↔ alumno**

- Inicio de sesión con cuentas de demostración (JWT propio + **Argon2id**); sin registro público.
- Un alumno tiene **un** entrenador y un entrenador muchos alumnos, con la relación
  persistida en base de datos; contratar desbloquea el plan.
- Calendario semanal prescrito por el entrenador (ejercicio, series, repeticiones y peso
  objetivo) y reporte por el alumno de **lo que realmente levantó**.
- Panel del entrenador con la evolución de cada alumno — fuerza como 1RM estimado por
  Epley, peso corporal y adherencia semanal — calculada en el servidor y pintada con
  gráficas SVG propias, sin librería de *charts*.

**Producto y accesibilidad**

- Bilingüe ES/EN en interfaz **y contenido** (columnas `_en` + parámetro `?lang=`).
- Tema claro/oscuro mediante tokens CSS, diseño responsive con menú hamburguesa,
  navegación por teclado y etiquetas ARIA.
- Tour guiado en la primera visita, saltable y repetible.

**Infraestructura y calidad**

- Backend en arquitectura hexagonal (dominio, aplicación, infraestructura, api) con
  Docker Compose para desarrollo.
- Despliegue continuo en Render + Vercel + Neon (`render.yaml`): cada merge a `main`
  redesplega, con arranque idempotente que reconcilia el esquema y rellena los datos
  que falten.
- Rendimiento en *free tier*: keep-alive contra el arranque en frío, caché de catálogo
  *stale-while-revalidate* en el navegador y `CachePort` (memoria / Redis) para los
  embeddings de consulta.
- CI que bloquea el merge: ruff, mypy, bandit, pip-audit, migraciones arriba y abajo, y
  186 tests de backend con **92,85 %** de cobertura contra un Postgres real con pgvector;
  85 tests de frontend (Vitest), e2e con Playwright, CodeQL, Trivy y Codecov.

### Changed

- **Chat migrado de Gemini a Groq**: la cuota gratuita de chat de Gemini devolvía `429`
  en la primera petición (ADR-0004).
- **Embeddings migrados a Jina AI**: Google retiró `gemini-embedding-001` y su *free tier*
  rechaza las IPs de datacenter desde las que llama Render (ADR-0018, ADR-0019).
- **Visión servida por OpenRouter**, el único proveedor multimodal gratuito alcanzable
  desde el despliegue (ADR-0020).
- El área de entrenadores **dejó de ser una maqueta de frontend** y pasó a datos reales en
  servidor, con cuentas, calendario y evolución (ADR-0021, ADR-0023, ADR-0024, ADR-0026).
- Backend movido de Hugging Face Docker Spaces (pasó a ser de pago) a Render, y de
  `sentence-transformers` local a embeddings por API, que caben en los 512 MB del plan
  gratuito (ADR-0010).

> Las tres migraciones de proveedor de IA costaron **un adaptador y una variable de
> entorno cada una**, sin tocar el dominio ni los casos de uso: es la comprobación práctica
> de la arquitectura hexagonal (ADR-0002).

### Fixed

- El chat **degrada con elegancia**: si el proveedor de IA falla o agota cuota, se devuelven
  igualmente los ejercicios recuperados en lugar de un 500.
- DSN de base de datos construido con `URL.create`, para contraseñas con caracteres
  especiales como las que emite Neon.
- `.gitignore`: el patrón `models/` ignoraba por error el paquete ORM
  `persistence/models`; acotado a rutas de caché de la raíz.
- El mapa muscular dejó de parpadear al (re)seleccionar, y la rutina generada se
  retraduce al cambiar de idioma.

### Security

- Validación con Pydantic y SQL parametrizado en todo el acceso a datos.
- Autorización en coaching (OWASP A01): toda lectura de un alumno pasa por la tabla de la
  relación, y el id del usuario sale **siempre del token**, nunca del cuerpo de la petición.
- Configuración 12-factor sin secretos en el código; en producción la aplicación **se niega
  a arrancar** con el secreto JWT de desarrollo.
- Cabeceras de seguridad, CORS con lista de permitidos, rate limiting y límite de tamaño en
  la subida de imágenes.
- SAST con Bandit y CodeQL, escaneo de imágenes con Trivy y auditoría de dependencias con
  pip-audit en cada PR.

### Known limitations

- **El pago es una simulación**: el checkout no pide datos de tarjeta y no existe todavía
  ningún `PaymentPort` (`infrastructure/payments/` es un paquete reservado).
- **No hay registro público**: solo cuentas de demostración sembradas.
- La estimación por foto tarda ~16 s con el modelo gratuito de OpenRouter, frente a ~2 s de
  una alternativa de pago: es el precio de la restricción de coste cero (ADR-0020).
- SonarCloud, CodeRabbit, Lighthouse CI y las pruebas de carga con k6 siguen en la hoja de
  ruta (`docs/roadmap-calidad-y-despliegue.md`).

[Unreleased]: https://github.com/drodriguezventosa/muscle_app/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/drodriguezventosa/muscle_app/releases/tag/v1.0.0
