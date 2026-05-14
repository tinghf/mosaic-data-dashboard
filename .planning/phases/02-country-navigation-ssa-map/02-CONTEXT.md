# Phase 2: Country Navigation & SSA Map - Context

**Gathered:** 2026-05-14
**Status:** Ready for planning

<domain>
## Phase Boundary

A MOSAIC modeler selects a Sub-Saharan African country via EITHER a sidebar dropdown OR by clicking on an SSA map; that selection drives every layer view (Phases 3+) for the rest of the session.

In scope (REQ-mapped):
- NAV-01 — Single country picker drives every panel/view in the app
- NAV-02 — Selected country persists across view switches within a session
- MAP-01 — User sees SSA map rendered from `processed/shapefiles/AFRICA_ADM0` with clickable countries (alternate picker)
- MAP-02 — Map highlights selected country; stays in sync with dropdown picker (bidirectional)

Explicitly **not** in this phase:
- Per-layer views (WHO/WASH/ENSO/etc.) — Phase 3
- Time-series overlays — Phase 4
- Subnational (ADM1/ADM2) drilldown — Phase 6
- Performance tuning beyond "the map and picker feel responsive" — Phase 6

</domain>

<decisions>
## Implementation Decisions

### Geo library + dependencies
- **D-21:** **folium + streamlit-folium** is the map stack. Mature Leaflet-based; native click events return clicked-country payloads to Python via `st_folium`; rich tooltip/marker/choropleth support that Phase 4 can extend if overlay-on-map ever becomes a thing.
- **D-22:** **geopandas** is the geometry-reading library for both AFRICA_ADM0 and per-country `XXX_ADM0` shapefiles. This brings in geopandas + fiona + shapely + pyproj (the geo stack deferred from Phase 1 per D-19). Add via `uv add geopandas folium streamlit-folium`.
- **D-23:** Map and time-series charts may use different libraries. Phase 4 OVERLAY will use plotly/altair for shared-x time series; this phase uses folium for the map. No requirement to unify visual language across libs in v1.

### Country names + metadata
- **D-24:** **Static ISO3→name lookup** lives in a new module `src/mosaic_dashboard/data/country_metadata.py`. NOT read from `AFRICA_ADM0.dbf` via geopandas, NOT from `pycountry`. Hand-curated list in code is the single source of truth for country names.
- **D-25:** `country_metadata.py` exposes an **ordered Python list/tuple** of `(iso3, name)` entries (or a list of `CountryMeta` dataclasses with `iso3` and `name` fields — implementer's choice). **The order of entries in the list IS the picker order.** No separate `sort_order` field; reorder by editing the list.
- **D-26:** **First entry in the list IS the default country on first load.** One knob serves both "picker order" and "first-load default" — customizing the list also customizes the default.
- **D-27:** Ships **alphabetical-by-name** (`AGO/Angola → ...`) — so first-load default is Angola. Anyone (you, a teammate) can edit the list to pin a different country to the top or reorder regionally without touching picker code.
- **D-28:** **Minimal columns for v1: `iso3` + `name` only.** Region, population, language, and other metadata are deferred — add only when a downstream phase actually needs them (avoid the "no Dataset wrapper" anti-pattern from D-09, scaled up).
- **D-29:** `country_metadata.py` exposes a helper like `iter_countries() -> list[tuple[str, str]]` and `name_for(iso3: str) -> str` (or equivalent). The picker imports this; views needing a country name (e.g., page captions in Phase 7) import this. The list of 54 entries SHOULD be cross-checked against `shapefiles.available_countries()` at startup — emit a warning if they diverge so upstream data changes are caught (don't crash; tolerate per D-04 spirit).

### Picker UI + sidebar extension
- **D-30:** Country picker is a **second `st.selectbox` in `ui/sidebar.py::render()`**, rendered at the top of every page below the data-root override. Same pattern Phase 1 established — the entrypoint-once pattern is NOT used because that requires `st.navigation`, which we don't use under D-15.
- **D-31:** Picker UI shows the **country name** (e.g., "Angola"); the selectbox `format_func` maps ISO3 to name. The underlying value stored in session_state is the **ISO3 code**. Picker order = order from `country_metadata.iter_countries()` (alphabetical-by-name in v1).
- **D-32:** Both sidebar dropdown and map click write to `st.session_state[COUNTRY_SESSION_KEY]` (a single, well-named constant exported from `config.py` or a new `state.py` module — implementer's choice — mirroring Phase 1's `SESSION_KEY` for the data-root override). **Single source of truth for selected country.** Every page reads `st.session_state[COUNTRY_SESSION_KEY]` exclusively; no parallel state.
- **D-33:** On first session load, if `COUNTRY_SESSION_KEY` is unset, initialize it to the first entry from `country_metadata.iter_countries()` — i.e., Angola (D-26 + D-27). Subsequent reloads within the same session preserve whatever the user picked (NAV-02).

### Map view placement + UX
- **D-34:** SSA map lives on a **dedicated page**: `src/mosaic_dashboard/pages/01_SSA_Map.py`. Data Status remains at `00_Data_Status.py` — it stays the natural first-thing-a-teammate-sees diagnostic page.
- **D-35:** The map page calls `ui.sidebar.render()` at the top like every other page (Phase 1 pattern). The selected country is read from `st.session_state[COUNTRY_SESSION_KEY]`. The map renders the SSA outline with the selected country visually highlighted (e.g., a stroke color or fill differentiator).
- **D-36:** Clicking a country in the map fires a streamlit-folium event payload; an `on_change`-style handler reads the clicked feature's ISO3 (parsed from the shapefile feature's properties — see D-29's metadata cross-check), writes it into `st.session_state[COUNTRY_SESSION_KEY]`, and Streamlit reruns the page. The sidebar dropdown (rendered on rerun) reflects the new selection.
- **D-37:** Bidirectional sync is implicit in D-32: both inputs write to the same session_state key. On rerun, both inputs read from it. No callback chaining is needed beyond Streamlit's default rerun-on-change.

### Loader API extension (honoring D-20)
- **D-38:** Add **new functions to `data/shapefiles.py`** for geometry; do NOT change existing Phase-1 signatures.
  - Phase-1 functions (`available_countries()`, `load_africa()`, `load_country(iso3)`) keep their **Path-only-metadata** semantics — Data Status still calls them and they MUST continue to return the metadata DataFrame they always did.
  - Phase 2 ADDS: `load_africa_geometry() -> gpd.GeoDataFrame` and `load_country_geometry(iso3: str) -> gpd.GeoDataFrame`. These wrap `geopandas.read_file(...)`, cached via `@st.cache_data` keyed on `(path, mtime)` like the rest of the data layer (D-18).
- **D-39:** Geometry loaders honor the same empty-state contract as Phase 1: missing subdir / missing expected file → empty GeoDataFrame + `logging.warning(...)`; schema mismatch (e.g., DBF lacks an expected attribute) → raise `SchemaMismatchError` (D-12). Phase 2 thus extends — but does not violate — D-10, D-12, D-13.
- **D-40:** D-20 ("internal cache representation reversible without breaking the loader API contract") is honored literally: existing Phase-1 callers see no change; Phase 2 just grows the surface. If Phase 6 needs to swap geopandas for, say, lazy GeoArrow reads, only the new functions change.

### Claude's Discretion
- Exact constant naming (`COUNTRY_SESSION_KEY` vs `SELECTED_COUNTRY_KEY`) and which module exports it.
- Whether `country_metadata` exposes a plain list of tuples or a list of dataclasses (`CountryMeta(iso3=..., name=...)`).
- Folium-specific styling: color choice for selected vs. unselected countries, stroke widths, hover-tooltip formatting. Picker's `format_func` rendering (just name vs. `name (ISO3)` for power-user transparency).
- Whether to draw a small "currently selected" indicator on top of the dropdown picker.
- Whether map zoom/pan settings are persisted in session_state (Phase 6 PERF may revisit).
- How aggressively to cache the AFRICA_ADM0 GeoDataFrame (probably once-per-session via `@st.cache_data` since it's ~10MB and changes rarely).
- Implementation of the country_metadata vs. shapefiles.available_countries() startup sanity check (warning style, where it's logged).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 artifacts (locked decisions and the API surface Phase 2 builds on)
- `.planning/phases/01-foundation-data-layer/01-CONTEXT.md` — D-01..D-20; especially D-07 (ISO3), D-15 (pages/), D-18 (mtime-keyed cache), D-19 (no geo in Phase 1), D-20 (API contract stable)
- `.planning/phases/01-foundation-data-layer/01-SUMMARY.md`-style files in that phase dir — `01-01-SUMMARY.md` through `01-05-SUMMARY.md`
- `.planning/phases/01-foundation-data-layer/COLUMN_DISCOVERY.md` — shapefile filename convention notes
- `.planning/phases/01-foundation-data-layer/01-VERIFICATION.md` — Phase 1 verified state

### Project-level
- `.planning/PROJECT.md` — Core value, constraints (offline, read-only, uv lockfile)
- `.planning/REQUIREMENTS.md` — Full text of NAV-01, NAV-02, MAP-01, MAP-02; plus DRILL-01/02 (Phase 6) flagged for awareness so Phase 2 doesn't bake ADM0-only assumptions where ADM1/ADM2 will need to plug in
- `.planning/ROADMAP.md` §"Phase 2: Country Navigation & SSA Map" — Goal + 4 success criteria
- `CLAUDE.md` at repo root — Project conventions (D-15 pages/, D-07 ISO3, `uv run` launch)

### Code Phase 2 extends
- `src/mosaic_dashboard/ui/sidebar.py` — `render()` is extended with the country selectbox (D-30)
- `src/mosaic_dashboard/config.py` — `SESSION_KEY` for data-root override is the pattern Phase 2's `COUNTRY_SESSION_KEY` mirrors (D-32)
- `src/mosaic_dashboard/data/shapefiles.py` — Phase 1's Path-only metadata loaders kept as-is; Phase 2 adds geometry-reading functions (D-38)
- `src/mosaic_dashboard/pages/00_Data_Status.py` — Reference for the page structure Phase 2's `01_SSA_Map.py` follows

### Upstream data
- `~/MOSAIC/MOSAIC-data/processed/shapefiles/AFRICA_ADM0.{shp,shx,dbf,prj}` — Source for the SSA map. ADM0-level only; no ADM1/ADM2 files in current upstream (DRILL concern for Phase 6).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`ui/sidebar.py::render()`** — Already called at the top of every page; extending it with the country selectbox preserves the Phase 1 pattern (no entrypoint-once magic). New widget slot is below the data-root override.
- **`config.py::SESSION_KEY` (data-root override)** — The reference pattern for `COUNTRY_SESSION_KEY` (D-32). Same `st.session_state` lifecycle: initialized lazily, written by widget on_change, read everywhere.
- **`shapefiles.available_countries()`** — Already returns 54 sorted ISO3 codes. Use as a runtime sanity check against `country_metadata.iter_countries()` (D-29 — emit a warning if the two diverge).
- **`pages/00_Data_Status.py`** — Reference for Streamlit page structure: `set_page_config` (optional per-page), `sidebar.render()` at top, main content body, captions.
- **`logging_config.py::configure`** — Idempotent across reruns; Phase 2 code adds `logging.warning(...)` calls without needing new logger setup.

### Established Patterns
- **One module per `processed/` subdir** (D-05) — `country_metadata.py` is a SIDE module under `data/`, NOT a per-subdir loader (it doesn't read from `processed/`). It coexists with loaders without violating D-05's spirit.
- **Public/private cached read split** (D-18) — Geometry loaders in `shapefiles.py` follow the same pattern: public function resolves path + computes mtime, private `_read_*_cached(path, mtime)` does the geopandas read.
- **Empty-state with logging.warning** (D-10, D-13) — Geometry loaders honor the same contract.

### Integration Points
- **`COUNTRY_SESSION_KEY`** is the contract every Phase 3+ view reads from. Phase 3 layer views (WHO, WASH, ENSO, ...) will call `st.session_state[COUNTRY_SESSION_KEY]` to scope their data loads. Keep the key name stable from this phase onward.
- **`country_metadata.iter_countries()`** is the contract Phase 7 (UX) will use for layer captions ("WHO cholera cases for Angola") and downstream phases needing a country name from an ISO3 code.
- **Map page (`pages/01_SSA_Map.py`)** is the first Phase-1-extending page that uses the new geo stack. Phase 6 DRILL may add `pages/0X_Subnational.py` that reuses the folium pattern with ADM1/ADM2 shapefiles when they exist upstream.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly framed the picker-order question as a `sort_order` in the metadata file — codified here as D-25/D-26 (file-order IS picker-order, no separate column). Customization knob is "edit the list," not "edit a config flag."
- "First entry IS default" (D-26) was the user's explicit synthesis — one knob serves both purposes. This avoids a separate `is_default: True` flag and the validation burden that comes with it (zero or two defaults).
- folium + streamlit-folium choice (D-21) was anchored on click-event support and Phase-4 extensibility (overlays-on-map are a real possibility later). pydeck was viable (zero new deps) but the click event API is less mature.
- The "static ISO3→name" choice (D-24) prioritises **named-by-MOSAIC-convention** over **upstream-name-tracking** — if the DBF says "Tanzania, United Republic of" but the project conventionally says "Tanzania", the static list wins.
- D-29's "runtime sanity check between country_metadata and shapefiles.available_countries()" is a small but important safety net — if MOSAIC-data adds a country shapefile that the metadata doesn't know about, we want a warning, not a silent dropdown gap.

</specifics>

<deferred>
## Deferred Ideas

- **Region/population columns in country_metadata** — D-28 limits v1 to `iso3` + `name` only. Add when a downstream phase has a concrete need (regional groupings in the picker, regional overlays in Phase 4, per-country summary panels in Phase 7).
- **URL query param for selected country** (e.g., `?country=AGO`) — considered as an alternative sync mechanism (D-32 alternative B). Not adopted for v1. Reconsider if "bookmark a country view" becomes a UX ask.
- **Map-at-top-of-every-view** — considered as a placement option for MAP. Not adopted; SSA map is its own page (D-34). Could revisit in Phase 7 UX if usability testing reveals users want it always-on.
- **Regional groupings in the picker** (West/Central/East/Southern Africa with section headers) — out of v1 picker UX. Would require region column in country_metadata (deferred per D-28).
- **`pycountry` library for names** — not adopted; static list wins per D-24. Reconsider only if multi-language support becomes a requirement (and even then, a translated `country_metadata.py` is probably simpler).
- **Persisting map zoom/pan in session_state** — not in Phase 2 scope; Phase 6 PERF may revisit if the map feels janky.
- **Country summary panel** (population, region, region-mates) on the Map page — not in v1; Phase 7 UX may add it.
- **Subnational (ADM1/ADM2) drilldown** — Phase 6 concern, but flagged: don't bake ADM0-only assumptions into the country picker's internal data shape. Use `iso3` keys throughout so ADM1 codes (e.g., `AGO.01`) can be additive without breaking the picker.

</deferred>

---

*Phase: 02-Country Navigation & SSA Map*
*Context gathered: 2026-05-14*
