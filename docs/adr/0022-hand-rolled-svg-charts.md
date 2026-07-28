# 22. Hand-rolled SVG charts with a validated palette

- Status: accepted
- Date: 2026-07-28

## Context

The trainer dashboard needs three charts per student (strength progression, body
weight, weekly adherence) plus one across the roster (age against BMI). Three
options were on the table: a charting library, an image service, or drawing the
SVG ourselves.

A library (Chart.js ≈ 70 kB gzipped, ECharts far more) would double the app's
JavaScript for four small charts, ship a canvas renderer that does not inherit
the app's theme tokens, and bring its own accessibility story — while the app
already draws its most complex graphic, the interactive body map, by hand.

The other risk is colour. Palettes picked by eye routinely fail for colourblind
readers, and "these look different enough" is not a check.

## Decision

**Draw the charts as plain SVG components** (`LineChart`, `BarChart`,
`ScatterChart`), themed with the same CSS custom properties as the rest of the
app, sized in real pixels from a `ResizeObserver` so labels never shrink with
the container.

**Colour is computed, not chosen.** Four categorical slots in a fixed order,
with a separate set of steps for each surface, validated with the data-viz
skill's checker against the app's actual chart surfaces (dark `#121620`, light
`#fbfcfe`): lightness band, chroma floor, colourblind separation (worst adjacent
pair ΔE 9.1 light / 8.4 dark, target ≥ 8) and contrast. Slots are assigned **by
entity** — a goal always keeps its hue — never by rank, so nothing repaints when
the data changes. The roster scatter caps at three hues, the all-pairs limit.

Two of the light-mode hues sit below 3:1 contrast on the light surface. The
palette's own relief rule applies and is shipped in full: **direct labels on the
lines, a legend on every multi-series chart, and a table view** (`Ver los datos`)
under each chart with every plotted value. Identity is therefore never carried by
colour alone, which also covers print and forced-colors.

**Interaction ships with the chart, not after it**: a snapping crosshair with one
tooltip listing every series on the line charts, a per-bar and per-dot tooltip
elsewhere, keyboard equivalents (arrow keys move the crosshair; every bar and dot
is focusable), and hit areas larger than the marks.

Marks follow the same spec everywhere: 2px lines, ≥8px end markers with a 2px
surface ring, bars capped at 24px with a rounded data end and a squared foot,
hairline grid, and no value printed on every point.

## Consequences

- The charts weigh a few kB, inherit light/dark automatically and match the
  hand-drawn body map in style.
- Every chart is usable without colour, without a mouse, and without hovering.
- No dependency to update, but also no free chart types: a new form (heatmap,
  stacked bar) is code we write. Acceptable — the dashboard's forms are settled.
- Long series names are shortened with an ellipsis when the gutter cannot fit
  them, and dropped below 420px wide, where the legend carries identity instead.
  The full name is always in the legend and the table.
