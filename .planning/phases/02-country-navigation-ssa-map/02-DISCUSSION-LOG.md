# Phase 2: Country Navigation & SSA Map - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-14
**Phase:** 02-Country Navigation & SSA Map
**Areas discussed:** Geo library choice, Country names source, Picker location, Map view placement, Sync model, Default country + picker order (merged into country_metadata), Loader API extension

---

## Geo library choice

### Q1 — Which geo library should drive the SSA map?

| Option | Description | Selected |
|--------|-------------|----------|
| folium + streamlit-folium | Mature Leaflet-based, native click events, rich tooltip/marker/choropleth support. | ✓ |
| pydeck (already installed) | Zero new deps; GPU-accelerated via deck.gl; click events less mature. | |
| plotly choropleth | HTML/SVG; integrates with Phase 4's plotly charts; click events via selectedData. | |

**User's choice:** folium + streamlit-folium
**Notes:** Click-event maturity and Phase-4 extensibility (overlays-on-map possible later) tipped the decision. Adds geopandas + fiona + shapely + pyproj to the dep set — the geo-stack deferral from D-19 ends here.

### Q2 — Should the map and Phase 4's charts use the same library?

| Option | Description | Selected |
|--------|-------------|----------|
| No — map and charts can be different libraries | Choose each on its own merits; mixing libs in Streamlit is common. | ✓ |
| Yes — prefer one lib for both | Visual consistency at the cost of map interactivity. | |

**User's choice:** No

---

## Country names source

### Q1 — How should the dropdown get human-readable country names?

| Option | Description | Selected |
|--------|-------------|----------|
| Read from AFRICA_ADM0.dbf via geopandas | Single source of truth; names track upstream. | |
| Static ISO3→name lookup | Hand-curated; named-by-MOSAIC-convention. | ✓ |
| Use pycountry library | ISO 3166 names; may not match MOSAIC conventions. | |

**User's choice:** Static ISO3→name lookup

### Q2 — Where should the ISO3→name mapping live?

| Option | Description | Selected |
|--------|-------------|----------|
| Inside shapefiles.py as a helper fn | Keeps name/shape discovery in one place. | |
| Separate module data/country_metadata.py | Dedicated module for country names + future per-country metadata. | ✓ |

**User's choice:** Separate module `data/country_metadata.py`

---

## Picker location

### Q1 — Where should the country picker live?

| Option | Description | Selected |
|--------|-------------|----------|
| Sidebar dropdown (extends sidebar.render()) | Always visible; consistent with Phase 1 data-root override. | ✓ |
| Top-of-page widget | Picker at top of each layer view; sidebar stays minimal. | |
| Dedicated 'Country' page | Pick once on Country page; persist in session. | |

**User's choice:** Sidebar dropdown

### Q2 — Picker option order?

| Option | Description | Selected |
|--------|-------------|----------|
| Alphabetical by name | User-friendly; type-to-find. | ✓ |
| Alphabetical by ISO3 | Matches shapefile filename ordering. | |
| Regional groupings | West/Central/East/Southern Africa subgroups. | |

**User's choice:** Alphabetical by name

---

## Map view placement

### Q1 — Where should the SSA map view live?

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated page (pages/01_SSA_Map.py) | Map is its own page; picker in sidebar works independently. | ✓ |
| Map at top of every layer view | Always visible; more screen real estate. | |
| Inline on a 'Country Overview' page | Map is one element among several. | |

**User's choice:** Dedicated page

### Q2 — Should the map page be the landing page?

| Option | Description | Selected |
|--------|-------------|----------|
| Keep Data Status as 00_, SSA Map as 01_ | Data Status remains the first diagnostic page. | ✓ |
| Demote Data Status, promote SSA Map | Map as natural first interaction. | |
| Both up, app.py routes to Map | Most polished UX; requires app.py refactor. | |

**User's choice:** Keep Data Status as 00_

---

## Sync model + default + picker order (merged after user clarification)

The initial framing asked default-country and sort-order as separate questions. User pushed back: "since there's a county metadata file already, could we create a sort order column in that metadata so user could customize the order for country to appear (and first load), with a default to alphabetical order?" — this merged the two into one decision via the metadata file.

### Q1 — Sync mechanism (asked but locked in same round)

| Option | Description | Selected |
|--------|-------------|----------|
| Both write to st.session_state[country_iso3] — single source of truth | Standard Streamlit pattern; one rerun cycle handles bidirectional sync. | ✓ |
| URL query param + session_state mirror | Bookmarkable country views; more code. | |

**User's choice:** session_state single source of truth

### Q2 — Sort order: explicit column vs. implicit (file order)?

| Option | Description | Selected |
|--------|-------------|----------|
| Implicit — file order IS picker order | Edit the list to reorder; simplest. | ✓ |
| Explicit integer column | Allows non-contiguous values; more flexible. | |
| Both — explicit wins if present, fallback to alphabetical | Most flexible; opt-in column. | |

**User's choice:** Implicit — file order IS picker order

### Q3 — Default-on-first-load mechanism?

| Option | Description | Selected |
|--------|-------------|----------|
| First entry in the metadata list | One knob serves both picker order and first-load default. | ✓ |
| Explicit is_default=True flag | Decouples list order from default; needs validation. | |
| No default — prompt 'select a country' | Honest UX; one extra interaction. | |

**User's choice:** First entry in the metadata list

### Q4 — What columns should country_metadata.py ship with?

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal: iso3 + name | Just what Phase 2 needs; add more later. | ✓ |
| iso3 + name + region | Region for future grouping/aggregates. | |
| iso3 + name + region + population | Most up-front metadata; risk of two-sources-of-truth drift. | |

**User's choice:** Minimal: iso3 + name

**Notes:** User's reframing turned three separate questions into a single coherent design: `data/country_metadata.py` is an ordered list of `(iso3, name)` entries; file order IS picker order; first entry IS default. Ships alphabetical-by-name (Angola first). Customizing the order also customizes the default — one knob, not two.

---

## Loader API extension (honoring D-20)

### Q1 — How should Phase 2 add geometry-reading without breaking D-20?

| Option | Description | Selected |
|--------|-------------|----------|
| Add new functions to shapefiles.py, leave existing ones alone | Path-only metadata fns unchanged; geometry fns are additive. | ✓ |
| New module data/geo.py | Separation by concern; slightly more files. | |
| Replace shapefiles.load_country() to return GeoDataFrame | Mutates signature; violates D-20. | |

**User's choice:** Add new functions to shapefiles.py
**Notes:** Phase 1's `available_countries()`, `load_africa()`, `load_country(iso3)` keep their Path-only-metadata semantics (Data Status still uses them). Phase 2 adds `load_africa_geometry()` and `load_country_geometry(iso3)` returning GeoDataFrames. Existing callers see no change. D-20 honored literally.

---

## Claude's Discretion

The following are intentionally left to the planner / executor:

- Exact constant naming (`COUNTRY_SESSION_KEY` vs `SELECTED_COUNTRY_KEY`) and which module exports it (config.py vs. new state.py).
- Whether `country_metadata` exposes plain `list[tuple[str, str]]` or `list[CountryMeta]` dataclasses.
- Folium-specific styling: color choice for selected vs. unselected countries, stroke widths, hover-tooltip formatting.
- Picker's `format_func` rendering — just name vs. `name (ISO3)` for power-user transparency.
- Cache scope of the AFRICA_ADM0 GeoDataFrame (likely `@st.cache_data` once-per-session; the file is ~10MB).
- Implementation of the country_metadata-vs-shapefiles.available_countries() startup sanity check (warning style, where it's logged).

## Deferred Ideas

Captured for future phases (also reflected in CONTEXT.md `<deferred>`):

- Region/population columns in country_metadata
- URL query param for selected country
- Map-at-top-of-every-view placement
- Regional groupings in the picker
- pycountry library for names
- Persisting map zoom/pan in session_state — Phase 6 PERF
- Country summary panel on the Map page — Phase 7 UX
- Subnational (ADM1/ADM2) drilldown awareness — flag for Phase 6
