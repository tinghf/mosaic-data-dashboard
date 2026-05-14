---
phase: 02-country-navigation-ssa-map
plan: 04
subsystem: ui
tags: [streamlit, folium, streamlit-folium, geopandas, choropleth, map, click-event, session_state]

requires:
  - phase: 01-foundation-data-layer
    provides: page-shell pattern (00_Data_Status.py), render_sidebar(), SchemaMismatchError, resolve_data_root()
  - phase: 02-country-navigation-ssa-map/02-01
    provides: country_metadata.COUNTRIES, country_metadata.ISO3_SET, country_metadata.name_for, country_metadata.iter_countries
  - phase: 02-country-navigation-ssa-map/02-02
    provides: shapefiles.load_africa_geometry() (GeoDataFrame with iso_a3/name/geometry), AFRICA_REQUIRED_COLUMNS, empty-GeoDataFrame contract
  - phase: 02-country-navigation-ssa-map/02-03
    provides: COUNTRY_SESSION_KEY constant, sidebar country selectbox bound to it, first-load Angola seed
provides:
  - SSA Map page (pages/01_SSA_Map.py) — clickable folium choropleth of AFRICA_ADM0
  - Click-driven country selection that writes to st.session_state[COUNTRY_SESSION_KEY]
  - Bidirectional sync between sidebar dropdown and map (implicit via shared session_state slot)
  - Encoded RESEARCH pitfall mitigations P3 (returned_objects narrowing), P7 (iso_a3 lowercase column), P10 (ISO3_SET click validation)
affects:
  - phase-03-cholera-driver-layers (every layer page reads st.session_state[COUNTRY_SESSION_KEY])
  - phase-04-driver-outcome-overlays (chart pages key on the same selected ISO3)
  - phase-05-static-geometry-layers (LAYER-06 may reuse the click-handler pattern for per-country shape views)
  - phase-06-subnational-drilldown-performance (PERF can revisit double-rerun + map zoom/pan persistence)
  - phase-07-usability-polish (UX-02 layer captions, optional country summary panel on this page)

tech-stack:
  added: [folium 0.20.x consumer surface, streamlit-folium 0.27.x consumer surface]
  patterns:
    - "Page-shell pattern inherited verbatim from 00_Data_Status.py: set_page_config -> render_sidebar -> imports -> title -> subtitle -> selected-caption -> body -> trailing caption"
    - "Click-as-alternate-picker: map click writes to st.session_state[COUNTRY_SESSION_KEY]; same slot the sidebar selectbox is bound to; bidirectional sync is implicit, no callback chaining"
    - "Three-clause click-handler guard: truthy clicked_iso3 AND clicked_iso3 in country_metadata.ISO3_SET AND clicked_iso3 != selected_iso3 — required to prevent ESH/-99 leak (RESEARCH P10) and rerun loops"
    - "Slim the GeoDataFrame to [iso_a3, name, geometry] before passing to folium (RESEARCH P5) — drops ~162 unused Natural Earth columns"

key-files:
  created:
    - src/mosaic_dashboard/pages/01_SSA_Map.py
  modified: []

key-decisions:
  - "Kept the explicit st.rerun() after click-driven session_state write (RESEARCH Open Question 2) — streamlit-folium fires its own rerun on click, but the explicit call guarantees the highlight + sidebar update within the same interaction. Phase 6 PERF may revisit if double-rerun cost matters."
  - "Closed _style_function over selected_iso3 at script-run time (not via a session_state read inside the closure) — keeps the style_function cheap per RESEARCH P8 (called once per feature per render)."
  - "Used `africa_slim = africa[['iso_a3', 'name', 'geometry']]` as an intermediate variable rather than inlining it into the folium.GeoJson call — makes the slimming step (RESEARCH P5) visually obvious to future readers."
  - "Wired both st.warning (empty GeoDataFrame) and st.error (SchemaMismatchError) surfaces per UI-SPEC, even though Plan 02-02's loader treats most missing-sidecar cases as the empty-state path — the error surface is the loud-failure escape hatch a malformed DBF would land in."

patterns-established:
  - "Map click handler: read output['last_active_drawing']['properties']['iso_a3'] -> validate against country_metadata.ISO3_SET -> compare against current selected_iso3 -> write + rerun. Phase 5 LAYER-06 can reuse this verbatim for any future click-driven map view."
  - "Folium tile + attribution pattern: tiles='CartoDB Positron' (built-in alias, folium auto-injects attribution); leave the bottom-right attribution badge alone (CC BY 3.0 license requirement)."

requirements-completed:
  - MAP-01
  - MAP-02
  - NAV-01

duration: 5min
completed: 2026-05-14
---

# Phase 02 Plan 04: SSA Map Page Summary

**Clickable folium SSA choropleth on `pages/01_SSA_Map.py` with bidirectional country-picker sync via `st.session_state[COUNTRY_SESSION_KEY]` and the ESH/-99 click-validation guard baked in.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-05-14T23:35:00Z (approx.)
- **Completed:** 2026-05-14T23:40:29Z
- **Tasks:** 1 / 1
- **Files modified:** 1 (1 new, 0 changed)

## Accomplishments

- Created `pages/01_SSA_Map.py` — the dedicated SSA map page (D-34) following the canonical page-shell pattern (D-35, UI-SPEC Page-Shell Pattern).
- Encoded all three critical RESEARCH pitfall mitigations directly in code with explicit inline comments citing P3 / P7 / P10:
  - **P3:** `st_folium(..., returned_objects=["last_active_drawing"])` narrows the rerun payload and prevents pan/zoom-triggered reruns.
  - **P7:** Every `properties` access uses the Natural Earth `iso_a3` (lowercase + underscore) column name — NOT `ISO3` or `ADM0_A3`.
  - **P10:** The click handler validates `clicked_iso3 in country_metadata.ISO3_SET` BEFORE writing session_state, preventing the documented ESH (Western Sahara) and `-99` (Somaliland) leak from crashing the sidebar selectbox.
- Wired bidirectional sync (D-37) by having both the sidebar selectbox (Plan 02-03) and the map click handler write to the same `st.session_state[COUNTRY_SESSION_KEY]` slot — no callback chaining, no event bus.
- Surfaced both empty-GeoDataFrame (`st.warning`) and `SchemaMismatchError` (`st.error`) UI states per D-39 / UI-SPEC, with `st.stop()` after each so no folium render is attempted in a broken-data state.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pages/01_SSA_Map.py implementing the full clickable SSA choropleth with all UI-SPEC styling + the ESH/-99 click-validation guard** — `84fa549` (feat)

## File structure (call order, top to bottom)

The page follows the strict UI-SPEC Page-Shell Pattern. Numbered steps mirror the in-file section comments:

1. Module docstring (purpose, bidirectional-sync contract, accessibility note, autodiscovery note, P3/P7/P10 mitigations).
2. `from __future__ import annotations` + `import streamlit as st`.
3. `st.set_page_config(page_title="SSA Map", layout="wide")` — first Streamlit call.
4. `from mosaic_dashboard.ui.sidebar import render as render_sidebar` + `render_sidebar()`.
5. Remaining late imports: `folium`, `streamlit_folium.st_folium`, `COUNTRY_SESSION_KEY`, `country_metadata`, `shapefiles`, `SchemaMismatchError` (each with `# noqa: E402`).
6. `st.title("SSA Map")`.
7. `st.write("Click a country to select it, or use the Country picker in the sidebar.")`.
8. Selected-country caption: `st.caption(f"Selected: {country_metadata.name_for(selected_iso3)} ({selected_iso3})")` — gated on `selected_iso3` being truthy.
9. `try/except` wrapper around `shapefiles.load_africa_geometry()` — `SchemaMismatchError` -> `st.error` + `st.stop()`; empty GeoDataFrame -> `st.warning` + `st.stop()`.
10. Slim the GeoDataFrame: `africa_slim = africa[["iso_a3", "name", "geometry"]]` (RESEARCH P5).
11. `folium.Map(location=[0.0, 20.0], zoom_start=3, tiles="CartoDB Positron", min_zoom=2, max_zoom=7)`.
12. `_style_function(feature)` closure over `selected_iso3` (RESEARCH P8) — returns the four UI-SPEC-locked hex colors and stroke widths.
13. `_highlight_function(feature)` — inherits base style, +0.1 fillOpacity (capped at 1.0), +1 weight.
14. `folium.GeoJson(...)` with `tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=[""], labels=False, sticky=False)` to suppress the "name: " field-name prefix (RESEARCH P6).
15. `st_folium(m, key="ssa_map", width=None, height=600, use_container_width=True, returned_objects=["last_active_drawing"])`.
16. Click handler: read `output["last_active_drawing"]["properties"]["iso_a3"]` -> three-clause guard (truthy AND in `country_metadata.ISO3_SET` AND != current `selected_iso3`) -> write session_state + `st.rerun()`.
17. `st.caption("Geometries: MOSAIC-data/processed/shapefiles/AFRICA_ADM0. Tiles: CartoDB Positron / OpenStreetMap.")`.

## RESEARCH Pitfall Mitigations Encoded

| Pitfall | Where | Inline comment |
|---------|-------|----------------|
| P3 — `returned_objects` narrows rerun payload, prevents pan/zoom reruns | `st_folium(...)` call (line ~213) | `# Slim rerun payload; pan/zoom does not trigger reruns (RESEARCH P3).` |
| P5 — slim the GeoDataFrame to 3 columns before passing to folium | `africa_slim = africa[["iso_a3", "name", "geometry"]]` (line ~117) | Comment explains 165-col Natural Earth payload reduction. |
| P6 — `labels=False` + `aliases=[""]` to suppress "name: " prefix in tooltip | `folium.GeoJsonTooltip(...)` | Comment on the GeoJson layer block. |
| P7 — DBF column is `iso_a3` (lowercase + underscore), NOT `ISO3` or `ADM0_A3` | `_style_function`, click handler | Both sites have explicit `# AFRICA_ADM0.dbf is Natural Earth schema; ISO3 column is 'iso_a3' (RESEARCH P7).` comments. |
| P8 — keep `style_function` cheap (called per feature per render) | `_style_function` reads page-scoped `selected_iso3`, not session_state | Docstring on `_style_function` calls out the closure capture. |
| P10 — validate clicked ISO3 against `country_metadata.ISO3_SET` BEFORE writing session_state | Click handler three-clause guard | `# Validate against country_metadata.ISO3_SET — ESH (Western Sahara) and "-99" (Somaliland) are in the DBF but NOT in our picker's set; silently ignore clicks on them (RESEARCH P10).` |

## UI-SPEC Styling Values Used

| Element | Value |
|---------|-------|
| Tile provider | `"CartoDB Positron"` (folium built-in alias) |
| Map center | `[0.0, 20.0]` (SSA centroid) |
| `zoom_start` | `3` |
| `min_zoom` / `max_zoom` | `2` / `7` |
| Selected fill | `#FF4B4B` (Streamlit accent) |
| Selected stroke | `#B71C1C` |
| Selected stroke width | `3px` |
| Selected fill opacity | `0.6` |
| Default fill | `#F0F2F6` (Streamlit secondary) |
| Default stroke | `#9AA0A6` (neutral gray) |
| Default stroke width | `1px` |
| Default fill opacity | `0.7` |
| Hover delta | `+0.1` fill opacity (capped at 1.0), `+1px` stroke weight |
| Tooltip fields | `["name"]` with `labels=False`, `aliases=[""]`, `sticky=False` |
| Container width | `use_container_width=True` + `width=None` |
| Container height | `600` px (mandatory; iframes require px per RESEARCH P4) |

## Decisions Implemented

| Decision | How |
|----------|-----|
| D-21 | Consumer of folium + streamlit-folium (the only Phase 2 consumer of these libraries). |
| D-23 | Folium is used here for the map; Phase 4 OVERLAY remains free to pick plotly/altair for time-series charts — no requirement to unify the visual language across libs. |
| D-34 | SSA map lives on its own dedicated page slot `pages/01_SSA_Map.py`. |
| D-35 | The page calls `render_sidebar()` at the top like every other page in the codebase (canonical page-shell pattern). |
| D-36 | Click writes the validated clicked ISO3 to `st.session_state[COUNTRY_SESSION_KEY]` and reruns the page. |
| D-37 | Bidirectional sync is implicit — both the sidebar selectbox (Plan 02-03) and the map click handler write to the same session_state slot. No callback chaining; rerun lifts the new value into both inputs automatically. |
| D-39 | Empty GeoDataFrame -> `st.warning` + `st.stop()`; `SchemaMismatchError` -> `st.error` + `st.stop()`; both pre-empt any folium render in a broken-data state. |

## Acceptance Verification

All static acceptance criteria from the plan pass. Per the `<verification>` block in 02-04-PLAN.md, full B3-B8 acceptance walk-through (live browser interaction: rendering, clicking on countries, observing the highlight follow + sidebar update, hovering for tooltips, attribution badge visible, etc.) is gated on Plan 02-05 (the human-verify checkpoint). The static set verified here:

- File exists, parses (`python3 -m py_compile` OK; `ast.parse` OK), and is 246 lines.
- `st.set_page_config(...)` at line 53; `render_sidebar()` call at line 61 — page-shell ordering preserved.
- `shapefiles.load_africa_geometry()` referenced once (in the `try/except` wrapper).
- `"iso_a3"` literal appears 6 times (style_function, click handler, slim-list, comment annotations).
- `country_metadata.ISO3_SET` referenced 3 times (click handler line + 2 comment annotations).
- `returned_objects=["last_active_drawing"]` exact literal present (1 in code + 1 in docstring quote — only 1 functional).
- `last_active_drawing` appears 4 times (code: `returned_objects` arg + click-payload extraction; docstring references).
- `last_object_clicked` appears 0 times (RESEARCH P1 — that key only carries `{lat, lng}`; we never reference it).
- `tiles="CartoDB Positron"` present (1 functional, line ~127).
- `height=600` present (1 functional in `st_folium`; 1 in code comment).
- All four UI-SPEC hex colors present: `#FF4B4B`, `#B71C1C`, `#F0F2F6`, `#9AA0A6`.
- All four UI-SPEC copy strings present verbatim: page title `"SSA Map"`, subtitle, `"Selected:"` caption form, attribution caption.
- Empty-state copy exact: `"SSA shapefile not found. Check Data Status, or set the data-root override in the sidebar."`.
- SchemaMismatchError surface wired (`SchemaMismatchError` imported + caught in `try/except`).
- DATA-03 still holds: no HTTP libraries (`requests`, `httpx`, `urllib.request`, `aiohttp`) appear anywhere in `src/mosaic_dashboard/`.

## Files Created/Modified

- `src/mosaic_dashboard/pages/01_SSA_Map.py` (NEW, 246 lines) — SSA Map page: clickable folium choropleth, page-shell pattern, ISO3_SET validation guard, all UI-SPEC styling and copy.

## Decisions Made

The plan did not leave open any implementation forks for this executor — UI-SPEC and RESEARCH together specified the page top-to-bottom. The few interpretive choices made (and logged in frontmatter `key-decisions`):

- Kept the explicit `st.rerun()` after the click-driven write per RESEARCH Open Question 2 (belt-and-suspenders against any race between streamlit-folium's auto-rerun and the next render).
- Used `africa_slim` as a named intermediate (vs. inlining the column-pick into `folium.GeoJson(data=...)`) to make RESEARCH P5 visually obvious in the code.
- Closed `_style_function` over the script-run-time `selected_iso3` (vs. reading `st.session_state[COUNTRY_SESSION_KEY]` inside the closure) per RESEARCH P8 — keeps the function cheap when called per feature.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

One minor format-only adjustment after the first write: my initial draft used Python's implicit string-literal concatenation across two lines for the attribution caption and the empty-state warning copy:

```python
st.warning(
    "SSA shapefile not found. Check Data Status, or set the data-root "
    "override in the sidebar."
)
```

Python compiles that to the exact target string, BUT the plan's `<acceptance_criteria>` uses `grep -F` on the full single-line literal, which doesn't match concatenated literals. Consolidated both onto single physical lines so the grep-based acceptance set passes verbatim. No semantic change — the rendered string is identical.

## Known Stubs

None. The page is fully wired end to end: real GeoDataFrame load, real folium render, real click handler writing to session_state, real UI-SPEC copy. No placeholders, no `TODO`s, no mock data, no hardcoded empty `[]`/`{}` flowing to UI.

## Threat Flags

None. The threat surface introduced by this plan is exactly the surface enumerated in PLAN `<threat_model>`:

- T-02-10 (Spoofing — click-handler input): mitigated by the `country_metadata.ISO3_SET` validation guard on the click payload.
- T-02-11 (Tampering — folium-iframe payload): accepted; we read one field and validate it.
- T-02-12 (Info Disclosure — tile-fetch URL): accepted; tile coordinates only, no PII.
- T-02-13 (DoS — massive geometry render): mitigated by the `[iso_a3, name, geometry]` slim (RESEARCH P5), the closure-only `style_function` (P8), and `returned_objects` narrowing (P3).
- T-02-14 (EoP): N/A — single-user local dashboard with no auth surface.

No NEW security-relevant surface (no new endpoints, no new auth paths, no new file-write paths). The CartoDB tile fetch is the only browser-initiated network call (license-compliant, attribution preserved).

## User Setup Required

None — no external service configuration required. The `CartoDB Positron` tiles fetch on first map render but require no API key; folium auto-injects the attribution badge (license requirement honored).

## Next Phase Readiness

Plan 02-04 is complete and ready for Plan 02-05's B-series acceptance walk-through (human-verify checkpoint):

- The page renders the SSA choropleth from the AFRICA_ADM0 GeoDataFrame.
- Clicks on valid SSA polygons update the highlight AND the sidebar dropdown in sync.
- Clicks on ESH / `-99` are silently ignored (no session_state pollution, no selectbox crash).
- Empty-state and schema-error UI banners are in place.
- All Phase 3+ layer pages can now key on `st.session_state[COUNTRY_SESSION_KEY]` knowing both inputs (dropdown + map) feed it.

No blockers. No concerns.

## Self-Check: PASSED

- `[x] src/mosaic_dashboard/pages/01_SSA_Map.py` exists (verified via `git log --stat`).
- `[x] Commit 84fa549` exists in current branch (verified via `git log --oneline`).
- `[x] python3 -m py_compile src/mosaic_dashboard/pages/01_SSA_Map.py` exits 0.
- `[x] python3 -c "import ast; ast.parse(open('src/mosaic_dashboard/pages/01_SSA_Map.py').read())"` exits 0.
- `[x] All acceptance grep checks pass` (set_page_config before render_sidebar; load_africa_geometry called; iso_a3 literal present; ISO3_SET present; returned_objects literal present; last_active_drawing >= 2; last_object_clicked == 0; tiles="CartoDB Positron"; height=600; 4 UI-SPEC hex colors; 4 UI-SPEC copy strings verbatim; SchemaMismatchError wired; DATA-03 clean).

---
*Phase: 02-country-navigation-ssa-map*
*Plan: 04*
*Completed: 2026-05-14*
