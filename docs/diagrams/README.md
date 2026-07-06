# C4 diagrams

Architecture diagrams following the [C4 model](https://c4model.com/). Add the source
(e.g. Mermaid or Structurizr) and exported images here as the system grows.

## Level 1 — System context (draft)

```mermaid
graph LR
    user[Visitor] -->|explores muscles, asks the chatbot| app[MuscleApp SPA]
    app -->|HTTPS /api/v1| api[MuscleApp API]
    api --> db[(PostgreSQL + pgvector)]
    api -->|LLMPort| llm[LLM provider\nOllama dev / Gemini deploy]
```

## Level 2 — Containers (draft)

```mermaid
graph TB
    spa[Frontend SPA\nVue 3 + Vite]
    api[Backend API\nFastAPI hexagonal]
    db[(PostgreSQL + pgvector)]
    llm[LLM provider]
    spa --> api
    api --> db
    api --> llm
```

_TODO: add the component-level (Level 3) diagram for the backend layers._
