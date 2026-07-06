# 3. PostgreSQL + pgvector as the single datastore

- Status: accepted
- Date: 2026-07-06

## Context

We need relational data (muscles, exercises, and later users/subscriptions) and vector
similarity search for the recommendation chatbot (RAG). Cost must stay near zero.

## Decision

Use a single PostgreSQL instance with the `pgvector` extension for both relational data
and embeddings, instead of adding a separate vector database.

## Consequences

- One datastore to run, back up and deploy (Neon/Supabase free tier support pgvector).
- Simpler infra and lower cost; adequate performance for the catalog size.
- If scale demands it later, a dedicated vector store can be introduced behind the
  existing repository port.
