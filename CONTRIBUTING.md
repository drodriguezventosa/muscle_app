# Contribuir a MuscleApp

## Flujo de trabajo

1. Crea una rama desde `main`: `feat/…`, `fix/…`, `docs/…`, `chore/…`.
2. Haz cambios acompañados de **tests**.
3. Asegura que pasa el control de calidad en local (ver más abajo).
4. Abre un PR usando la plantilla. CodeRabbit + SonarCloud + CI lo revisarán.
5. Merge solo con todos los checks en verde y la review aprobada.

## Commits convencionales

`tipo(ámbito): descripción` — tipos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`.
Ejemplo: `feat(chatbot): añade recuperación semántica con pgvector`.

## Control de calidad local

```bash
# Backend
cd backend
ruff check . && ruff format --check . && mypy app && bandit -r app
pytest --cov=app --cov-fail-under=80

# Frontend
cd frontend
npm run lint && npm run test && npm run build
```

Recomendado: instala los hooks de pre-commit → `pre-commit install`.

## Arquitectura

Respeta las capas hexagonales (ver `CLAUDE.md`) y usa la skill del área correspondiente en `.claude/skills/`.

## Seguridad

Aplica el checklist OWASP de la skill `security` en cada cambio. Reporta vulnerabilidades de forma privada, no en issues públicos.
