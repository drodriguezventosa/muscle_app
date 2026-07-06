---
name: db-migrations
description: Alembic migration workflow and database seeding for the Postgres + pgvector schema. Use when changing SQLAlchemy models or the database schema.
---

# Database migrations (Alembic + Postgres/pgvector)

## Workflow

1. Edit or add SQLAlchemy models under `app/infrastructure/persistence/models/`.
2. Autogenerate a migration:
   ```bash
   alembic revision --autogenerate -m "short description"
   ```
3. **Review the generated file** in `alembic/versions/` — autogen misses some changes (indexes, pgvector columns, enum changes). Fix by hand.
4. Apply it:
   ```bash
   alembic upgrade head
   ```
5. Downgrade path must work: verify `alembic downgrade -1`.

## pgvector

- The `vector` column type comes from the `pgvector` package. Ensure the extension exists:
  `CREATE EXTENSION IF NOT EXISTS vector;` (add it in the first migration).
- Match the embedding dimension to `settings.embedding_dim` (default 384).

## Seeds

- Seed data (muscles, exercise catalog) lives in a dedicated script/module and is idempotent.
- Precompute exercise embeddings with the local `sentence-transformers` model at seed time.

## Rules

- One logical change per migration; never edit an already-applied migration.
- All messages and comments in English.
