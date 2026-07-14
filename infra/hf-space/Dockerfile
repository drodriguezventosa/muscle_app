# Hugging Face Space (Docker SDK) — MuscleApp backend API.
# Python 3.12 (not 3.14) so the optional `.[ai]` extra — sentence-transformers /
# torch — installs from prebuilt wheels. The CD workflow copies backend/ next to
# this file, so the build context already contains pyproject.toml, app/ and alembic/.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # Writable caches for the sentence-transformers model download.
    HF_HOME=/tmp/hf \
    TRANSFORMERS_CACHE=/tmp/hf \
    SENTENCE_TRANSFORMERS_HOME=/tmp/hf

# Non-root user (HF convention: uid 1000). OWASP A05.
RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --chown=app:app . .

RUN pip install --upgrade pip && pip install ".[ai]"

USER app
EXPOSE 8000
CMD ["sh", "bootstrap.sh"]
