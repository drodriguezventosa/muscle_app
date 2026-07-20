# 16. Nutrition module (calculator + food catalog + RAG meal chat)

- Status: accepted
- Date: 2026-07-20

## Context

The app covered training (explorer, workouts, progress) but not nutrition, which
is half of any fitness result. We wanted a nutrition section that adds real value
for a thesis demo, stays €0 / no-login, and — importantly — is safe: nutrition
advice is sensitive (eating disorders, minors, medical conditions).

## Decision

Add a **Nutrition** section in three layers, reusing existing infrastructure:

1. **Calculator** — a pure `CalculateNutrition` use case: Mifflin-St Jeor BMR →
   activity-scaled TDEE → goal adjustment → protein/fat/carb split. Deterministic,
   no external calls. **Safeguards**: no calorie deficit when underweight, a hard
   minimum-calorie floor, and a dietitian/medical disclaimer.
2. **Food catalog + menu builder** — a `foods` table (macros per 100 g, bilingual,
   diet tags) with a client-side menu builder that sums macros against the target.
   Seeded **independently and idempotently** so it lands on an already-seeded DB.
3. **RAG meal chatbot** — `RecommendMeals` reuses the *exact* stack from the
   exercise chatbot: `EmbeddingPort` (Gemini) → pgvector `search_similar` over
   foods → `LLMPort` (Groq), grounded only on retrieved foods, with prompt-injection
   and medical guardrails. Query embeddings are cached (`CachePort`).

## Consequences

- The RAG architecture is shown to **generalize to a second domain** with zero new
  infrastructure — a strong point for the thesis (validates ADR-0002/0003/0004).
- Everything stays €0/no-login: targets and menu live client-side (ADR-0011); the
  chat reuses the free Groq/Gemini free tiers.
- Responsible-design story: explicit safeguards and disclaimers for a sensitive
  domain, documented and enforced in the use case.
- Schema grows by one table (`foods`), created via `create_all` at boot like the
  rest; the independent seed guarantees it populates on existing databases.
