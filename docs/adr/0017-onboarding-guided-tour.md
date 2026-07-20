# 17. Onboarding guided tour and section-aware assistant

- Status: accepted
- Date: 2026-07-21

## Context

The app grew to five sections (explorer, workouts, nutrition, progress,
trainers) plus a floating AI assistant. A first-time visitor lands with no login
and no explanation of what each area does. For a thesis demo we wanted a short,
non-invasive way to showcase every feature, without adding a heavy dependency or
breaking the €0 / no-login constraint.

## Decision

Add a lightweight, dependency-free **guided tour** (`GuidedTour.vue`) plus small
touches that make the assistant feel part of each page.

- **Hybrid, short walkthrough**: a centered welcome, then one step per section
  and one each for the assistant and the theme/language controls. Each section
  step **navigates to its route** and spotlights the section, so the description
  always matches what is on screen (opening the tour from `/nutrition` still
  starts the explanation on the explorer).
- **First-visit + replayable**: shown once (a flag in `localStorage`), and always
  replayable from a header **"?"** button. A **"Don't show again"** toggle controls
  whether the flag is persisted; clicking outside the modal does **not** dismiss it,
  so an accidental click can't hide it forever. The tour restores the user's
  original route when it finishes.
- **Custom over library**: a small custom component (spotlight via an outer
  `box-shadow`, an anchored tooltip) instead of a tour library, to keep the bundle
  small, own the i18n/a11y/responsive behavior, and match the design system.
- **Section-aware assistant**: the chat is already context-aware (meals on
  Nutrition); the closed bubble icon now also mirrors the current section
  (💪 / 🏋️ / 🍗 / 📈 / 🧑‍🏫), falling back to the robot icon elsewhere.

## Consequences

- New users get a guided overview of the whole product in ~9 short, skippable
  steps, driven entirely client-side (no backend, no extra dependency).
- Because each step owns its route, the tour is resilient to being launched from
  any page and stays correct as sections are added or reordered.
- Accessibility and responsiveness are handled in-house: the tour keeps tooltips
  within the viewport and targets the hamburger path on narrow screens.
- Trade-off: maintaining the spotlight/positioning logic ourselves (measuring
  targets, avoiding scroll feedback loops) instead of delegating to a library.
