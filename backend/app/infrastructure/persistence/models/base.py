"""Declarative base for all ORM models."""

from sqlalchemy.orm import DeclarativeBase

# Embedding dimension for the exercise vectors. Must match settings.embedding_dim
# and the migration; changing it requires a new migration.
EMBEDDING_DIM = 384


class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base."""
