# C4 diagrams

Architecture diagrams following the [C4 model](https://c4model.com/), written in
Mermaid so they render directly on GitHub. Three levels of zoom: system **context**,
**containers**, and backend **components**.

## Level 1 — System context

Who uses the system and what it depends on.

```mermaid
graph LR
    user["Visitor<br/>(no login)"]
    app["MuscleApp<br/>Explorer · Chatbot · Workout generator"]
    yt["YouTube<br/>(embedded demo videos)"]
    llm["LLM provider<br/>Ollama (dev) / Gemini free (deploy) / stub"]

    user -->|"explores muscles, asks for recommendations,<br/>generates a routine"| app
    app -->|"embeds exercise videos"| yt
    app -->|"grounded recommendations (RAG)"| llm
```

## Level 2 — Containers

The runtime pieces and how they talk.

```mermaid
graph TB
    user["Visitor"]
    spa["Frontend SPA<br/>Vue 3 + Vite + Pinia"]
    ls[("Browser localStorage<br/>progress, theme, demo assignments")]
    api["Backend API<br/>FastAPI · hexagonal · /api/v1"]
    db[("PostgreSQL + pgvector<br/>muscles, exercises, embeddings")]
    emb["Embeddings<br/>sentence-transformers (local) / fake"]
    llm["LLM provider<br/>Ollama / Gemini / stub"]
    yt["YouTube<br/>(nocookie embed)"]

    user --> spa
    spa -->|"HTTPS JSON, ?lang="| api
    spa -->|"iframe embed"| yt
    spa -->|"client-only, no login"| ls
    api -->|"SQL + vector search"| db
    api -->|"EmbeddingPort"| emb
    api -->|"LLMPort"| llm
```

## Level 3 — Components (backend, hexagonal)

Dependencies point **inwards**: `api` and `infrastructure` depend on `application`
and `domain`; the `domain` depends on nothing external. Adapters (DB, LLM,
embeddings) implement the ports the use cases need, so infrastructure can be swapped
without touching business logic.

```mermaid
graph TB
    subgraph api["api (FastAPI)"]
        routers["routers<br/>muscles · exercises · chat · workouts · health"]
        schemas["Pydantic schemas"]
        deps["dependency injection"]
    end
    subgraph application["application"]
        usecases["use cases<br/>ListMuscleExercises · ListActiveMuscles<br/>RecommendExercises · GenerateWorkout"]
    end
    subgraph domain["domain (pure)"]
        entities["entities<br/>Muscle · Exercise · WorkoutTemplate"]
        ports["ports (interfaces)<br/>MuscleRepository · ExerciseRepository<br/>EmbeddingPort · LLMPort"]
    end
    subgraph infrastructure["infrastructure (adapters)"]
        repos["SQLAlchemy repositories"]
        ai["embeddings + LLM adapters<br/>(sentence-transformers, Ollama/Gemini/stub)"]
    end

    routers --> deps
    deps --> usecases
    usecases --> ports
    usecases --> entities
    repos -. implements .-> ports
    ai -. implements .-> ports
    deps -. wires .-> repos
    deps -. wires .-> ai
```

> To export images (optional), paste a block into the [Mermaid Live Editor](https://mermaid.live)
> or use the Mermaid CLI. GitHub renders the blocks above without any tooling.
