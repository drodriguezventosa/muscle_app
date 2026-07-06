# Changelog

Todos los cambios notables de este proyecto se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto se adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

### Added
- Scaffolding inicial del monorepo: backend (FastAPI hexagonal), frontend (Vue 3 + Vite),
  Docker Compose, CI/CD, skills de Claude, documentación de arquitectura e higiene de repo.
- Dominio y base de datos: entidades `Muscle`/`Exercise` + value objects, puertos de repositorio,
  modelos SQLAlchemy con columna `pgvector`, sesión async, repositorios, migración Alembic inicial
  (extensión `vector` + tablas) y seed idempotente del catálogo. Tests unit + integración y servicio
  Postgres en CI.

### Fixed
- `.gitignore`: el patrón `models/` ignoraba por error el paquete ORM `persistence/models`; acotado
  a rutas de caché de la raíz.
