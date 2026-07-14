# 13. Light/dark theme via CSS custom-property tokens

- Status: accepted
- Date: 2026-07-14

## Context

The app was dark-only. Users want a light mode and a way to switch. The design
already uses CSS custom properties (design tokens) for all colors.

## Decision

Define a light theme as token overrides under `:root[data-theme='light']` in
`styles.css` (plus a softer body aurora and theme-aware `--color-header`,
`--color-elevated` for opaque popovers, and `--color-input`). A small store toggles
`data-theme` on `<html>` and persists the choice in localStorage. An inline script
in `index.html` applies the saved (or `prefers-color-scheme`) theme before paint to
avoid a flash.

## Consequences

- Components stay theme-agnostic by using tokens; avoid hard-coded colors
  (dropdowns/popovers must use `--color-elevated`, inputs `--color-input`).
- No flash of the wrong theme on load; the choice survives reloads, per device.
- Modal scrims stay dark in both themes by design.
