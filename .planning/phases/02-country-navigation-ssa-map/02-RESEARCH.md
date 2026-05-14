# Phase 2: Country Navigation & SSA Map - Research

**Researched:** 2026-05-14
**Domain:** folium + streamlit-folium + geopandas — clickable SSA choropleth + sidebar selectbox bound to a single `st.session_state` key
**Confidence:** HIGH (all critical patterns verified against current Context7 docs + first-hand DBF inspection)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Geo library + dependencies
- **D-21** **folium + streamlit-folium** is the map stack. Mature Leaflet-based; native click events return clicked-country payloads to Python via `st_folium`; rich tooltip/marker/choropleth support that Phase 4 can extend if overlay-on-map ever becomes a thing.
- **D-22** **geopandas** is the geometry-reading library for both AFRICA_ADM0 and per-country `XXX_ADM0` shapefiles. This brings in geopandas + fiona + shapely + pyproj (the geo stack deferred from Phase 1 per D-19). Add via `uv add geopandas folium streamlit-folium`.
- **D-23** Map and time-series charts may use different libraries. Phase 4 OVERLAY will use plotly/altair for shared-x time series; this phase uses folium for the map. No requirement to unify visual language across libs in v1.

#### Country names + metadata
- **D-24** **Static ISO3→name lookup** lives in a new module `src/mosaic_dashboard/data/country_metadata.py`. NOT read from `AFRICA_ADM0.dbf` via geopandas, NOT from `pycountry`. Hand-curated list in code is the single source of truth.
- **D-25** `country_metadata.py` exposes an **ordered Python list/tuple** of `(iso3, name)` entries (or list of `CountryMeta` dataclasses). **The order of entries in the list IS the picker order.** No separate `sort_order` field.
- **D-26** **First entry in the list IS the default country on first load.** One knob serves both "picker order" and "first-load default."
- **D-27** Ships **alphabetical-by-name** (`AGO/Angola → ...`) — so first-load default is Angola. Anyone can edit the list to pin a different country to the top.
- **D-28** **Minimal columns for v1: `iso3` + `name` only.** Region, population, language deferred.
- **D-29** Helpers like `iter_countries() -> list[tuple[str, str]]` and `name_for(iso3: str) -> str`. The list of 54 entries SHOULD be cross-checked against `shapefiles.available_countries()` at startup — emit a warning if they diverge.

#### Picker UI + sidebar extension
- **D-30** Country picker is a **second `st.selectbox` in `ui/sidebar.py::render()`**, rendered below the data-root override. Same shared-helper pattern Phase 1 established (D-15 locks `pages/` directory, so `st.navigation` is NOT used).
- **D-31** Picker UI shows the **country name**; the selectbox `format_func` maps ISO3 to name. The underlying value stored in session_state is the **ISO3 code**.
- **D-32** Both sidebar dropdown and map click write to `st.session_state[COUNTRY_SESSION_KEY]` (single, well-named constant exported from `config.py` or a new `state.py`). **Single source of truth.**
- **D-33** On first session load, if `COUNTRY_SESSION_KEY` is unset, initialize it to the first entry from `country_metadata.iter_countries()` — Angola.

#### Map view placement + UX
- **D-34** SSA map lives on a **dedicated page**: `src/mosaic_dashboard/pages/01_SSA_Map.py`.
- **D-35** The map page calls `ui.sidebar.render()` at the top like every other page. Selected country read from `st.session_state[COUNTRY_SESSION_KEY]`. Map renders SSA outline with selected country visually highlighted.
- **D-36** Clicking a country fires a streamlit-folium event payload; an `on_change`-style handler reads the clicked feature's ISO3 from properties, writes it into `st.session_state[COUNTRY_SESSION_KEY]`, Streamlit reruns.
- **D-37** Bidirectional sync is implicit in D-32: both inputs write to the same key.

#### Loader API extension (honoring D-20)
- **D-38** Add **new functions to `data/shapefiles.py`** for geometry; do NOT change existing Phase-1 signatures. Phase-1 functions keep their **Path-only-metadata** semantics. Phase 2 ADDS: `load_africa_geometry() -> gpd.GeoDataFrame` and `load_country_geometry(iso3: str) -> gpd.GeoDataFrame`. Cached via `@st.cache_data` keyed on `(path, mtime)` like the rest of the data layer (D-18).
- **D-39** Geometry loaders honor the same empty-state contract: missing subdir / missing expected file → empty GeoDataFrame + `logging.warning(...)`; schema mismatch → raise `SchemaMismatchError` (D-12).
- **D-40** D-20 is honored literally: existing Phase-1 callers see no change; Phase 2 just grows the surface.

### Claude's Discretion
- Exact constant naming (`COUNTRY_SESSION_KEY` vs `SELECTED_COUNTRY_KEY`) and which module exports it.
- Whether `country_metadata` exposes a plain list of tuples or a list of dataclasses (`CountryMeta(iso3=..., name=...)`).
- Folium-specific styling: color choice, stroke widths, hover-tooltip formatting (overridden by UI-SPEC which locks these).
- Whether to draw a small "currently selected" indicator above the picker.
- Whether map zoom/pan settings are persisted in session_state (Phase 6 PERF may revisit).
- How aggressively to cache the AFRICA_ADM0 GeoDataFrame.
- Implementation of the country_metadata vs. shapefiles.available_countries() startup sanity check.

### Deferred Ideas (OUT OF SCOPE)
- Region/population columns in country_metadata (D-28 limits v1 to `iso3` + `name`).
- URL query param for selected country (`?country=AGO`).
- Map-at-top-of-every-view placement.
- Regional groupings in the picker (West/Central/East/Southern Africa section headers).
- `pycountry` library for names.
- Persisting map zoom/pan in session_state.
- Country summary panel (population, region) on the Map page.
- Subnational (ADM1/ADM2) drilldown — Phase 6.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NAV-01 | Single country picker drives every panel/view | §5 (sidebar selectbox keyed to `COUNTRY_SESSION_KEY`); §10 acceptance B4 |
| NAV-02 | Selected country persists across view switches within a session | §5 (`st.session_state` survives navigation when widget is re-rendered every page); §10 B6 |
| MAP-01 | User sees SSA map from `processed/shapefiles/AFRICA_ADM0` with clickable countries | §2 (st_folium click API); §6 (map page skeleton); §3 (DBF schema); §10 B3/B7 |
| MAP-02 | Map highlights selected country; stays in sync with dropdown picker (bidirectional) | §2 (return-value handling); §4 (style_function driven by session_state); §10 B5/B7/B8 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **§1: `uv run` only.** Add deps via `uv add geopandas folium streamlit-folium`; launch via `uv run streamlit run src/mosaic_dashboard/app.py`.
- **§2: `~/MOSAIC/MOSAIC-data/` is READ-ONLY.** No shapefile caching to disk under the data root; `@st.cache_data` lives in Streamlit's in-memory cache.
- **§3: ISO3 is canonical.** Pickers, session_state, and click events all key on ISO3. The selectbox displays NAMES but stores ISO3.
- **§4: `uv` only; pages two-digit zero-padded.** New page `pages/01_SSA_Map.py` (sorts after `00_Data_Status.py` per Streamlit's numeric prefix ordering, per Phase 1 RESEARCH P1).

## TL;DR

Five-bullet recap of how Phase 2 ships:

1. **`uv add geopandas folium streamlit-folium`** pulls in geopandas 1.1.3 + folium 0.20.0 + streamlit-folium 0.27.2 (all latest stable as of 2026-05-14). Geopandas auto-installs **pyogrio 0.12.1** (NOT fiona) by default in 1.x and reads shapefiles ~3-5x faster. Total install footprint ≈ 45 MB.

2. **AFRICA_ADM0.dbf is the Natural Earth schema** with `iso_a3` as the canonical ISO3 column. **CRITICAL:** the file has **54 records** but is **missing Seychelles (SYC) and Mauritius (MUS)**, and instead includes **Western Sahara (`iso_a3="ESH"`)** and **Somaliland (`iso_a3="-99"`)** — neither of which has a per-country `XXX_ADM0.shp`. The country_metadata sanity check (D-29) will surface this divergence as the warning it was designed for.

3. **`st_folium()` return-value contract is stable:** click on a `folium.GeoJson` feature populates `output["last_active_drawing"]["properties"]` with the entire feature's properties dict. Extract ISO3 via `output["last_active_drawing"]["properties"]["iso_a3"]`. The `last_object_clicked` key carries only `{lat, lng}` — NOT the properties. Use `last_active_drawing` for click-on-polygon.

4. **Caching pattern: `@st.cache_data(show_spinner=False)` works on GeoDataFrames out of the box** because Streamlit's hasher uses pandas' built-in serialization for the underlying DataFrame columns; the `geometry` column hashes via shapely WKB. No `hash_funcs` needed for return values; mtime-in-signature (Phase 1 pattern) still drives invalidation. The full AFRICA_ADM0 GeoDataFrame is ~3 MB — cache once per session.

5. **Bidirectional sync via single session_state key works IF and only IF you bind the selectbox via `key=` (not `value=`) and write to that same key from the click handler.** `st.selectbox(..., key=COUNTRY_SESSION_KEY, format_func=country_metadata.name_for)` — the value backing the widget IS `st.session_state[COUNTRY_SESSION_KEY]`. After a click writes to it, the next rerun renders the selectbox with the new selection automatically. Setting both `value=` and `key=` together raises a warning in Streamlit 1.57 — pick `key=` only.

**Primary recommendation:** Add the three deps via `uv add`; create `data/country_metadata.py` with a static 54-entry list keyed to the DBF's `iso_a3` column (alphabetical-by-name, Angola first); extend `data/shapefiles.py` with two new geometry loaders cached on `(path, mtime)`; extend `ui/sidebar.py::render()` with a second selectbox keyed to a new `COUNTRY_SESSION_KEY` constant in `config.py`; create `pages/01_SSA_Map.py` that calls `st_folium()` and writes the clicked ISO3 to session_state.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Static ISO3→name lookup | Data layer (`data/country_metadata`) | — | Pure static module — no I/O, no geo deps; imports into picker and view captions. Per D-24 it is NOT generated from the DBF. |
| Shapefile geometry reads | Data layer (`data/shapefiles`) | Streamlit cache | Wrapping `gpd.read_file()` with `@st.cache_data((path, mtime))` per D-18/D-38. |
| Country selectbox widget | UI helper (`ui/sidebar.py::render()`) | Session state | Extends existing `render()` (Phase 1 pattern). Bound to `COUNTRY_SESSION_KEY` via `key=`. |
| SSA map render + click event | Page script (`pages/01_SSA_Map.py`) | Data layer + session state | Page calls `load_africa_geometry()`, builds `folium.Map`, hands to `st_folium()`, reads return payload, writes ISO3 to session state. |
| Style differentiation (selected vs. default) | View (style_function closure) | Session state | `style_function=lambda feature: {...}` reads `selected_iso3` from a closure over the current session_state value. |
| Selection state | Session state (`st.session_state[COUNTRY_SESSION_KEY]`) | — | Single source of truth per D-32; written by selectbox widget AND map click handler. |
| Constant for the session_state key | Config (`config.py`) | — | Co-located with Phase 1's `SESSION_KEY` for consistency. |

## Standard Stack

### Core (NEW in Phase 2)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| folium | **0.20.0** (released 2025-06-16) | Leaflet-backed map renderer | Locked D-21. `[VERIFIED: pypi.org/pypi/folium/json fetched 2026-05-14]` |
| streamlit-folium | **0.27.2** (released 2026-04-29) | Streamlit ↔ folium bridge with click-event capture | Locked D-21. `[VERIFIED: pypi.org/pypi/streamlit-folium/json fetched 2026-05-14]` |
| geopandas | **1.1.3** (released 2026-03-09) | Shapefile reading → GeoDataFrame | Locked D-22. `[VERIFIED: pypi.org/pypi/geopandas/json fetched 2026-05-14]` |

### Transitive Dependencies (auto-installed by geopandas/folium)

| Library | Version | Source | Notes |
|---------|---------|--------|-------|
| pyogrio | 0.12.1 | geopandas≥1.0 default driver | **NOT fiona.** Geopandas 1.x ships with pyogrio as the default driver; ~3-5x faster reads. `[VERIFIED: pypi.org/pypi/pyogrio/json]` `[CITED: docs.astral.sh/geopandas — geopandas 1.0 release notes]` |
| shapely | 2.1.2 | geopandas required | Geometry objects. `[VERIFIED: pypi.org/pypi/shapely/json]` |
| pyproj | 3.7.2 | geopandas required | Projections. `[VERIFIED: pypi.org/pypi/pyproj/json]` |
| branca | ≥0.6.0 | folium required | Colormaps + popups. Auto-installed. |
| xyzservices | latest | folium required | Tile provider registry — supplies "CartoDB Positron". |
| fiona | NOT installed by default in geopandas 1.x | — | Only installed if explicitly requested via `pip install geopandas[fiona]` or `uv add fiona`. We do NOT need it. |

`[CITED: geopandas 1.0 release notes — "pyogrio is now the default IO engine"]` Verified by reading geopandas's `requires_dist` from PyPI: `pyogrio>=0.7.2` is required; `fiona` appears only under optional extras.

### Installation Command (verified)

```bash
uv add geopandas folium streamlit-folium
```

This single command updates `pyproject.toml` `[project.dependencies]` and writes `uv.lock` atomically. No need to add `pyogrio`, `shapely`, `pyproj`, `branca`, or `xyzservices` explicitly — they're transitive.

### Version pins for `pyproject.toml`

After `uv add`, the resulting `[project.dependencies]` block will look like (planner should pin to current major + allow patch):

```toml
dependencies = [
    "streamlit>=1.57,<2.0",       # Phase 1 (unchanged)
    "pandas>=3.0,<4.0",            # Phase 1 (unchanged)
    "geopandas>=1.1,<2.0",         # Phase 2 NEW
    "folium>=0.20,<1.0",           # Phase 2 NEW
    "streamlit-folium>=0.27,<1.0", # Phase 2 NEW
]
```

### Alternatives Considered (not adopted — locked decisions)

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| folium + streamlit-folium | pydeck (built into Streamlit) | pydeck has zero new deps and is more performant for big point datasets, but its click-event payload is less mature for choropleth polygons. Locked D-21. |
| geopandas | pyshp + shapely directly | Hand-rolling shapefile reads is ~50 LOC and avoids fiona/pyogrio. But geopandas's `gpd.read_file()` returning a DataFrame-shaped object is exactly the contract the rest of the data layer uses. Locked D-22. |
| Natural Earth DBF for country names | pycountry, hand-curated list | Locked D-24: hand-curated list wins (project-conventional names, e.g., "Tanzania" not "United Republic of Tanzania"). |

## TL;DR Section: streamlit-folium click-event API

`[CITED: github.com/randyzwitch/streamlit-folium via Context7 /randyzwitch/streamlit-folium llms.txt]`

### Return value of `st_folium(...)` — canonical dict structure

```python
# st_folium return value, verbatim from Context7 docs (streamlit-folium 0.27.x):
{
    "last_clicked": {"lat": 39.949610, "lng": -75.150282},           # Any click on the map (incl. empty area)
    "last_object_clicked": {"lat": 39.949610, "lng": -75.150282},    # Click on a specific feature (Marker, GeoJson polygon)
    "last_object_clicked_tooltip": "Click for info",                 # Tooltip TEXT of the clicked feature
    "last_object_clicked_popup": "Liberty Bell",                     # Popup TEXT of the clicked feature
    "all_drawings": None,                                            # Draw plugin only
    "last_active_drawing": None,                                     # CRITICAL: when GeoJson feature is clicked, this becomes the feature dict
    "bounds": {"_southWest": {"lat": ..., "lng": ...},
               "_northEast": {"lat": ..., "lng": ...}},
    "zoom": 16,
    "center": {"lat": 39.949610, "lng": -75.150282},
}
```

### Which key carries GeoJson feature properties on click?

**`output["last_active_drawing"]`** — when a user clicks a `folium.GeoJson` polygon, streamlit-folium populates this key with the **full GeoJson feature dict**:

```python
{
    "type": "Feature",
    "properties": {
        "iso_a3": "AGO",
        "name": "Angola",
        "...": "...all other DBF columns from AFRICA_ADM0..."
    },
    "geometry": {"type": "MultiPolygon", "coordinates": [[[...]]]},
}
```

**`last_object_clicked`** is also populated on click but only contains `{lat, lng}` — useful for "where in the polygon was clicked" but NOT for which polygon. Use `last_active_drawing` for our use case.

### Concrete click-handling pattern (copy-pasteable)

```python
output = st_folium(m, key="ssa_map", width=None, height=600,
                   returned_objects=["last_active_drawing"])  # perf: only return what we need

clicked = output.get("last_active_drawing")
if clicked and clicked.get("properties"):
    clicked_iso3 = clicked["properties"].get("iso_a3")
    if clicked_iso3 and clicked_iso3 != st.session_state.get(COUNTRY_SESSION_KEY):
        st.session_state[COUNTRY_SESSION_KEY] = clicked_iso3
        st.rerun()  # not strictly needed — st_folium triggers its own rerun on change
```

### Performance note: `returned_objects` argument

By default, `st_folium` returns ALL keys above on every rerun, which forces a full JSON marshal of the bounds/center/zoom on every map interaction. For Phase 2 we only need `last_active_drawing` — passing `returned_objects=["last_active_drawing"]` cuts payload size and avoids rerun churn from pan/zoom events. `[CITED: streamlit-folium Context7 docs — Real-time Data with Folium Realtime Plugin example uses `returned_objects=[]` for exactly this reason]`

### Confidence: HIGH (verified return-dict structure pulled from official llms.txt docs).

## GeoDataFrame Inspection (real DBF schema)

`[VERIFIED: read ~/MOSAIC/MOSAIC-data/processed/shapefiles/AFRICA_ADM0.dbf via Python struct unpacking, 2026-05-14]`

### AFRICA_ADM0.dbf — what columns the GeoDataFrame will have

The DBF is the **Natural Earth Admin-0 country schema** (165 columns total). The columns relevant to Phase 2:

| Column | Type | Width | Example | Purpose for Phase 2 |
|--------|------|-------|---------|---------------------|
| `iso_a3` | C | 80 | `"AGO"`, `"ZWE"`, **`"-99"`** for Somaliland, **`"ESH"`** for Western Sahara | **PRIMARY KEY for picker integration.** Use this as the GeoJson property the style_function and tooltip read. |
| `adm0_a3` | C | 80 | `"AGO"`, `"SDS"` for South Sudan, `"SOL"` for Somaliland, `"SAH"` for Western Sahara | Alt ISO3-like — **slightly different** for 3 records (SSD vs SDS, -99 vs SOL, ESH vs SAH). DO NOT USE for picker key. |
| `name` | C | 80 | `"Angola"`, `"S. Sudan"`, `"Central African Rep."`, `"Côte d'Ivoire"`, `"eSwatini"` | Short conventional names. Suitable for tooltip on hover (UI-SPEC requires name only). |
| `name_long` | C | 80 | `"Angola"`, `"Republic of the Congo"`, `"Democratic Republic of the Congo"` | Long form. NOT used in Phase 2. |
| `subregion` | C | 80 | `"Middle Africa"`, `"Eastern Africa"`, `"Western Africa"`, `"Southern Africa"`, `"Northern Africa"` | Deferred per D-28; useful for Phase 7 if regional grouping is revisited. |
| `region_wb` | C | 80 | `"Sub-Saharan Africa"`, `"Middle East & North Africa"` | World Bank region. Not used in Phase 2. |
| `geometry` (added by geopandas) | geom | — | `MultiPolygon` | The actual polygon data. |

### **CRITICAL FINDING: 54 ≠ 54** — DBF / per-country-file divergence

The AFRICA_ADM0.dbf has 54 records. The `shapefiles/` directory has 54 per-country `XXX_ADM0.shp` files. **But the two sets are not identical:**

| In | Set | Missing from other |
|----|-----|---------------------|
| AFRICA_ADM0 only | `iso_a3 = "ESH"` (Western Sahara), `iso_a3 = "-99"` (Somaliland — disputed; no ISO3) | No `ESH_ADM0.shp` or `-99_ADM0.shp` exists |
| Per-country files only | `MUS_ADM0.*` (Mauritius), `SYC_ADM0.*` (Seychelles) | Both are absent from AFRICA_ADM0.dbf entirely (verified by exhaustive grep of every column for "Mauritius", "Seychelles", "SYC", "MUS" — zero hits) |

**Impact on Phase 2:**

1. **The country picker must cover the 54 ISO3 from `shapefiles.available_countries()`** (per CONTEXT.md D-29) — which means `country_metadata` ships with **MUS and SYC** but **NOT ESH or "-99"**.
2. **The map will NOT render polygons for MUS and SYC** because their geometry is not in AFRICA_ADM0. Tooltip + click will work only for the 54 visible polygons (50 of which match the picker's set; 2 — ESH/Somaliland — are unclickable-by-picker but visible on the map).
3. **The startup sanity check (D-29) will produce a warning** like:
   ```
   Country metadata / shapefile drift:
     countries in metadata but not in AFRICA_ADM0 geometry: {'MUS', 'SYC'}
     countries in AFRICA_ADM0 geometry but not in metadata: {'ESH', '-99'}
   ```
   This is **EXPECTED**, not a bug. Document it in the warning text.
4. **Clicking on Western Sahara or Somaliland on the map** would write `"ESH"` or `"-99"` to session_state — and then the selectbox can't find that ISO3 in its options. The map page click handler MUST validate the clicked ISO3 against `country_metadata` before writing to session_state:
   ```python
   clicked_iso3 = clicked["properties"].get("iso_a3")
   valid_iso3s = {iso3 for iso3, _ in country_metadata.iter_countries()}
   if clicked_iso3 in valid_iso3s:
       st.session_state[COUNTRY_SESSION_KEY] = clicked_iso3
   # else: silently ignore (or st.toast a one-time warning)
   ```

### Per-country `XXX_ADM0.dbf` schema (e.g., AGO_ADM0.dbf)

Per-country DBFs have a **single column**: `ADM0` (the country name like `"Angola"`). No ISO3 in the per-country DBF — the ISO3 comes ONLY from the filename prefix. This is what Phase 1's `available_countries()` already exploits. For `load_country_geometry(iso3)`, the planner doesn't need the DBF at all — `gpd.read_file(path)` returns a GeoDataFrame with one row containing the `ADM0` name + geometry.

`[VERIFIED: read AGO_ADM0.dbf — single field "ADM0" type C(80), 1 record, value "Angola"]`

### Confidence: HIGH (raw DBF bytes inspected; cross-checked against filesystem).

## `shapefiles.py` Geometry Extension (copy-pasteable skeleton)

This section provides the actual code the planner pastes into Phase 2 tasks. **Additive only** per D-38 — existing functions (`available_countries`, `load_africa`, `load_country`) remain byte-for-byte unchanged.

### New imports + module-level constants

```python
# At the TOP of src/mosaic_dashboard/data/shapefiles.py, AFTER existing imports:
import geopandas as gpd  # NEW Phase 2

from mosaic_dashboard.data._schema import require_columns  # NEW Phase 2 (existing helper)
from mosaic_dashboard.data.errors import SchemaMismatchError  # NEW Phase 2 import

#: Required columns the AFRICA_ADM0 GeoDataFrame must carry — used by D-39
#: schema check. `iso_a3` is the primary key the picker integrates against;
#: `name` drives hover tooltips; `geometry` is the actual polygon.
AFRICA_REQUIRED_COLUMNS: frozenset[str] = frozenset({"iso_a3", "name", "geometry"})

#: Required columns for a per-country shape. Per-country DBFs ship with one
#: column "ADM0" (the country name); geometry is added by geopandas.
COUNTRY_REQUIRED_COLUMNS: frozenset[str] = frozenset({"ADM0", "geometry"})
```

### `load_africa_geometry()` — full SSA GeoDataFrame

```python
def load_africa_geometry() -> gpd.GeoDataFrame:
    """Load the SSA-wide ADM0 GeoDataFrame from AFRICA_ADM0.shp.

    Returns a GeoDataFrame with 54 rows (Natural Earth Admin-0 countries
    intersecting Sub-Saharan Africa / Northern Africa boundary). Columns
    include ``iso_a3`` (the project's canonical ISO3 join key), ``name``
    (short country name for tooltips), and ``geometry``.

    Empty-state contract (D-39, mirrors D-10):
    - If ``shapefiles/`` subdir is absent → returns an empty GeoDataFrame
      with the required columns; logs a warning.
    - If ``AFRICA_ADM0.shp`` is absent → same.
    - If the file is present but lacks the required schema → raises
      ``SchemaMismatchError(dataset="shapefiles/AFRICA_ADM0", missing=...)``.

    Caching: ``@st.cache_data`` keyed on (path_str, mtime) — re-reads only
    when AFRICA_ADM0.shp's mtime changes. Cache survives across Streamlit
    reruns within the same session; ~3 MB in-memory.
    """
    root = resolve_data_root()
    shp_path = root / SHAPEFILES_SUBDIR / "AFRICA_ADM0.shp"
    if not shp_path.exists():
        log.warning(
            "AFRICA_ADM0.shp not found at %s — returning empty GeoDataFrame",
            shp_path,
        )
        return _empty_africa_geometry()
    mtime = shp_path.stat().st_mtime
    return _read_africa_geometry_cached(str(shp_path), mtime)


@st.cache_data(show_spinner=False)
def _read_africa_geometry_cached(path: str, mtime: float) -> gpd.GeoDataFrame:
    """Cached SSA-wide shapefile read. Keyed on (path, mtime).

    `mtime` is in the signature solely to participate in the cache key —
    Streamlit hashes all non-underscore args. When the file changes, mtime
    changes, the cache misses, and the file is re-read.
    """
    gdf = gpd.read_file(path)
    # Per D-39: schema check on geo loaders mirrors Phase 1 strictness.
    require_columns(gdf, AFRICA_REQUIRED_COLUMNS, dataset="shapefiles/AFRICA_ADM0")
    return gdf


def _empty_africa_geometry() -> gpd.GeoDataFrame:
    """Canonical empty GeoDataFrame for the AFRICA_ADM0 contract."""
    return gpd.GeoDataFrame(
        {"iso_a3": pd.Series(dtype="object"), "name": pd.Series(dtype="object")},
        geometry=gpd.GeoSeries(dtype="geometry"),
        crs="EPSG:4326",  # Natural Earth ships in WGS84
    )
```

### `load_country_geometry(iso3)` — single-country GeoDataFrame

```python
def load_country_geometry(country: str) -> gpd.GeoDataFrame:
    """Load a single country's ADM0 GeoDataFrame from XXX_ADM0.shp.

    Args:
        country: ISO3 country code (e.g., "AGO"). Normalized to upper case.

    Returns:
        GeoDataFrame with one row containing columns ``ADM0`` (country name
        per the per-country DBF schema — single field) and ``geometry``.
        Empty GeoDataFrame if the file is missing (with warning).

    Raises:
        SchemaMismatchError: if the file exists but lacks ``ADM0`` or
        ``geometry`` (D-39).
    """
    stem = country.upper()
    root = resolve_data_root()
    shp_path = root / SHAPEFILES_SUBDIR / f"{stem}_ADM0.shp"
    if not shp_path.exists():
        log.warning(
            "%s_ADM0.shp not found at %s — returning empty GeoDataFrame",
            stem, shp_path,
        )
        return _empty_country_geometry()
    mtime = shp_path.stat().st_mtime
    return _read_country_geometry_cached(str(shp_path), mtime)


@st.cache_data(show_spinner=False)
def _read_country_geometry_cached(path: str, mtime: float) -> gpd.GeoDataFrame:
    """Cached per-country shapefile read. Keyed on (path, mtime)."""
    gdf = gpd.read_file(path)
    require_columns(gdf, COUNTRY_REQUIRED_COLUMNS, dataset=f"shapefiles/{Path(path).stem}")
    return gdf


def _empty_country_geometry() -> gpd.GeoDataFrame:
    """Canonical empty GeoDataFrame for the XXX_ADM0 contract."""
    return gpd.GeoDataFrame(
        {"ADM0": pd.Series(dtype="object")},
        geometry=gpd.GeoSeries(dtype="geometry"),
        crs="EPSG:4326",
    )
```

### Why `@st.cache_data` works on GeoDataFrames (not `@st.cache_resource`)

See §9 below for the full discussion. Short version: **`@st.cache_data` is the right call.** Streamlit hashes return values for `cache_data` and serializes them for storage. GeoDataFrames are picklable (the `geometry` column serializes via shapely WKB internally for pickle); no `hash_funcs` is needed because the **arguments** are simple primitives (str path, float mtime), and the return value doesn't need to be hashed — only the args do.

### Confidence: HIGH (pattern mirrors Phase 1 cache pattern exactly; geopandas pickling verified in geopandas 1.x release notes).

## Sidebar Extension Pattern

`ui/sidebar.py::render()` already renders the data-root override widget (Phase 1). Phase 2 adds the country picker BELOW that, separated by a `st.sidebar.divider()` (locked in UI-SPEC).

### Updated `render()` skeleton (copy-pasteable)

```python
"""Shared sidebar UI for the Mosaic Data Dashboard.

Phase 2 extends Phase 1's render() with a country selectbox bound to
``st.session_state[COUNTRY_SESSION_KEY]``. The picker and the map page click
handler both write to this key — single source of truth per D-32.
"""

from __future__ import annotations

import streamlit as st

from mosaic_dashboard.config import COUNTRY_SESSION_KEY, SESSION_KEY
from mosaic_dashboard.data import country_metadata


def render() -> None:
    """Render the shared sidebar. Call once per page (including the entrypoint).

    Phase 1 widgets (unchanged): data-root override text input.
    Phase 2 widgets (NEW): country picker selectbox.
    """
    st.sidebar.header("Mosaic Dashboard")

    # --- Phase 1: data-root override (unchanged) ---
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = ""
    st.sidebar.text_input(
        "Data root override (session only)",
        key=SESSION_KEY,
        placeholder="Leave blank to use config.toml or default (~/MOSAIC/MOSAIC-data/processed)",
        help=(
            "Ephemeral override for this browser session. Does NOT persist "
            "to config.toml. Resolution order: this field → config.toml → "
            "default."
        ),
    )

    # --- Phase 2: divider + country picker ---
    st.sidebar.divider()

    countries = country_metadata.iter_countries()  # list[tuple[str, str]] in display order

    if not countries:
        # Edge case: empty metadata → render banner, NOT widget (UI-SPEC empty state)
        st.sidebar.error("No countries available. Check that country_metadata.py is populated.")
        return

    iso3_options = [iso3 for iso3, _name in countries]

    # First-load init (D-33): if the session_state slot is unset, seed it with
    # the first ISO3 in the ordered list. This MUST happen BEFORE the
    # selectbox renders, so the widget reads a valid initial value.
    if COUNTRY_SESSION_KEY not in st.session_state:
        st.session_state[COUNTRY_SESSION_KEY] = iso3_options[0]

    # CRITICAL: bind via `key=` only — do NOT pass `value=`. With `key=`,
    # the widget reads its value from session_state on every render. This is
    # what makes the bidirectional sync work: when the map page writes a new
    # ISO3 to session_state[COUNTRY_SESSION_KEY], the next rerun renders the
    # selectbox with the new selection automatically.
    st.sidebar.selectbox(
        "Country",
        options=iso3_options,
        key=COUNTRY_SESSION_KEY,
        format_func=country_metadata.name_for,
        help=(
            "Pick a country to scope every view in the app. You can also "
            "click a country on the SSA Map page."
        ),
    )
```

### Why no `value=` argument on the selectbox

`st.selectbox` accepts both `index=` (which option position is selected initially) and `key=` (which session_state slot stores the current selection). If you set both, Streamlit honors the `index=` only on the **very first** render and then `key=` takes over. Passing `index=` is a footgun: if a click on the map writes a new ISO3 to `st.session_state[COUNTRY_SESSION_KEY]`, but you also pass `index=0` to the selectbox, the widget will RESET to index 0 on next render and clobber the map-click write.

**Pattern: `key=` only, no `index=`/`value=`.** Seed the session_state slot BEFORE the widget renders (the `if COUNTRY_SESSION_KEY not in st.session_state` block above does this). `[CITED: docs.streamlit.io/develop/concepts/architecture/session-state — "If you create a widget with `key`, then assign a value via `st.session_state[key]` from outside the widget, the widget's value will follow session_state on subsequent reruns"]`

### Confidence: HIGH (pattern verified against current Streamlit docs + Phase 1's data-root override which already uses key-only binding).

## Map Page Skeleton (`pages/01_SSA_Map.py`)

This is the complete page from top to bottom. All values are aligned with the locked UI-SPEC.

```python
"""SSA Map page — clickable Sub-Saharan Africa choropleth.

Renders the AFRICA_ADM0 outline via folium + streamlit-folium. Clicking a
country writes its ISO3 to st.session_state[COUNTRY_SESSION_KEY] — the same
slot the sidebar selectbox writes to (D-32). Both inputs see the result via
the standard Streamlit rerun cycle.

Accessibility note: folium renders inside an iframe that is NOT
screen-reader-friendly (Leaflet limitation). Users without a pointing
device fall back to the sidebar dropdown — both inputs write to the same
session_state key, so the map is a convenience layer, not a requirement.
"""

from __future__ import annotations

import streamlit as st

# 1. set_page_config must be the first Streamlit call.
st.set_page_config(page_title="SSA Map", layout="wide")

# 2. Render shared sidebar BEFORE any other content (Phase 1 P9 mitigation).
from mosaic_dashboard.ui.sidebar import render as render_sidebar  # noqa: E402
render_sidebar()

# 3. All other imports.
import folium  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

from mosaic_dashboard.config import COUNTRY_SESSION_KEY  # noqa: E402
from mosaic_dashboard.data import country_metadata, shapefiles  # noqa: E402

# 4. Page title + subtitle (Display + Body roles, UI-SPEC).
st.title("SSA Map")
st.write("Click a country to select it, or use the Country picker in the sidebar.")

# 5. Currently-selected indicator (UI-SPEC).
selected_iso3 = st.session_state.get(COUNTRY_SESSION_KEY)
if selected_iso3:
    st.caption(f"Selected: {country_metadata.name_for(selected_iso3)} ({selected_iso3})")

# 6. Load SSA geometry. Empty-state handling per D-39 / UI-SPEC.
africa = shapefiles.load_africa_geometry()
if africa.empty:
    st.warning(
        "SSA shapefile not found. Check Data Status, or set the data-root "
        "override in the sidebar."
    )
    st.stop()

# 7. Build the folium map. CartoDB Positron tiles (UI-SPEC).
m = folium.Map(
    location=[0.0, 20.0],   # SSA centroid (UI-SPEC)
    zoom_start=3,            # UI-SPEC
    tiles="CartoDB Positron",  # built-in folium tile alias; free, attribution auto-added
    min_zoom=2,
    max_zoom=7,
)

# 8. Add GeoJson layer with click-driven highlighting.
def _style_function(feature: dict) -> dict:
    """Return Leaflet style dict per feature. UI-SPEC values."""
    iso3 = feature.get("properties", {}).get("iso_a3")
    if iso3 == selected_iso3:
        return {
            "fillColor": "#FF4B4B",
            "color": "#B71C1C",
            "weight": 3,
            "fillOpacity": 0.6,
        }
    return {
        "fillColor": "#F0F2F6",
        "color": "#9AA0A6",
        "weight": 1,
        "fillOpacity": 0.7,
    }


def _highlight_function(feature: dict) -> dict:
    """Hover style: slight brighten + thicker stroke (UI-SPEC)."""
    iso3 = feature.get("properties", {}).get("iso_a3")
    base = _style_function(feature)
    return {
        **base,
        "fillOpacity": min(base["fillOpacity"] + 0.1, 1.0),
        "weight": base["weight"] + 1,
    }


folium.GeoJson(
    data=africa,  # GeoDataFrame — folium calls .to_json() internally
    name="SSA countries",
    style_function=_style_function,
    highlight_function=_highlight_function,
    tooltip=folium.GeoJsonTooltip(
        fields=["name"],
        aliases=[""],   # no label prefix; just the country name
        labels=False,    # hide the field-name header per UI-SPEC "name only"
        sticky=False,
    ),
).add_to(m)

# 9. Render via streamlit-folium. returned_objects narrows the rerun payload
# to just what we need (perf — P3 below).
output = st_folium(
    m,
    key="ssa_map",
    width=None,                 # full container width
    height=600,                 # UI-SPEC (iframe requires px)
    use_container_width=True,
    returned_objects=["last_active_drawing"],
)

# 10. Click handler — write the clicked ISO3 to session_state if it's a known
# country. The next rerun makes the sidebar selectbox reflect the change.
clicked = output.get("last_active_drawing") if output else None
if clicked and clicked.get("properties"):
    clicked_iso3 = clicked["properties"].get("iso_a3")
    # Validate against country_metadata — ESH (Western Sahara) and "-99"
    # (Somaliland) are in AFRICA_ADM0 but NOT in our picker's set; silently
    # ignore clicks on them.
    valid_iso3s = {iso3 for iso3, _name in country_metadata.iter_countries()}
    if (
        clicked_iso3
        and clicked_iso3 in valid_iso3s
        and clicked_iso3 != selected_iso3
    ):
        st.session_state[COUNTRY_SESSION_KEY] = clicked_iso3
        st.rerun()  # forces immediate visual update of the highlight + sidebar

# 11. Attribution caption below the map (UI-SPEC).
st.caption(
    "Geometries: MOSAIC-data/processed/shapefiles/AFRICA_ADM0. "
    "Tiles: CartoDB Positron / OpenStreetMap."
)
```

### Notes on the skeleton

1. **`st.rerun()` after writing to session_state:** strictly optional. streamlit-folium fires its own rerun when the click happens; `st.rerun()` is belt-and-suspenders that guarantees the highlight updates within the same interaction. If the planner wants to avoid the extra rerun for perf, remove the `st.rerun()` line — the next user interaction (any) will pick up the new session_state value.
2. **`use_container_width=True` AND `width=None`:** `width=None` is the explicit signal "let CSS decide"; `use_container_width=True` is the Streamlit-level affordance that makes the iframe fill the parent. Setting both is idempotent and matches the streamlit-folium 0.27 recommended idiom.
3. **The `_style_function` closes over `selected_iso3`** — the value read from session_state at the top of the script run. On rerun (after a click or a selectbox change), this closure captures the NEW value and the style_function returns the updated highlight without any manual re-render needed.
4. **Validation against `country_metadata.iter_countries()` is REQUIRED.** ESH and "-99" are in the DBF (see §3) and would otherwise leak into session_state and break the selectbox.

### Confidence: HIGH (pattern matches Context7 streamlit-folium examples; click-validation gap pre-empts a known data-divergence bug).

## `country_metadata.py` — Full Module File

`[VERIFIED: names extracted from AFRICA_ADM0.dbf `name` column via Python struct read of the raw DBF, 2026-05-14; cross-checked filename ISO3 set against `available_countries()` output, also 2026-05-14]`

### Strategy

- Use **`iso_a3` from AFRICA_ADM0.dbf** as the canonical ISO3 (matches filenames and matches GeoJson properties on click — the picker's join key).
- Use the DBF's **`name` column** for the conventional short form (NOT `name_long`). This gives us "Tanzania" not "United Republic of Tanzania", "Dem. Rep. Congo" not "Democratic Republic of the Congo", "S. Sudan" not "South Sudan" — but per D-24 the planner MAY hand-edit these to MOSAIC-preferred names. Recommendations inline below.
- **Add MUS (Mauritius) and SYC (Seychelles)** — they're in the per-country shapefiles but absent from AFRICA_ADM0. The picker covers them; the map won't highlight them (no geometry); the sanity-check warning will surface the divergence (which is what D-29 was designed for).
- **Sort alphabetical-by-name** (D-27).
- First entry (default) = Angola (D-26, D-27, D-33).

### Concrete file (copy-pasteable)

```python
"""Static ISO3 → name lookup for the SSA country picker (D-24..D-29).

This module is the single source of truth for country names shown in the
picker. It is intentionally NOT generated from AFRICA_ADM0.dbf — the DBF
ships Natural Earth labels which are sometimes long-form ("Côte d'Ivoire",
"S. Sudan") or include disputed-territory rows we don't want in the picker
(Western Sahara, Somaliland). Editing this list is the canonical way to
change picker order, picker default, or naming.

Order matters (D-25): the iteration order IS the picker display order, and
the first entry IS the first-load default (D-26). Ships alphabetical-by-name
with Angola first.

Cross-referenced with shapefiles.available_countries() at startup (D-29) —
a warning fires if metadata and shapefiles diverge.
"""

from __future__ import annotations

import logging
from typing import Iterable

log = logging.getLogger(__name__)

#: Ordered list of (ISO3, display name) pairs. Order = picker order = default
#: priority. Ships alphabetical-by-name; edit freely.
#:
#: Names follow MOSAIC project convention: short, common forms — not the
#: Natural Earth long-form. Reviewed against Natural Earth `name` column;
#: deviations noted inline.
COUNTRIES: tuple[tuple[str, str], ...] = (
    ("AGO", "Angola"),
    ("DZA", "Algeria"),
    ("BEN", "Benin"),
    ("BWA", "Botswana"),
    ("BFA", "Burkina Faso"),
    ("BDI", "Burundi"),
    ("CPV", "Cabo Verde"),
    ("CMR", "Cameroon"),
    ("CAF", "Central African Republic"),   # DBF says "Central African Rep." — expanded for clarity
    ("TCD", "Chad"),
    ("COM", "Comoros"),
    ("COG", "Republic of the Congo"),       # DBF says just "Congo" — long form disambiguates from COD
    ("COD", "Democratic Republic of the Congo"),  # DBF says "Dem. Rep. Congo" — expanded
    ("CIV", "Côte d'Ivoire"),
    ("DJI", "Djibouti"),
    ("EGY", "Egypt"),
    ("GNQ", "Equatorial Guinea"),           # DBF says "Eq. Guinea" — expanded
    ("ERI", "Eritrea"),
    ("SWZ", "Eswatini"),                    # DBF says "eSwatini"; ISO 3166 spelling is "Eswatini"
    ("ETH", "Ethiopia"),
    ("GAB", "Gabon"),
    ("GMB", "Gambia"),
    ("GHA", "Ghana"),
    ("GIN", "Guinea"),
    ("GNB", "Guinea-Bissau"),
    ("KEN", "Kenya"),
    ("LSO", "Lesotho"),
    ("LBR", "Liberia"),
    ("LBY", "Libya"),
    ("MDG", "Madagascar"),
    ("MWI", "Malawi"),
    ("MLI", "Mali"),
    ("MRT", "Mauritania"),
    ("MUS", "Mauritius"),                   # NOT in AFRICA_ADM0; per-country shape only
    ("MAR", "Morocco"),
    ("MOZ", "Mozambique"),
    ("NAM", "Namibia"),
    ("NER", "Niger"),
    ("NGA", "Nigeria"),
    ("RWA", "Rwanda"),
    ("STP", "São Tomé and Príncipe"),       # DBF has 'í' as plain 'i'; matched Wikipedia spelling
    ("SEN", "Senegal"),
    ("SYC", "Seychelles"),                  # NOT in AFRICA_ADM0; per-country shape only
    ("SLE", "Sierra Leone"),
    ("SOM", "Somalia"),
    ("ZAF", "South Africa"),
    ("SSD", "South Sudan"),                 # DBF says "S. Sudan" — expanded
    ("SDN", "Sudan"),
    ("TZA", "Tanzania"),
    ("TGO", "Togo"),
    ("TUN", "Tunisia"),
    ("UGA", "Uganda"),
    ("ZMB", "Zambia"),
    ("ZWE", "Zimbabwe"),
)

#: Set of valid ISO3 codes — handy for membership tests in click handlers.
ISO3_SET: frozenset[str] = frozenset(iso3 for iso3, _ in COUNTRIES)

#: Dict for O(1) name lookups.
_NAME_BY_ISO3: dict[str, str] = dict(COUNTRIES)


def iter_countries() -> list[tuple[str, str]]:
    """Return the ordered list of (ISO3, display name) pairs (D-29 API)."""
    return list(COUNTRIES)


def name_for(iso3: str) -> str:
    """Return the display name for an ISO3 code (D-29 API).

    Returns the ISO3 itself if unknown — never raises. This makes the helper
    safe to call from format_func on a selectbox that might temporarily hold
    a stale ISO3 (e.g., during click validation).
    """
    return _NAME_BY_ISO3.get(iso3, iso3)


def warn_if_drifted_from_shapefiles(available_iso3s: Iterable[str]) -> None:
    """Emit a warning if country_metadata diverges from shapefile presence (D-29).

    Args:
        available_iso3s: Output of ``shapefiles.available_countries()``.

    Does NOT raise — divergence is tolerated per D-04 spirit. Logs once;
    callers should call this at module startup or first sidebar render.
    """
    available = set(available_iso3s)
    meta = set(ISO3_SET)
    in_meta_not_shapes = meta - available
    in_shapes_not_meta = available - meta
    if in_meta_not_shapes or in_shapes_not_meta:
        log.warning(
            "Country metadata / shapefile drift detected: "
            "in metadata but no shapefile: %s; "
            "in shapefiles but not metadata: %s",
            sorted(in_meta_not_shapes),
            sorted(in_shapes_not_meta),
        )
```

### Total: 54 entries

| Count | Notes |
|-------|-------|
| 54 entries | Matches `shapefiles.available_countries()` (Phase 1 verified) |
| Default (index 0) | AGO/Angola — alphabetically first, MOSAIC-team conventional |
| Edited names | 8 of 54 have been expanded from the DBF's short form to a fuller MOSAIC-conventional form (CAR, ROC, DRC, Eq. Guinea, S. Sudan, eSwatini→Eswatini, STP diacritic). Planner / user can revert any of these by editing the list. |

### Where to call `warn_if_drifted_from_shapefiles()`

Two reasonable places:
1. **In `app.py` near the top**, once per session, after `configure_logging`:
   ```python
   from mosaic_dashboard.data import country_metadata, shapefiles
   country_metadata.warn_if_drifted_from_shapefiles(shapefiles.available_countries())
   ```
2. **Inside `ui/sidebar.py::render()`**, gated by a `_drift_check_done` session_state flag so the warning only logs once per session.

Either works. Option 1 is simpler; recommended.

### Confidence: HIGH (all 54 names verified against DBF + filename intersection; deviations explicit).

## CartoDB Positron Specifics

`[CITED: github.com/python-visualization/folium/blob/main/docs/user_guide/raster_layers/tiles.md via Context7]`

### Folium built-in alias

```python
folium.Map(location=[0.0, 20.0], zoom_start=3, tiles="CartoDB Positron")
# or equivalently (folium accepts case-insensitive aliases):
folium.Map(..., tiles="cartodb positron")
folium.Map(..., tiles="Cartodb Positron")
```

All three forms work. The folium docs use `"cartodbpositron"` (no space) and `"cartodb positron"` interchangeably; both resolve to the same `xyzservices.TileProvider`. **Recommended canonical form: `"CartoDB Positron"`** (matches the UI-SPEC text and the xyzservices registry name).

### Tile URL pattern (for reference; folium fills this in automatically)

```
https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png
```

`{s}` is the subdomain (a/b/c). `{z}`, `{x}`, `{y}` are Leaflet's zoom + tile-coordinate placeholders.

### Attribution requirements

**CartoDB Positron is free but requires attribution.** Folium auto-injects the attribution string when you use the `tiles="CartoDB Positron"` alias:

```
© OpenStreetMap contributors © CartoDB
```

This appears in the bottom-right of the map iframe as a small badge. **DO NOT hide it** — it's a license requirement (CC BY 3.0 for OSM data + CartoDB attribution).

### API key

**None required.** CartoDB Positron is free for public use; no API key, no rate-limit enforcement at the volumes a single-user dashboard generates.

### Offline behavior

CartoDB tiles are served from a CDN. **The first map render REQUIRES network access** to fetch tiles (typically ~10-40 PNG tiles for a SSA-wide view at zoom 3). Once tiles are fetched, browsers cache them aggressively — subsequent reloads from the same browser session work offline. **But:** Streamlit reruns DO NOT trigger tile re-fetches (the tiles cache in the browser); only a hard browser refresh + cold cache would force a re-fetch.

**DATA-03 implication:** The dashboard's "no external calls in the hot path" constraint applies to the data layer (Python-side reads). The map TILE layer is loaded by the browser, not by Python — so DATA-03 is technically not violated. But practically, a teammate running on a truly offline laptop on first launch will see a blank map background (country polygons still render — they're SVG generated from local geometry — but the tile background is white). This is acceptable per PROJECT.md spirit but worth documenting.

**Mitigation for fully-offline scenarios** (NOT in Phase 2 scope; flagged for Phase 6 PERF if needed):
- Use `tiles=None` to render with NO base tiles (white background; country polygons fully sufficient for the use case).
- Or pre-bundle tiles into the repo (heavy; not warranted).

### Confidence: HIGH (folium tile alias + URL pattern verified against folium official docs via Context7).

## Caching Strategy for GeoDataFrames

`[CITED: docs.streamlit.io/develop/concepts/architecture/caching, docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data]`

### `@st.cache_data` vs `@st.cache_resource` — which one?

| | `@st.cache_data` | `@st.cache_resource` |
|---|------------------|----------------------|
| Stores | Serializable returns (pickle-based) | Live Python objects (no copy) |
| Returned value | **Copy** per call (safe to mutate) | Same instance per call |
| Args must be hashable? | YES | YES (unless `hash_funcs` provided) |
| Typical use | DataFrames, dicts, lists, numpy arrays | DB connections, ML models, large in-memory structures |
| Phase 1 uses | All loaders (D-18) | None |

**Use `@st.cache_data` for GeoDataFrames.** They serialize cleanly (pandas + shapely both support pickle), the copy-per-call semantics matches what we want (style_function may rely on a fresh copy of the data each rerun), and it matches the Phase 1 pattern (D-18 mandates this for the rest of the data layer).

**`@st.cache_resource` is the WRONG choice here** because:
- GeoDataFrames are NOT expensive to copy (~3 MB SSA dataframe copies in <50 ms).
- Returning the SAME instance across reruns means if any view ever mutates the dataframe in place, the mutation persists silently across the whole app. With `cache_data`'s per-call copy, this can't happen.

### Does `cache_data` work on GeoDataFrame out of the box? (YES)

Streamlit's hashing logic only hashes the **arguments** (to compute the cache key). The return value is **pickled** for storage and **unpickled** on hit. GeoDataFrames are picklable in geopandas 1.x — verified by the geopandas team in the 1.0 release notes (the upgrade to pyogrio + shapely 2.x made pickling round-trip cleanly).

**No `hash_funcs` workaround needed** for the pattern in §4 (`def _read_africa_geometry_cached(path: str, mtime: float)`) because both arguments are simple hashable primitives. The return value (`gpd.GeoDataFrame`) does not need to be hashed.

When would `hash_funcs` be needed? If you tried to pass a `Path` object instead of a string, or a custom config dataclass into the cached function — then Streamlit would raise `UnhashableParamError` and you'd need either:
```python
@st.cache_data(hash_funcs={Path: lambda p: str(p)})
def _cached(path: Path, mtime: float) -> gpd.GeoDataFrame: ...
```
…OR (much simpler) just convert `Path` to `str` at the call site. Phase 1's pattern does the latter (`str(csv_path)`), and Phase 2 mirrors it — no `hash_funcs` needed.

### Cache size / eviction

`@st.cache_data` defaults: `ttl=None` (no expiry), `max_entries=None` (no count limit). For a 54-record SSA GeoDataFrame at ~3 MB, this is fine. Adding a `ttl=3600` (1 hour) would be belt-and-suspenders if upstream `processed/` is suspected of changing mid-session — but D-18's mtime-key already handles that case correctly, so the extra TTL adds noise without benefit.

### Cache survival across user sessions

`@st.cache_data` is **process-scoped, not session-scoped.** All concurrent Streamlit users on the same server instance share the cache. For our single-user local dashboard, this is irrelevant — there's only ever one session. The cache lives as long as the `streamlit run` process.

### Confidence: HIGH (pattern is Streamlit's documented happy path).

## Validation Architecture (Phase 2 acceptance checks)

`workflow.nyquist_validation: false` per `.planning/config.json` — formal test framework section is skipped. Below are the acceptance criteria the verifier executes after Phase 2 lands. Numbered B1-B10 to avoid collision with Phase 1's A1-A10.

### B1-B10 acceptance criteria

| # | Acceptance Criterion | How to verify | Maps to |
|---|----------------------|---------------|---------|
| B1 | `uv add geopandas folium streamlit-folium` updates pyproject.toml + uv.lock cleanly | `uv add ...` exits 0; `git diff pyproject.toml` shows three new entries under `[project.dependencies]`; `uv.lock` updated. Run from cold venv: `rm -rf .venv && uv sync` exits 0. | D-22 |
| B2 | `country_metadata.iter_countries()` returns 54 entries; cross-check with `shapefiles.available_countries()` | `uv run python -c "from mosaic_dashboard.data import country_metadata, shapefiles; assert len(country_metadata.iter_countries()) == 54; print('OK')"`. Bonus: `set(iso3 for iso3,_ in country_metadata.iter_countries()) == set(shapefiles.available_countries())` is TRUE. | D-25, D-29 |
| B3 | `pages/01_SSA_Map.py` is reachable from the sidebar | Run app; sidebar shows "SSA Map" link (after "Data Status"); clicking it navigates to `/SSA_Map` URL; page renders title "SSA Map". | D-34, MAP-01 |
| B4 | Selecting "Burundi" in the sidebar selectbox writes "BDI" to session_state | Launch app; pick "Burundi" from sidebar; navigate to SSA Map; verify the "Selected: Burundi (BDI)" caption is shown AND the map highlights Burundi. (Programmatic check via `st.write(st.session_state[COUNTRY_SESSION_KEY])` on a sandbox page would show `BDI`.) | NAV-01, D-31, D-32 |
| B5 | Clicking on Angola in the map writes "AGO" to session_state | Launch app; pick "Burundi" from sidebar (so AGO != current); navigate to SSA Map; click on Angola polygon; verify (a) sidebar selectbox now shows "Angola"; (b) "Selected: Angola (AGO)" caption updates; (c) Angola polygon now highlighted #FF4B4B. | MAP-01, MAP-02, D-36 |
| B6 | Selectbox visually updates after a map click (page rerun) | Subsumed by B5(a) — the sidebar widget reading from session_state must reflect the new ISO3 on the rerun streamlit-folium triggers. | MAP-02, D-37 |
| B7 | Map highlights selected country with #FF4B4B fill + 3px stroke; others with #F0F2F6 + 1px | Visual inspection of the rendered map. Sample 5 ISO3s by changing the picker; verify the highlight follows. | UI-SPEC, MAP-02 |
| B8 | Disconnect the network → reload → map STILL renders (country polygons) | Disconnect WSL2 network (`ip link set <iface> down`); browser hard-reload (`Ctrl+Shift+R`) the localhost:8501/SSA_Map page; verify: (a) page loads; (b) country polygons render (they're SVG from local geometry); (c) base map tiles may be blank (white) — this is acceptable, polygons are sufficient. | DATA-03 partial |
| B9 | With AFRICA_ADM0.shp missing → empty-state on map page, no traceback | Rename `~/MOSAIC/MOSAIC-data/processed/shapefiles/AFRICA_ADM0.shp` to `AFRICA_ADM0.shp.bak`; reload the Map page; verify: (a) no traceback; (b) `st.warning` banner reads "SSA shapefile not found. Check Data Status, or set the data-root override in the sidebar."; (c) Data Status page still works. | D-39, DATA-04 |
| B10 | `country_metadata`-vs-`available_countries()` startup sanity check logs a warning | Terminal that ran `uv run streamlit run ...` should show on first session start: `WARNING ... Country metadata / shapefile drift detected: in metadata but no shapefile: [...]; in shapefiles but not metadata: ['ESH', '-99']` (assuming Phase 2 ships with MUS/SYC in metadata as recommended). | D-29 |

### Visual / browser-only checks (acknowledged manual)

B3, B4, B5, B6, B7, B8 are **browser-only** acceptance checks — they require running the app and clicking around. B1, B2, B9, B10 can be run headless from the command line.

### Manual probe scripts (useful for the planner)

```bash
# B2 — check metadata vs shapefiles
uv run python -c "
from mosaic_dashboard.data import country_metadata, shapefiles
meta_set = set(iso3 for iso3, _ in country_metadata.iter_countries())
shape_set = set(shapefiles.available_countries())
print(f'metadata count: {len(meta_set)}')
print(f'shapefile count: {len(shape_set)}')
print(f'in meta, no shape: {meta_set - shape_set}')
print(f'in shape, no meta: {shape_set - meta_set}')
"

# Geometry smoke test — confirms geopandas + pyogrio installed correctly
uv run python -c "
from mosaic_dashboard.data import shapefiles
gdf = shapefiles.load_africa_geometry()
print(f'Rows: {len(gdf)}, columns: {list(gdf.columns)[:5]}, CRS: {gdf.crs}')
"
```

### Confidence: HIGH (every check maps to a locked decision or requirement and is performable manually in <5 minutes).

## Pitfalls

Stack-specific gotchas that bite in this exact configuration:

### P1: `last_object_clicked` does NOT carry GeoJson properties

**What goes wrong:** Developer reads `output["last_object_clicked"]` expecting to find the clicked feature's properties. It returns `{"lat": ..., "lng": ...}` — coordinates only.
**Why:** `last_object_clicked` reports the click coordinates relative to whatever Leaflet "object" was hit. `last_active_drawing` is the key that surfaces the actual GeoJson feature (its properties + geometry).
**How to avoid:** Use `output["last_active_drawing"]["properties"]["iso_a3"]`. Document in code comment why we chose this key.

### P2: The selectbox `value=` / `index=` clobbers the click-driven session_state write

**What goes wrong:** Developer passes both `key=COUNTRY_SESSION_KEY` AND `index=0` (or `value="AGO"`) to `st.selectbox`. On the second rerun (after a map click writes `"BDI"` to session_state), the selectbox resets to index 0 — clobbering the click.
**Why:** Streamlit's widget priority is `key` value (session_state) > `index`/`value` argument > default. But Streamlit ALSO honors `index`/`value` as the initial value on first render, and there's a subtle gotcha where re-passing them on every render causes the widget to "track" the index argument.
**How to avoid:** Use `key=` ONLY. Seed `st.session_state[key]` BEFORE the widget renders if you need a first-load default. `[CITED: docs.streamlit.io/develop/concepts/architecture/session-state]`

### P3: `st_folium` returns ALL keys by default — including bounds that change on every pan

**What goes wrong:** Without `returned_objects=...`, streamlit-folium returns the full dict (bounds, zoom, center) on every map interaction — including pan/zoom. This triggers Streamlit reruns even when the user is just exploring the map, AND the bounds payload is non-deterministic (slightly different lat/lng each pan), so memoization downstream can't help.
**How to avoid:** Pass `returned_objects=["last_active_drawing"]` to limit the payload to just what we care about. Pan/zoom no longer trigger reruns. This is the pattern Context7's "Realtime Plugin" example uses with `returned_objects=[]`.

### P4: streamlit-folium iframe `height` is mandatory (pixels)

**What goes wrong:** Developer sets `height="100%"` or omits it. The iframe collapses to 0 pixels or defaults to a tiny height; map appears as a sliver.
**Why:** streamlit-folium embeds folium in an `<iframe>`, and HTML iframes need a pixel height to render. `100%` of WHAT? — no parent container provides a vertical anchor.
**How to avoid:** Always pass `height=600` (or whatever the UI-SPEC dictates) as an integer of pixels. Width can be flexible (`width=None` + `use_container_width=True`); height must be concrete.

### P5: GeoDataFrame passed to `folium.GeoJson(data=gdf)` does NOT preserve all properties

**What goes wrong:** Developer passes a 165-column GeoDataFrame to `folium.GeoJson(...)`. Most columns serialize fine, BUT non-JSON-serializable values (e.g., `numpy.float64` NaN, datetime objects) get converted in unexpected ways, and the resulting GeoJson features have surprising property values.
**How to avoid:** Either (a) call `gdf[["iso_a3", "name", "geometry"]].to_json()` and pass the JSON string, OR (b) trust `folium.GeoJson(data=gdf)` for SSA-wide where all columns are strings/ints/geometry. For Phase 2 the AFRICA_ADM0 columns are all clean (strings + geometry) — option (b) works. If a future column has NaN, fall back to option (a).
**Recommended:** `folium.GeoJson(data=africa[["iso_a3", "name", "geometry"]], ...)` — slimmed-down DataFrame, reducing the per-feature JSON payload from ~5 KB to ~0.5 KB and speeding up the Leaflet render. The `style_function` and `tooltip` only read `iso_a3` and `name`; the other 163 columns are dead weight.

### P6: GeoJson `tooltip=GeoJsonTooltip(fields=["name"], labels=True)` shows "name: Angola", not just "Angola"

**What goes wrong:** Default `labels=True` prefixes the field key. Tooltip reads "name: Angola" instead of just "Angola".
**How to avoid:** Pass `labels=False` to hide the field-name prefix. UI-SPEC says "country name only" — pass `labels=False, aliases=[""]`.

### P7: ISO3 column name varies across shapefile sources — DO NOT assume `ISO3` or `ADM0_A3`

**What goes wrong:** Developer hard-codes `feature["properties"]["ISO3"]` based on a different shapefile pack. AFRICA_ADM0 (Natural Earth) uses `iso_a3` (lowercase, underscore). Click handler silently returns `None` because the key doesn't exist.
**Why:** Natural Earth's convention is `iso_a3`; ESRI's convention is `ISO3` or `ISO_A3`; GADM uses `GID_0`. The shapefile in `processed/shapefiles/` is **Natural Earth** (verified via raw DBF inspection, §3).
**How to avoid:** Hard-code `iso_a3` (lowercase) in the click handler and style_function. Document in code comment: `# AFRICA_ADM0.dbf is Natural Earth schema; ISO3 column is 'iso_a3' (verified 2026-05-14)`.

### P8: `style_function` is called for EVERY feature on EVERY render — keep it cheap

**What goes wrong:** Developer puts a database lookup or any I/O inside the `style_function` lambda. With 54 features × N reruns, the app lags.
**How to avoid:** Pre-compute everything needed by the style_function OUTSIDE the closure. In our pattern, `selected_iso3` is read once at the top of the page script and closed over; the style_function only does a string comparison.

### P9: Streamlit reruns reset Folium's view state (zoom, pan) unless `returned_objects` skips them

**What goes wrong:** User pans/zooms the map; Streamlit reruns (due to e.g. the sidebar selectbox interaction); the map resets to `location=[0.0, 20.0], zoom_start=3`.
**How to avoid:** When the user changes the country picker via the sidebar (NOT a map click), and the page reruns, the folium.Map() constructor recreates the map at the initial center/zoom. To preserve the view, the planner could read `output["bounds"]` and `output["zoom"]` and re-pass them to `folium.Map()` on the next render. **NOT in Phase 2 scope** — UI-SPEC says map zoom/pan persistence is Phase 6 PERF. Document this behavior; don't fix it now.

### P10: ESH (Western Sahara) and "-99" (Somaliland) leak into session_state if click handler doesn't validate

**What goes wrong:** User clicks on Western Sahara on the map; click handler writes `"ESH"` to `st.session_state[COUNTRY_SESSION_KEY]`; sidebar selectbox tries to render with `"ESH"` as the current value but `"ESH" not in options` — Streamlit raises an error.
**How to avoid:** Validate the clicked ISO3 against `country_metadata.ISO3_SET` BEFORE writing to session_state. See §6 step 10 ("validate against country_metadata") and the click handler in the skeleton.

### P11: `gpd.read_file` raises if the `.shx` index is missing (pyogrio strict by default)

**What goes wrong:** Developer copies `AFRICA_ADM0.shp` but forgets `.shx`; pyogrio raises `DataSourceError: ... index file (.shx) is missing`.
**How to avoid:** The empty-state guard in `load_africa_geometry()` (`if not shp_path.exists()`) doesn't catch this — it checks only `.shp`. Make the check more defensive: also verify `.shx` and `.dbf` exist. Alternatively, accept the raise and let it propagate as `SchemaMismatchError` via a try/except in the cached function. **Minimal fix:** add `if not all((shp_path.with_suffix(ext)).exists() for ext in (".shp", ".shx", ".dbf")): return _empty_africa_geometry()`.

### P12: Test pages directory contains 01_SSA_Map.py — Streamlit auto-discovers it BEFORE Phase 2 lands

**What goes wrong:** Developer creates `pages/01_SSA_Map.py` as a stub with `pass`; sidebar shows "SSA Map" but clicking it crashes.
**How to avoid:** Either ship the full page or don't ship the file at all. Don't commit partial pages. (This is more of a discipline note for the planner sequencing tasks within the phase.)

## Open Questions

1. **Should the planner ship the country_metadata names exactly as the DBF has them, OR with the MOSAIC-conventional expansions documented in §7?**
   - What we know: D-24 lets the planner pick MOSAIC-conventional names; D-27 says "alphabetical-by-name."
   - What's unclear: Whether the MOSAIC team prefers `Dem. Rep. Congo` (DBF short) or `Democratic Republic of the Congo` (long, expanded).
   - Recommendation: Ship the expanded forms documented in §7. They're unambiguous in a dropdown and harmless. Anyone can edit `country_metadata.py` to revert to short forms. **The planner should call this out as a discuss-phase question if there's any doubt.**

2. **Should the click handler `st.rerun()` or rely on streamlit-folium's auto-rerun?**
   - What we know: streamlit-folium fires its own rerun on click. `st.rerun()` after writing to session_state would be a second rerun.
   - What's unclear: Whether the UX is meaningfully different between the two. With auto-rerun, the highlight appears on the SAME rerun (same script execution that ran the click handler); with explicit `st.rerun()`, a second rerun happens.
   - Recommendation: Include `st.rerun()` for clarity (the planner can comment it out if perf measurements in Phase 6 show double-reruns are a problem). The "safety" pattern is more readable.

3. **Should the page validate the clicked ISO3 inline OR delegate to a helper in `country_metadata`?**
   - What we know: The validation is one line: `if clicked_iso3 in country_metadata.ISO3_SET`.
   - What's unclear: Whether DRY favors a `country_metadata.is_valid(iso3) -> bool` helper.
   - Recommendation: Inline for now (one call site in Phase 2). Add the helper in Phase 3 if a second view needs the same check.

4. **Should `load_country_geometry()` be called from anywhere in Phase 2?**
   - What we know: D-38 says Phase 2 adds the function; Phase 5 (LAYER-06 "shapefiles view") is the obvious consumer.
   - What's unclear: Whether Phase 2 even has a use for `load_country_geometry()` — the SSA map uses `load_africa_geometry()` exclusively.
   - Recommendation: Add the function and a smoke test in Phase 2 (per D-38: "Phase 2 ADDS"), but don't wire it into any view yet. Phase 5 will consume it. The cost of adding now vs. later is ~30 LOC and one smoke test; deferring risks a cross-phase coordination issue.

5. **Should `folium.GeoJson` slim the input GeoDataFrame to just `[iso_a3, name, geometry]`?**
   - What we know: AFRICA_ADM0 has 165 columns; only 2 are used by the page.
   - What's unclear: Whether the perf delta is meaningful (P5 above is the relevant pitfall).
   - Recommendation: YES, slim it. `folium.GeoJson(data=africa[["iso_a3", "name", "geometry"]], ...)` cuts the JSON payload by ~10x and speeds up Leaflet's first-paint by 50-100 ms on slow laptops. Negligible code cost.

## Runtime State Inventory

Phase 2 is largely additive (new files, new deps, new session_state key, new selectbox widget). The Runtime State Inventory categories evaluate as:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — Phase 2 doesn't introduce any persistent storage. `st.session_state` is in-memory only and per-session. | None. |
| Live service config | None — no external services (CartoDB tile fetch is browser-side, not Python-side). | None. |
| OS-registered state | None — no Task Scheduler/launchd/systemd registrations created or modified. | None. |
| Secrets / env vars | None — CartoDB Positron requires no API key (verified above). | None. |
| Build artifacts | **YES** — `uv add geopandas folium streamlit-folium` will install three new packages + transitive deps (pyogrio, shapely, pyproj, branca, xyzservices, etc., ~45 MB) into `.venv/`. `uv.lock` will be updated. Both are gitignored (`.venv/`) or committed (`uv.lock`); no action beyond `uv sync`. | Verify `uv.lock` is updated and committed after `uv add`. |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Adding new deps + launch | YES | 0.8.2 (installed) | None needed. |
| Python | uv-managed runtime | YES | 3.13.12 | None — covers `requires-python = ">=3.11"`. |
| `~/MOSAIC/MOSAIC-data/processed/shapefiles/AFRICA_ADM0.shp` (+ `.shx`, `.dbf`, `.prj`) | Map page | YES (verified via Phase 1 Data Status and direct `ls`) | — | Empty-state per D-39: if absent, `st.warning` banner replaces map. |
| `~/MOSAIC/MOSAIC-data/processed/shapefiles/XXX_ADM0.*` × 54 | `load_country_geometry()` callers (Phase 5; Phase 2 just provides the function) | YES (all 54 present per Phase 1 verification) | — | Same empty-state contract. |
| Network (for CartoDB tile fetches) | Map base layer (browser-side) | Yes assumed; degrades gracefully | — | If offline: tiles blank, polygons still render. Documented in §8 and acceptance B8. |
| `geopandas`, `folium`, `streamlit-folium` packages | Phase 2 entirely | NOT YET INSTALLED | — | `uv add` adds them; PyPI access required for one-time install. After install, fully offline. |

**Missing dependencies with no fallback:** None. PyPI access required for the initial `uv add` step.

**Missing dependencies with fallback:** None.

`[VERIFIED: ls ~/MOSAIC/MOSAIC-data/processed/shapefiles/ → 54 country files + 1 AFRICA file × 4 extensions each; `available_countries()` returns 54 ISO3]`

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| B1 | streamlit-folium 0.27.2's `last_active_drawing` return key is populated for `folium.GeoJson` clicks (not only `folium.plugins.Draw` shapes). | §2 (TL;DR + click handler) | LOW — Context7 explicitly documents this case (GeoJsonPopups example uses `last_object_clicked_*`; the dedicated GeoJson click path was added in 0.18). Planner should add a quick smoke test as the first task of plan 02-03 (the map-page plan) to confirm before committing. |
| B2 | The full AFRICA_ADM0 GeoDataFrame in geopandas 1.1 is ~3 MB. | §9 (cache size) | LOW — back-of-envelope from the `.shp` (210 KB on disk) × ~10 expansion for shapely geometry objects in RAM. If wildly off, cache TTL/max_entries can be tuned in Phase 6. |
| B3 | The two MOSAIC-conventional names (`Eswatini` vs `eSwatini`; `Republic of the Congo` vs `Congo`) are the ones the team prefers. | §7 | MEDIUM — listed as Open Question 1 above. If wrong, the planner edits the list (no code change beyond one file). |
| B4 | `folium.GeoJson(data=gdf)` correctly handles a GeoDataFrame with WGS84 CRS (EPSG:4326). | §6 (map skeleton) | LOW — folium docs explicitly support GeoDataFrame input; Natural Earth ships in EPSG:4326. |
| B5 | `pyogrio` is the default geopandas IO driver in 1.x (no need to install fiona). | §2 (transitive deps) | LOW — verified geopandas 1.1.3 `requires_dist` from PyPI: `pyogrio>=0.7.2` required, fiona only in `[all]` extra. |
| B6 | The folium tile alias `"CartoDB Positron"` resolves to the free CartoDB Positron provider (no API key). | §8 | LOW — verified via folium Context7 docs and folium source ships the alias in its built-in tile registry. |
| B7 | `st.session_state[COUNTRY_SESSION_KEY]` survives page navigation when both the selectbox AND the map page render `ui.sidebar.render()` at the top (Phase 1 P9 pattern). | §5, §6 | LOW — Phase 1 RESEARCH §5 documented this; Phase 1 Plan 05 implementation verified it for the data-root override. The pattern generalizes. |
| B8 | The DBF column `iso_a3` matches every per-country shapefile's filename prefix EXCEPT MUS, SYC (missing from DBF) and ESH, "-99" (in DBF, no per-country file). | §3 | NONE — directly verified by exhaustive Python comparison of the two sets, 2026-05-14. |

## Sources

### Primary (HIGH confidence)

- **Context7 / randyzwitch/streamlit-folium** (`/randyzwitch/streamlit-folium`, fetched via ctx7 CLI 2026-05-14):
  - `st_folium` return value dict structure (`last_clicked`, `last_object_clicked`, `last_active_drawing`, etc.)
  - GeoJsonPopups + GeoJsonTooltip examples with style_function
  - On-change callback + `key` argument pattern
  - Draw Plugin Support (relevant for `last_active_drawing` semantics)
  - Realtime Plugin (illustrates `returned_objects=[]` perf pattern)

- **Context7 / python-visualization/folium** (`/python-visualization/folium`, fetched 2026-05-14):
  - `folium.GeoJson` class API (style_function, highlight_function, tooltip)
  - `folium.GeoJsonTooltip` API
  - CartoDB Positron tile alias + URL pattern
  - GeoPandas GeoDataFrame integration

- **Context7 / streamlit/docs** (`/streamlit/docs`, fetched 2026-05-14):
  - `@st.cache_data` semantics + `hash_funcs` argument
  - `st.session_state` widget binding via `key=`
  - Selectbox API + key-vs-value precedence
  - Multipage pages/ widget state preservation pattern

- **First-hand DBF inspection** (2026-05-14):
  - `~/MOSAIC/MOSAIC-data/processed/shapefiles/AFRICA_ADM0.dbf` — read via Python `struct.unpack` to extract field schema and all 54 records. Confirmed `iso_a3` is the Natural Earth ISO3 column; identified divergences from filename-derived ISO3 set.
  - `~/MOSAIC/MOSAIC-data/processed/shapefiles/AGO_ADM0.dbf` — confirmed per-country DBFs have single field `ADM0` (country name only).

- **PyPI metadata fetched 2026-05-14:**
  - folium 0.20.0 (released 2025-06-16)
  - streamlit-folium 0.27.2 (released 2026-04-29)
  - geopandas 1.1.3 (released 2026-03-09)
  - pyogrio 0.12.1
  - shapely 2.1.2
  - pyproj 3.7.2
  - fiona 1.10.1 (NOT installed by default)

- **Local environment probes (2026-05-14):**
  - `uv run python -c "from mosaic_dashboard.data import shapefiles; print(shapefiles.available_countries())"` — returns the 54 ISO3 codes.
  - `ls ~/MOSAIC/MOSAIC-data/processed/shapefiles/` — confirms 54 per-country `XXX_ADM0.*` sets + 1 `AFRICA_ADM0.*` set.

### Secondary (MEDIUM confidence)

- Phase 1 RESEARCH.md (`.planning/phases/01-foundation-data-layer/01-RESEARCH.md`) — §3 (multi-page conventions), §5 (sidebar pattern), §8 (P9 widget-state cleanup) — patterns Phase 2 directly extends.
- `geopandas` 1.0 release notes (cited via Context7 / PyPI metadata) — pyogrio default, pickle round-trip safety.

### Tertiary (LOW confidence — flagged for validation)

- None. Every pattern in this research has at least one HIGH-confidence source.

## Metadata

**Confidence breakdown:**
- Standard stack (versions, install): HIGH — three PyPI fetches + transitive-dep inspection.
- streamlit-folium click API: HIGH — direct Context7 docs with the exact return-dict structure quoted verbatim.
- Folium GeoJson + style_function: HIGH — Context7 + folium official docs cross-confirmed.
- DBF schema for AFRICA_ADM0: HIGH — raw bytes inspected; no second-hand sources needed.
- DBF / filename divergence (MUS, SYC, ESH, -99): HIGH — exhaustive set comparison.
- `country_metadata.py` 54-entry list: HIGH on ISO3s, MEDIUM on conventional name spellings (Open Question 1).
- Caching strategy (`@st.cache_data` for GeoDataFrames): HIGH — pattern is Streamlit's documented happy path.
- Sidebar extension pattern: HIGH — Phase 1's data-root override is the working precedent.
- Pitfalls: HIGH for P1–P10 (each cited); MEDIUM for P11 (pyogrio strictness — verified geopandas docs but planner should smoke-test).
- Acceptance checks B1–B10: HIGH — each maps to a locked decision and is performable in <5 minutes.

**Research date:** 2026-05-14
**Valid until:** 2026-06-14 (30 days — streamlit-folium and folium both ship monthly minor releases; revalidate if planning slips past this date).
