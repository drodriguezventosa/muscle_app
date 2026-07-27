# 20. Meal-photo estimation (vision port, editable results)

- Status: accepted
- Date: 2026-07-27

## Context

Logging a meal one food at a time is the slowest part of the nutrition section.
A photo carries the whole plate, and multimodal models can name its foods and
estimate portions — but the estimate is inherently approximate (a 2D image hides
depth, oils and hidden ingredients), so it must be a starting point the user
corrects, never a figure presented as fact.

A spike against the real API confirmed the idea is viable: a full English
breakfast yielded all seven visible foods (including bacon half-hidden under the
sausage) in ~2 s and ~1.5k tokens, a photo without food returned nothing.

## Decision

Add a **`VisionPort`** (separate from `LLMPort`: different provider, model and
failure modes) returning `EstimatedFood` entities, whose macros are **totals for
the estimated portion** rather than the per-100 g convention of catalog foods.

- **Adapters**: `GeminiVision` posts the image inline (base64) to
  `generateContent` with a forced `responseSchema`, so the reply is always valid
  JSON; `StubVision` keeps dev/CI free of external calls. Parsing is defensive —
  unusable replies mean "no foods", and malformed or absurd items (empty name,
  >2 kg, negative macros) are dropped rather than shown.
- **Failure is never a 500**: HTTP errors are logged with the upstream status and
  raised as `VisionUnavailableError`; the use case turns that into an empty,
  `available: false` result, so the UI can say "try again" instead of breaking
  (the contract established in ADR-0018).
- **The image is never stored.** It is validated (mime allow-list, 5 MB cap),
  sent to the provider and dropped. The prompt states the image is data, never
  instructions, since it is untrusted input.
- **Results are ordinary menu items.** The frontend converts the AI totals into
  per-100 g values and pushes them into the menu with the estimated grams, so
  editing the grams rescales the macros exactly like a catalog food and the
  existing per-macro progress keeps working. Estimated foods get negative ids to
  stay distinguishable from catalog rows.
- **Capture**: `getUserMedia` opens the real camera (desktop webcam and mobile
  rear camera), with a file-picker fallback when it is unavailable or denied.
  Frames are downscaled to 1280 px JPEG before upload, which keeps requests far
  below the size cap and cuts token cost.

**Not persisted to the catalog.** Writing AI-detected foods into `foods` was
considered and rejected: the API is public and unauthenticated (ADR-0006), so any
caller could pollute the shared catalog with arbitrary, unreviewed entries
(OWASP A01/A04). Missing foods are instead added to the curated seed — which this
change also makes **incremental**, because the previous "seed only if the table
is empty" logic meant newly curated foods never reached an already-populated
database. The catalog grew from 76 to 111 foods.

## Consequences

- Logging a plate is one photo instead of a dozen taps, while the numbers stay
  explicitly editable and carry the nutrition disclaimer.
- **Two providers, picked per environment.** Gemini's free tier rejects
  datacenter IPs (ADR-0019) and Groq no longer lists any vision model, so the
  deploy uses **OpenRouter** with a free multimodal model. Measured on
  2026-07-27 with the same test photos:

  | Provider / model | Latency | English breakfast |
  |---|---|---|
  | Gemini `3.1-flash-lite` (local only) | ~2 s | 7/7 foods, exact names |
  | OpenRouter `google/gemma-4-26b-a4b-it:free` | 16–29 s | 6–7/7, plausible portions, minor naming drift |
  | OpenRouter `nvidia/nemotron-nano-12b-v2-vl:free` | ~7 s | inflated portions, broken Spanish |
  | OpenRouter `google/gemma-4-31b-it:free` | — | consistently 429 upstream |

  The trade-off is deliberate: correctness of the *foods* matters more than
  latency here (the user edits the grams anyway), and the spinner covers the
  wait. Both adapters stay available and are switched with `VISION_PROVIDER`, so
  moving to a paid Gemini key later is one environment variable.
- The free tier is roughly 50 requests/day and can 429 upstream; that path is
  already covered by the graceful degradation above.
- New dependency `python-multipart` (required by FastAPI for uploads) and a new
  upload surface, mitigated by the mime/size validation and the existing rate
  limit.
- Also refreshed the Gemini chat model default: `gemini-2.0-flash` now answers 429
  and `gemini-2.5-flash` is retired, so it points at the live flash-lite line.
