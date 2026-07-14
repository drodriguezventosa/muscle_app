# 8. Exercise media: localized videos with forced subtitles, and how-to steps fallback

- Status: accepted
- Date: 2026-07-14

## Context

Every exercise should show how it is performed. We could not reliably verify an
embeddable YouTube video for all exercises, and some good references exist only in
one language.

## Decision

- Store per-locale demonstration videos (`video_url`/`video_url_en`, YouTube).
- Provide localized how-to `steps`/`steps_en` as a fallback: shown inline when there
  is no video, and inside a collapsible when there is one.
- The player embeds `youtube-nocookie` and forces captions in the UI language
  (`cc_load_policy=1&cc_lang_pref=<locale>`), so a video in the "other" language still
  shows readable subtitles.

## Consequences

- Every exercise always has an example (video or steps); no hard dependency on video
  availability or language.
- Videos are verified via YouTube oEmbed before use; broken/removed ids are caught.
- Steps are authored in-repo (no external asset licensing).
