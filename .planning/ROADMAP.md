# Roadmap: Mosaic Data Dashboard

**Milestone:** v1.0 Inspector
**Created:** 2026-05-13
**Granularity:** coarse
**Phases:** 7
**Coverage:** 29/29 v1 requirements mapped

## Core Value

A MOSAIC modeler can pick a country and, in one screen, eyeball whether drivers like ENSO, WASH, or mobility track with cholera cases — fast enough that exploration replaces (rather than supplements) ad-hoc notebook work.

## Phases

- [ ] **Phase 1: Foundation & Data Layer** — Project scaffolding with uv + a configurable, offline, fresh-read data access layer over `MOSAIC-data/processed/`.
- [ ] **Phase 2: Country Navigation & SSA Map** — Country picker + SSA shapefile map that together drive every panel and stay in sync.
- [ ] **Phase 3: Cholera & Driver Layers** — Per-country views for WHO cholera and the four driver subdirs (ENSO, WASH, OAG, demographics).
- [ ] **Phase 4: Driver↔Outcome Overlays** — Shared-x-axis cholera vs. driver overlays with toggling and cadence handling.
- [ ] **Phase 5: Static & Geometry Layers** — Remaining `processed/` subdir views: shapefiles, immunity, vaccine_effectiveness, symptomatic, similarity_matrix.
- [ ] **Phase 6: Subnational Drilldown & Performance** — ADM1/ADM2 drilldown where supported + sub-second country-switch and map interaction.
- [ ] **Phase 7: Usability Polish** — Per-layer captions and a no-walkthrough usability pass against the v1 done bar.

## Phase Details

### Phase 1: Foundation & Data Layer
**Goal**: Stand up a runnable Streamlit app and a configurable, offline-safe, fresh-read data access layer over `MOSAIC-data/processed/`.
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, ENV-01, ENV-02
**Success Criteria** (what must be TRUE):
  1. A teammate can clone the repo, run `uv sync && uv run streamlit run <entry>`, and see the dashboard load with no manual data-fetch step.
  2. The dashboard reads from a `MOSAIC-data/processed/` path the user can configure (env var, config, or settings UI) and reflects edits to those files on the next page load without a refresh button.
  3. With the network disconnected, the dashboard still loads and renders any layer whose files exist locally.
  4. If a `processed/` subdir is missing, renamed, or empty, the affected view shows an empty-state message instead of crashing the app.
**Plans**: TBD

### Phase 2: Country Navigation & SSA Map
**Goal**: A modeler can pick a Sub-Saharan African country from either a dropdown or the map, and that selection drives every view in the app for the rest of the session.
**Depends on**: Phase 1
**Requirements**: NAV-01, NAV-02, MAP-01, MAP-02
**Success Criteria** (what must be TRUE):
  1. The user sees a single country picker that, when changed, updates every panel in the app to that country.
  2. The user sees an SSA map rendered from `processed/shapefiles/AFRICA_ADM0` and can click a country to select it as an alternative to the dropdown.
  3. The map visibly highlights the currently selected country, and dropdown and map selections stay in sync in both directions.
  4. After picking a country, the user can switch between views without having to re-select that country.
**Plans**: TBD
**UI hint**: yes

### Phase 3: Cholera & Driver Layers
**Goal**: For the selected country, the modeler can open a dedicated view for cholera cases and for each driver subdir (ENSO, WASH, OAG, demographics).
**Depends on**: Phase 2
**Requirements**: LAYER-01, LAYER-02, LAYER-03, LAYER-04, LAYER-05
**Success Criteria** (what must be TRUE):
  1. The WHO view shows annual (1949–2024) and weekly (2023–2024) cholera cases for the selected country.
  2. The WASH view shows WASH indicators (from `WASH_data_Sikder_2023.csv`) for the selected country.
  3. The OAG view shows flight-mobility series (daily/weekly/monthly 2017 means) involving the selected country.
  4. The demographics view shows UN WPP (1967–2100) and Africa 2000–2023 series for the selected country.
  5. The ENSO view shows daily/weekly/monthly ENSO indices (1970–2025) on the dashboard's shared time axis.
**Plans**: TBD
**UI hint**: yes

### Phase 4: Driver↔Outcome Overlays
**Goal**: The modeler can place cholera cases on a shared time axis against one or more drivers and toggle drivers in/out without leaving the view.
**Depends on**: Phase 3
**Requirements**: OVERLAY-01, OVERLAY-02, OVERLAY-03
**Success Criteria** (what must be TRUE):
  1. The user can open an overlay view that shows cholera cases (from WHO) plotted against one or more of ENSO, WASH, demographics, and OAG on a shared x-axis, scoped to the selected country.
  2. The user can add or remove individual drivers from the overlay in place, without changing country or leaving the view.
  3. Layers with different cadences (daily / weekly / monthly / annual) appear correctly aligned on the time axis — no visible misalignment when mixing, say, weekly cholera with monthly ENSO.
**Plans**: TBD
**UI hint**: yes

### Phase 5: Static & Geometry Layers
**Goal**: Every remaining subdir under `processed/` has at least one inspectable view for the selected country, completing per-subdir coverage.
**Depends on**: Phase 2
**Requirements**: LAYER-06, LAYER-07, LAYER-08, LAYER-09, LAYER-10
**Success Criteria** (what must be TRUE):
  1. The shapefiles view shows the selected country's ADM0 geometry standalone (from its per-country shapefile).
  2. The immunity view shows immunity values for the selected country (table or single figure is acceptable if the data has no time axis).
  3. The vaccine_effectiveness and symptomatic views each show their respective values for the selected country as a best-effort visualization.
  4. The similarity_matrix view shows the matrix with the selected country highlighted or filtered to its row/column.
**Plans**: TBD
**UI hint**: yes

### Phase 6: Subnational Drilldown & Performance
**Goal**: Where the data supports it, the modeler can drill from country into ADM1/ADM2; everywhere else falls back cleanly; and country-switch + map interaction feel snappy across the full SSA extent.
**Depends on**: Phase 3, Phase 5
**Requirements**: DRILL-01, DRILL-02, PERF-01, PERF-02
**Success Criteria** (what must be TRUE):
  1. On layers backed by ADM1/ADM2 data and matching shapefiles, the user can drill from the country view into a subnational unit and see that unit's data.
  2. On layers without subnational support for the selected country, the user sees a clear "country-level only" indicator and the view still renders normally — no crashes, no empty plots.
  3. Switching country renders the new country's primary views in under 1 second on a typical MOSAIC-team laptop with all SSA loaded, with no user-visible "loading data" spinner during steady-state use.
  4. Pan and zoom on the SSA map feels sub-second across the full SSA extent.
**Plans**: TBD
**UI hint**: yes

### Phase 7: Usability Polish
**Goal**: A MOSAIC teammate who has never seen the dashboard can sit down, pick a country, and compare cholera to at least one driver without anyone explaining the app.
**Depends on**: Phase 4, Phase 6
**Requirements**: UX-01, UX-02
**Success Criteria** (what must be TRUE):
  1. A first-time MOSAIC teammate can, unaided, pick a country and produce a cholera-vs-driver overlay within their first session.
  2. Every layer view displays a one-line caption stating what the user is looking at, including data source, units, and time range.
**Plans**: TBD
**UI hint**: yes

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Data Layer | 0/0 | Not started | — |
| 2. Country Navigation & SSA Map | 0/0 | Not started | — |
| 3. Cholera & Driver Layers | 0/0 | Not started | — |
| 4. Driver↔Outcome Overlays | 0/0 | Not started | — |
| 5. Static & Geometry Layers | 0/0 | Not started | — |
| 6. Subnational Drilldown & Performance | 0/0 | Not started | — |
| 7. Usability Polish | 0/0 | Not started | — |

## Coverage Map

| Requirement | Phase |
|-------------|-------|
| DATA-01 | Phase 1 |
| DATA-02 | Phase 1 |
| DATA-03 | Phase 1 |
| DATA-04 | Phase 1 |
| ENV-01 | Phase 1 |
| ENV-02 | Phase 1 |
| NAV-01 | Phase 2 |
| NAV-02 | Phase 2 |
| MAP-01 | Phase 2 |
| MAP-02 | Phase 2 |
| LAYER-01 | Phase 3 |
| LAYER-02 | Phase 3 |
| LAYER-03 | Phase 3 |
| LAYER-04 | Phase 3 |
| LAYER-05 | Phase 3 |
| OVERLAY-01 | Phase 4 |
| OVERLAY-02 | Phase 4 |
| OVERLAY-03 | Phase 4 |
| LAYER-06 | Phase 5 |
| LAYER-07 | Phase 5 |
| LAYER-08 | Phase 5 |
| LAYER-09 | Phase 5 |
| LAYER-10 | Phase 5 |
| DRILL-01 | Phase 6 |
| DRILL-02 | Phase 6 |
| PERF-01 | Phase 6 |
| PERF-02 | Phase 6 |
| UX-01 | Phase 7 |
| UX-02 | Phase 7 |

**Total v1 requirements:** 29
**Mapped:** 29
**Unmapped:** 0

---
*Roadmap created: 2026-05-13*
