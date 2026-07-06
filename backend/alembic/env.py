"""Alembic environment.

Uses the application settings for the database URL and a synchronous psycopg
connection for migrations (async engines are for the app runtime, not Alembic).
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.infrastructure.persistence.models import Base

target_metadata = Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic runs synchronously; swap the async driver for the sync psycopg one.
sync_url = get_settings().database_url.replace("+asyncpg", "+psycopg")
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
