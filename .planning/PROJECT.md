# Mosaic Data Dashboard

## What This Is

A local Streamlit dashboard for the MOSAIC team to explore the processed datasets backing the MOSAIC project — an agent-based metapopulation simulation of cholera transmission across Sub-Saharan Africa. The dashboard reads directly from a local clone of [MOSAIC-data](https://github.com/InstituteforDiseaseModeling/MOSAIC-data) and lets a modeler pick a country and see every relevant data layer (WHO cholera cases, ENSO, WASH, demographics, OAG flight mobility, immunity, vaccine effectiveness, symptomatic fraction, similarity matrix) side by side, with time-series overlays that surface relationships between environmental/structural drivers and outbreak outcomes.

## Core Value

A MOSAIC modeler can pick a country and, in one screen, eyeball whether drivers like ENSO, WASH, or mobility track with cholera cases — fast enough that exploration replaces (rather than supplements) ad-hoc notebook work.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Country-first navigation: pick an ADM0 country, see all layers for it
- [ ] Side-by-side time-series overlays for cholera vs. drivers (ENSO, WASH, demographics, mobility) — shared x-axis, country-scoped
- [ ] Map view of Sub-Saharan Africa using the shipped shapefiles, with country selection
- [ ] At least one view per `processed/` subdir: WHO (annual + weekly), WASH, OAG, demographics, ENSO, shapefiles, immunity, vaccine_effectiveness, symptomatic, similarity_matrix
- [ ] Subnational drilldown (ADM1/ADM2) wherever the underlying data and shapefiles support it; gracefully fall back to country level otherwise
- [ ] Reads directly from a local checkout of `MOSAIC-data/processed/` — path configurable
- [ ] Fresh-read on every load (no manual refresh button needed)
- [ ] Runs fully offline once data is local — no external network calls in the hot path
- [ ] Sub-second pan/zoom and country switching, even with all SSA loaded (caching + appropriate file formats allowed; cache is invisible to user)
- [ ] Reproducible setup: pinned dependencies with a lockfile so any team member can `uv sync && streamlit run` and get an identical environment
- [ ] Anyone on the MOSAIC team can open it and figure it out without a walkthrough (usability is the v1 done bar)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Hosting / public deployment — local-laptop only; team usability does not require a URL
- Auto-fetching from GitHub or ingesting into a database — local checkout is the only data source for v1
- Writing back to data files / annotation features — read-only inspector
- Simulation outputs from MOSAIC itself — this dashboard is about the *input* data under `processed/`, not model results
- Authentication / multi-user state — single-user local tool
- Driver↔outcome statistical modeling (cross-correlation engines, regression dashboards) — v1 surfaces relationships visually via overlays; formal stats stay in notebooks for now

## Context

- **Data source**: Local clone at `~/MOSAIC/MOSAIC-data` with the dataset under `processed/`. Confirmed subdirs present: `WHO/` (annual 1949–2024, weekly 2023–2024, daily), `WASH/` (single CSV `WASH_data_Sikder_2023.csv`), `OAG/` (daily/weekly/monthly 2017 means), `demographics/` (UN WPP 1967–2100, Africa 2000–2023), `ENSO/` (daily/weekly/monthly 1970–2025), `shapefiles/` (per-country ADM0 plus `AFRICA_ADM0`), `immunity/`, `similarity_matrix/`, `symptomatic/`, `vaccine_effectiveness/`.
- **No `climate/` or `elevation/` directories** in current `processed/` despite being mentioned in the original brief — treat as upstream change; cover what's actually there.
- **Audience**: MOSAIC team modelers/researchers — they already know the data, so the dashboard's job is fast inspection and overlay, not pedagogy.
- **Tech**: Python + Streamlit. Geo stack will lean on geopandas / pydeck or folium for maps; plotly/altair for time series.
- **MOSAIC project is upstream and active** — `processed/` files will change over time. Dashboard must tolerate adds/renames without code changes where reasonable.

## Constraints

- **Tech stack**: Python + Streamlit — Fast to build, easy for team to run locally, ecosystem coverage for geo + time series.
- **Deployment**: Local laptop only — Lowest friction; no hosting overhead; matches single-user inspection workflow.
- **Performance**: Sub-second pan/zoom and country switching — Cholera/driver overlays must feel snappy enough for exploration loops; slow tools get abandoned for notebooks.
- **Offline**: No external network calls in the hot path — Air-gappable; some MOSAIC use contexts (travel, secure networks) require this.
- **Reproducibility**: Pinned dependencies + lockfile (uv preferred) — Any team member can clone and run with identical environment.
- **Read-only**: Dashboard never writes to `MOSAIC-data/` — Prevents accidental corruption of the source-of-truth data repo.

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python + Streamlit over R/Shiny or Dash | Fastest path to working app; user picked it; strong geo + plotly ecosystem | — Pending |
| Local file read (no DB, no GitHub fetch) | User has repo cloned; simplest; matches offline constraint | — Pending |
| Country-first navigation as the primary entry point | Matches how a modeler actually starts a session ("what's going on in country X?") | — Pending |
| Cover everything in `processed/` in v1, not just the listed subdirs | User chose full coverage; immunity/vaccine_effectiveness/symptomatic/similarity_matrix included | — Pending |
| Visual overlays for driver↔outcome relationships; formal stats deferred | v1 done bar is "team can use without explanation"; cross-corr UI is heavier scope than needed now | — Pending |
| Fresh-read on every load (no manual refresh button) | Dataset size manageable; user explicitly chose this; caching can be invisible/internal | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-13 after initialization*
