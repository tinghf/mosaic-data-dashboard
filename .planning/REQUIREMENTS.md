# Requirements: Mosaic Data Dashboard

**Defined:** 2026-05-13
**Milestone:** v1.0 Inspector
**Core Value:** A MOSAIC modeler can pick a country and, in one screen, eyeball whether drivers like ENSO, WASH, or mobility track with cholera cases — fast enough that exploration replaces (rather than supplements) ad-hoc notebook work.

## v1 Requirements

Requirements for v1.0 Inspector. Each maps to exactly one roadmap phase.

### DATA — Local data layer

- [ ] **DATA-01**: Dashboard reads directly from a local checkout of `MOSAIC-data/processed/`; the root path is configurable (env var, config file, or settings UI — implementer's choice).
- [ ] **DATA-02**: Dashboard re-reads data on every load (no manual refresh button); internal caching is allowed as long as it is invisible to the user and respects file mtime.
- [ ] **DATA-03**: Dashboard makes zero external network calls in the hot path; works fully offline once data is local.
- [ ] **DATA-04**: Dashboard tolerates upstream `processed/` additions, renames, and missing subdirs without code changes where reasonable (e.g., a layer with no data shows an empty-state, not a crash).

### NAV — Country-first navigation

- [ ] **NAV-01**: User can select an ADM0 country from a single picker that drives every panel/view in the app.
- [ ] **NAV-02**: The selected country persists across view switches within a session (no re-picking when navigating between layers).

### MAP — Sub-Saharan Africa map view

- [ ] **MAP-01**: User sees a map of Sub-Saharan Africa rendered from `processed/shapefiles/AFRICA_ADM0`, with countries clickable as an alternate country picker.
- [ ] **MAP-02**: The map highlights the currently selected country and stays in sync with the dropdown picker.

### LAYER — Per-subdir data views

- [ ] **LAYER-01**: View for `WHO/` cholera data showing annual (1949–2024) and weekly (2023–2024) cases for the selected country.
- [ ] **LAYER-02**: View for `WASH/` (`WASH_data_Sikder_2023.csv`) showing WASH indicators for the selected country.
- [ ] **LAYER-03**: View for `OAG/` flight mobility (daily/weekly/monthly 2017 means) showing mobility involving the selected country.
- [ ] **LAYER-04**: View for `demographics/` showing UN WPP (1967–2100) and Africa 2000–2023 series for the selected country.
- [ ] **LAYER-05**: View for `ENSO/` showing daily/weekly/monthly indices (1970–2025) on the dashboard's shared time axis.
- [ ] **LAYER-06**: View for `shapefiles/` (per-country ADM0) showing the selected country's geometry standalone.
- [ ] **LAYER-07**: View for `immunity/` showing immunity values for the selected country (table or single-figure is fine if the data has no time axis).
- [ ] **LAYER-08**: View for `vaccine_effectiveness/` showing vaccine effectiveness values for the selected country (best-effort visualization).
- [ ] **LAYER-09**: View for `symptomatic/` showing symptomatic-fraction values for the selected country (best-effort visualization).
- [ ] **LAYER-10**: View for `similarity_matrix/` showing the similarity matrix with the selected country highlighted or filtered to its row/column.

### OVERLAY — Driver↔outcome time-series overlays

- [ ] **OVERLAY-01**: User can view cholera cases (from `WHO/`) overlaid against one or more driver layers (`ENSO`, `WASH`, `demographics`, `OAG`) on a shared x-axis time-series chart, scoped to the selected country.
- [ ] **OVERLAY-02**: Overlay chart lets the user toggle which drivers are shown without leaving the view.
- [ ] **OVERLAY-03**: Overlay chart handles layers with mismatched cadence (daily / weekly / monthly / annual) without misaligning their time axes.

### DRILL — Subnational drilldown

- [ ] **DRILL-01**: For any layer whose underlying data and shapefiles support ADM1/ADM2, the user can drill from the country view down to a subnational unit.
- [ ] **DRILL-02**: When subnational data or shapefiles are unavailable for a layer, the view falls back gracefully to country level with a clear "country-level only" indicator (no crashes, no empty plots).

### PERF — Performance

- [ ] **PERF-01**: Country switching renders the new country's primary views in under 1 second on a typical MOSAIC-team laptop with all SSA loaded (caching allowed; user never sees a "loading data" spinner during steady-state use).
- [ ] **PERF-02**: Map pan and zoom feels sub-second across the full SSA extent.

### ENV — Reproducible environment

- [ ] **ENV-01**: Project uses `uv` with pinned dependencies and a committed lockfile (`uv.lock`) so any team member can clone, run `uv sync`, and get an identical environment.
- [ ] **ENV-02**: A documented one-liner — `uv sync && uv run streamlit run <entry>` (or equivalent) — launches the dashboard locally.

### UX — Usability bar

- [ ] **UX-01**: A MOSAIC teammate who has not used the dashboard before can open it and figure out how to (a) pick a country and (b) compare cholera vs. at least one driver, without a walkthrough.
- [ ] **UX-02**: Every layer view has a one-line caption describing what the user is looking at (data source, units, time range) so the dashboard is self-explanatory.

## v2 Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### STATS — Driver↔outcome statistical modeling

- **STATS-01**: Cross-correlation or lag analysis between driver layers and cholera cases.
- **STATS-02**: Regression dashboards summarizing driver explanatory power.

### EXPORT — Snapshot export

- **EXPORT-01**: Export current view (country × layers) as a PNG/PDF.
- **EXPORT-02**: Export underlying data slice as CSV.

### COMPARE — Multi-country comparison

- **COMPARE-01**: Compare two or more countries side-by-side on the same driver overlay.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Hosted / public deployment | Local-laptop only; team usability does not require a URL. |
| Auto-fetching from GitHub or DB ingest | Local checkout is the only data source for v1. |
| Write-back / annotation features | Dashboard is a read-only inspector; never modify `MOSAIC-data/`. |
| MOSAIC simulation outputs | Dashboard is about *input* data under `processed/`, not model results. |
| Authentication / multi-user state | Single-user local tool. |
| Formal driver↔outcome statistics in v1 | v1 surfaces relationships visually; formal stats stay in notebooks for now (see v2 STATS). |
| Coverage for `climate/` or `elevation/` subdirs | Not present in current `processed/`; cover only what's actually there. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| DATA-03 | Phase 1 | Pending |
| DATA-04 | Phase 1 | Pending |
| NAV-01 | Phase 2 | Pending |
| NAV-02 | Phase 2 | Pending |
| MAP-01 | Phase 2 | Pending |
| MAP-02 | Phase 2 | Pending |
| LAYER-01 | Phase 3 | Pending |
| LAYER-02 | Phase 3 | Pending |
| LAYER-03 | Phase 3 | Pending |
| LAYER-04 | Phase 3 | Pending |
| LAYER-05 | Phase 3 | Pending |
| LAYER-06 | Phase 5 | Pending |
| LAYER-07 | Phase 5 | Pending |
| LAYER-08 | Phase 5 | Pending |
| LAYER-09 | Phase 5 | Pending |
| LAYER-10 | Phase 5 | Pending |
| OVERLAY-01 | Phase 4 | Pending |
| OVERLAY-02 | Phase 4 | Pending |
| OVERLAY-03 | Phase 4 | Pending |
| DRILL-01 | Phase 6 | Pending |
| DRILL-02 | Phase 6 | Pending |
| PERF-01 | Phase 6 | Pending |
| PERF-02 | Phase 6 | Pending |
| ENV-01 | Phase 1 | Pending |
| ENV-02 | Phase 1 | Pending |
| UX-01 | Phase 7 | Pending |
| UX-02 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 29 total
- Mapped to phases: 29
- Unmapped: 0

---
*Requirements defined: 2026-05-13*
*Last updated: 2026-05-13 — roadmap created, all 29 v1 requirements mapped*
