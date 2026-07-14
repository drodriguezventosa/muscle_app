# 7. Bilingual content via default + `_en` columns and a `lang` query param

- Status: accepted
- Date: 2026-07-14

## Context

The app is bilingual (Spanish/English). It is not enough to translate UI strings:
catalog content (muscle and exercise names, descriptions, videos, how-to steps)
must also be localized.

## Decision

- UI strings: `vue-i18n`, browser-detected default, with a flag language switcher.
- Content: each translatable column stores Spanish by default plus an optional
  `*_en` override (e.g. `name`/`name_en`, `video_url`/`video_url_en`,
  `steps`/`steps_en`). The repository resolves the right value from the `?lang=`
  query param (default `es`); the frontend appends `lang` to every content request.

## Consequences

- Simple and query-free at the domain level; no join/translation tables for two langs.
- Falls back to Spanish when an English value is missing.
- A third language would mean more columns; acceptable at this scale, revisit if it grows.
