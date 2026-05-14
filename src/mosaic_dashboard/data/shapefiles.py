"""Shapefile presence/metadata + geometry loaders.

Phase 1 surface: presence/mtime metadata only -- no shapefile parsing. Phase 2
adds geometry loaders that wrap `geopandas.read_file(...)` and follow the same
public/private cached pattern the rest of the data layer uses (D-18). The
Phase-1 functions retain their Path-only semantics byte-for-byte (D-20, D-38,
D-40) -- the Data Status page still calls them and depends on the metadata
DataFrame shape.

Per D-19 (CONTEXT.md), the heavy geo-stack dependency (geopandas + its
underlying drivers pyogrio, shapely, pyproj) lands in Phase 2. For the Data
Status page (Plan 05), Path-only file enumeration is sufficient; the geometry
loaders below are what Phase 2's SSA map and Phase 5's per-country shape view
consume.

Public surface:
- `available_countries() -> list[str]` -- ISO3 codes parsed from `XXX_ADM0.shp`
  filenames in `<root>/shapefiles/`. Plan 05's Data Status calls this to
  confirm shapefile presence; Phase 2's country picker reuses it.
- `load_africa() -> pd.DataFrame` -- Per-extension metadata rows for the SSA
  regional shape (`AFRICA_ADM0.{shp,shx,dbf,prj}`). Path-only metadata; the
  geometry-carrying counterpart is `load_africa_geometry()`.
- `load_country(country: str) -> pd.DataFrame` -- Same metadata shape as
  `load_africa()` but for a specific ISO3-prefixed country shape.
- `load_africa_geometry() -> gpd.GeoDataFrame` -- NEW in Phase 2. Reads
  `AFRICA_ADM0.shp` via geopandas, returning a 54-row GeoDataFrame with the
  canonical `iso_a3`, `name`, `geometry` columns (Natural Earth Admin-0
  schema). Phase 2's SSA-map page is the primary consumer.
- `load_country_geometry(country: str) -> gpd.GeoDataFrame` -- NEW in Phase 2.
  Reads a per-country `<ISO3>_ADM0.shp` and returns a 1-row GeoDataFrame with
  `ADM0` (country name) and `geometry`. Phase 5 (LAYER-06 shapefiles view)
  is the primary consumer.

Caching note (Phase 1 metadata vs. Phase 2 geometry):
- The metadata loaders (`load_africa`, `load_country`, `available_countries`)
  are NOT wrapped in `@st.cache_data`. Each call performs a small number of
  `Path.stat()` lookups (O(1) per file); we want fresh mtime values on every
  Data Status reload, so caching would defeat the purpose.
- The geometry loaders ARE cached: their disk reads run through private
  `_read_*_cached(path, mtime)` helpers decorated with
  `@st.cache_data(show_spinner=False)`, mirroring Phase 1's WHO/WASH/ENSO
  pattern (D-18). Empty-state and schema-strictness contracts (D-39) match
  D-10 / D-12 / D-13: missing subdir or file -> empty GeoDataFrame + warning;
  required-column absent -> `SchemaMismatchError`.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st

from mosaic_dashboard.config import resolve_data_root
from mosaic_dashboard.data._schema import require_columns
from mosaic_dashboard.data.errors import SchemaMismatchError  # noqa: F401  re-exported for typed catches

log = logging.getLogger(__name__)

#: Subdir name under `<data_root>/` that holds the shapefiles.
SHAPEFILES_SUBDIR: str = "shapefiles"

#: Sidecar extensions that accompany every `.shp` (ESRI shapefile convention).
#: Phase 1 surfaces all four so the Data Status page can show partial-set
#: corruption (e.g., `.shp` present but `.prj` missing).
SHAPEFILE_EXTENSIONS: tuple[str, ...] = ("shp", "shx", "dbf", "prj")

#: Pattern an ADM0 stem must match to be considered a country shape.
#: Three uppercase ASCII letters — matches ISO3 alpha-3 country codes only.
#: Rejects the regional `AFRICA` aggregate (filtered separately) and any
#: malformed filenames (defensive per D-13 — "tolerate irrelevant file
#: additions").
_ISO3_PREFIX_RE: re.Pattern[str] = re.compile(r"^[A-Z]{3}$")

#: Stem reserved for the regional SSA outline — never appears in
#: `available_countries()` output.
_AFRICA_STEM: str = "AFRICA"

#: Canonical column order for the metadata DataFrames returned by
#: `load_africa()` and `load_country()`. Defined here so the empty-DataFrame
#: factory and the populated path share a single schema.
_METADATA_COLUMNS: tuple[str, ...] = (
    "filename",
    "extension",
    "exists",
    "mtime",
    "size_bytes",
)

#: Required columns the AFRICA_ADM0 GeoDataFrame must carry (D-39 schema check).
#:
#: `AFRICA_ADM0.dbf` is the Natural Earth Admin-0 schema (165 columns total --
#: see RESEARCH §3). The ISO3 column name is the **lowercase + underscore**
#: form `iso_a3`, NOT `ISO3` or `ADM0_A3` (RESEARCH P7; Natural Earth's
#: convention differs from ESRI / GADM). `name` drives map hover tooltips per
#: the Phase 2 UI-SPEC; `geometry` is the polygon column added by geopandas
#: when reading the shapefile.
AFRICA_REQUIRED_COLUMNS: frozenset[str] = frozenset({"iso_a3", "name", "geometry"})

#: Required columns for a per-country shape (D-39 schema check).
#:
#: The per-country DBFs (e.g. `AGO_ADM0.dbf`) ship with a single attribute
#: `ADM0` -- the country's display name -- and geopandas adds the `geometry`
#: column. The ISO3 itself is NOT inside the DBF; it lives only in the
#: filename prefix (verified RESEARCH §3 "Per-country XXX_ADM0.dbf schema").
#: Phase 5 LAYER-06 ("shapefiles view") is the primary consumer; Phase 2
#: ships the loader but doesn't wire it into any page yet (per CONTEXT.md
#: D-38 and RESEARCH §"Open Questions" Q4).
COUNTRY_REQUIRED_COLUMNS: frozenset[str] = frozenset({"ADM0", "geometry"})


def available_countries() -> list[str]:
    """Return sorted ISO3 codes for every country shapefile in `shapefiles/`.

    Parses `XXX_ADM0.shp` filenames in `<data_root>/shapefiles/` and extracts
    the `XXX` prefix as the ISO3 country code. The `AFRICA_ADM0.shp` regional
    aggregate is filtered out — it's the SSA-wide outline, not a country.
    Defensive validation rejects any stem that isn't exactly three uppercase
    ASCII letters (D-13: tolerate irrelevant file additions silently).

    Returns:
        Sorted, de-duplicated list of ISO3 country codes. Empty list if the
        `shapefiles/` subdir is absent (warning logged) or contains no
        matching `*_ADM0.shp` files.
    """
    root = resolve_data_root()
    subdir = root / SHAPEFILES_SUBDIR

    if not subdir.exists():
        log.warning(
            "%s/ not found at %s — returning empty country list",
            SHAPEFILES_SUBDIR,
            subdir,
        )
        return []

    countries: set[str] = set()
    for shp_path in subdir.glob("*_ADM0.shp"):
        # `XXX_ADM0.shp` → stem = "XXX_ADM0" → split on "_" → ["XXX", "ADM0"].
        # Take the prefix before the literal `_ADM0` suffix to be robust to
        # any future hyphenated codes (still rejected by the ISO3 regex below
        # if they aren't 3 uppercase letters).
        stem = shp_path.stem  # "XXX_ADM0"
        if not stem.endswith("_ADM0"):
            continue
        prefix = stem[: -len("_ADM0")]
        if prefix == _AFRICA_STEM:
            # Regional aggregate; not a country.
            continue
        if not _ISO3_PREFIX_RE.match(prefix):
            # Malformed filename — log at debug level (D-13 says "silent",
            # but keep a breadcrumb in case a teammate ever needs to debug
            # why a country is missing from the picker).
            log.debug(
                "Skipping non-ISO3 shapefile prefix %r in %s",
                prefix,
                shp_path.name,
            )
            continue
        countries.add(prefix)

    return sorted(countries)


def load_africa() -> pd.DataFrame:
    """Return presence/mtime metadata for the `AFRICA_ADM0.*` regional shape.

    Phase 1 contract — see module docstring. Phase 2 replaces this return
    type with a GeoDataFrame carrying the actual SSA outline geometry.

    Returns:
        DataFrame with one row per sidecar extension
        (`shp`, `shx`, `dbf`, `prj`) and columns
        `{filename, extension, exists, mtime, size_bytes}`. If the
        `shapefiles/` subdir is missing, every row has `exists=False` and
        `mtime`/`size_bytes` are `None`; a warning is logged once.
    """
    return _load_shape_metadata(stem=_AFRICA_STEM)


def load_country(country: str) -> pd.DataFrame:
    """Return presence/mtime metadata for a specific country's ADM0 shape.

    Args:
        country: ISO3 country code (e.g., `"AGO"`, `"BEN"`). The function
            normalizes to upper case before looking up files, matching the
            project-wide ISO3 convention (D-07).

    Returns:
        Same shape as `load_africa()` but rows reference
        `<country>_ADM0.{shp,shx,dbf,prj}`. If the country's shapefile set is
        absent (e.g., `country="ZZZ"`), every row has `exists=False`. If the
        `shapefiles/` subdir itself is missing, the same all-False shape is
        returned and a warning is logged.
    """
    # Defensive normalization — keep the project's ISO3-uppercase invariant.
    stem = country.upper()
    return _load_shape_metadata(stem=stem)


def _load_shape_metadata(stem: str) -> pd.DataFrame:
    """Build the metadata DataFrame for `<stem>_ADM0.{ext}` sidecars.

    Internal helper shared by `load_africa()` and `load_country()`. Always
    returns one row per extension in `SHAPEFILE_EXTENSIONS` (even when the
    files don't exist), so the schema is stable for the Data Status page.
    """
    root = resolve_data_root()
    subdir = root / SHAPEFILES_SUBDIR
    subdir_exists = subdir.exists()

    if not subdir_exists:
        log.warning(
            "%s/ not found at %s — returning all-False metadata for %s_ADM0",
            SHAPEFILES_SUBDIR,
            subdir,
            stem,
        )

    rows: list[dict[str, object]] = []
    for ext in SHAPEFILE_EXTENSIONS:
        filename = f"{stem}_ADM0.{ext}"
        if not subdir_exists:
            rows.append(
                {
                    "filename": filename,
                    "extension": ext,
                    "exists": False,
                    "mtime": None,
                    "size_bytes": None,
                }
            )
            continue

        path = subdir / filename
        if path.exists():
            stat = path.stat()
            rows.append(
                {
                    "filename": filename,
                    "extension": ext,
                    "exists": True,
                    "mtime": float(stat.st_mtime),
                    "size_bytes": int(stat.st_size),
                }
            )
        else:
            rows.append(
                {
                    "filename": filename,
                    "extension": ext,
                    "exists": False,
                    "mtime": None,
                    "size_bytes": None,
                }
            )

    return pd.DataFrame(rows, columns=list(_METADATA_COLUMNS))


# --- Phase 2 geometry loaders ---------------------------------------------
#
# Below this line is ADDITIVE to Phase 1 (D-38, D-40): the functions above
# this comment have stable Path-only-metadata semantics and MUST remain
# byte-for-byte unchanged. New geometry loaders wrap `geopandas.read_file`
# and honour the same `@st.cache_data(path, mtime)` pattern Phase 1
# established for the WHO/WASH/ENSO loaders (D-18).
#
# Empty-state contract (D-39, mirrors D-10):
#   - Missing subdir or missing expected `.shp/.shx/.dbf` -> log a warning
#     and return an empty GeoDataFrame with the right column set + CRS.
#   - File present but missing a required attribute -> raise
#     SchemaMismatchError (D-12, never silently swallowed).


def load_africa_geometry() -> gpd.GeoDataFrame:
    """Load the SSA-wide ADM0 GeoDataFrame from ``AFRICA_ADM0.shp``.

    Returns a GeoDataFrame with 54 rows (Natural Earth Admin-0 countries
    intersecting the Sub-Saharan / Northern Africa boundary). Columns
    include ``iso_a3`` (the project's canonical ISO3 join key), ``name``
    (short country name for hover tooltips), and ``geometry``.

    Empty-state contract (D-39, mirrors D-10):

    - If the ``shapefiles/`` subdir is absent OR ``AFRICA_ADM0.shp`` is
      missing OR any of its mandatory sidecars (``.shx``, ``.dbf``) are
      missing -> return an empty GeoDataFrame with the canonical columns
      and ``EPSG:4326`` CRS, and emit a ``logging.warning``. The
      ``.shx``/``.dbf`` guard pre-empts pyogrio's hard raise on a missing
      index file (RESEARCH P11) so callers get the same empty-state
      contract regardless of which sidecar is absent.
    - If the file is present but lacks a required attribute -> raise
      ``SchemaMismatchError(dataset="shapefiles/AFRICA_ADM0", ...)``
      (D-12 strict-on-schema; not cached, re-raises until file is fixed).

    Caching: the disk read runs through ``_read_africa_geometry_cached``
    (``@st.cache_data(show_spinner=False)``, keyed on ``(path_str, mtime)``).
    The cache misses only when AFRICA_ADM0.shp's mtime changes; in-memory
    footprint is ~3 MB and survives all reruns within the same Streamlit
    process (D-18).

    Returns:
        ``geopandas.GeoDataFrame`` (54 rows in production; empty in the
        missing-file path).

    Raises:
        SchemaMismatchError: When AFRICA_ADM0.shp is present but its DBF
            lacks one of ``iso_a3`` / ``name`` (``geometry`` is added by
            geopandas itself and would only be missing on a non-geometry
            file -- which would also surface as a schema error).
    """
    root = resolve_data_root()
    shp_path = root / SHAPEFILES_SUBDIR / "AFRICA_ADM0.shp"

    # Defensive existence check: pyogrio raises hard if any of .shp/.shx/.dbf
    # is missing (RESEARCH P11). We surface the same empty-state contract D-39
    # specifies regardless of which sidecar is missing, so the data layer
    # never propagates a raw DataSourceError to UI code.
    required_sidecars = (".shp", ".shx", ".dbf")
    missing_sidecars = [
        ext for ext in required_sidecars if not shp_path.with_suffix(ext).exists()
    ]
    if missing_sidecars:
        log.warning(
            "AFRICA_ADM0 shapefile incomplete at %s (missing %s) -- "
            "returning empty GeoDataFrame",
            shp_path.parent,
            ", ".join(missing_sidecars),
        )
        return _empty_africa_geometry()

    mtime = shp_path.stat().st_mtime
    return _read_africa_geometry_cached(str(shp_path), mtime)


@st.cache_data(show_spinner=False)
def _read_africa_geometry_cached(path: str, mtime: float) -> gpd.GeoDataFrame:
    """Cached AFRICA_ADM0 shapefile read; keyed on ``(path, mtime)``.

    The ``mtime`` parameter is in the signature SOLELY to participate in
    Streamlit's cache key -- the body does not use it (mirrors Phase 1's
    ``_who_annual_cached(path, mtime)`` style). When the file's mtime
    changes, the cache misses and the file is re-read; when it doesn't,
    the cached GeoDataFrame is returned (a fresh pickled copy per call,
    per ``@st.cache_data`` semantics).

    A ``SchemaMismatchError`` raised here is NOT cached -- it re-raises on
    every call until the file is fixed and mtime changes (Phase 1 P8).
    """
    gdf = gpd.read_file(path)
    # D-39 mirrors D-12: schema mismatch is loud and explicit, never silent.
    # AFRICA_ADM0.dbf is the Natural Earth schema; the ISO3 column is the
    # lowercase + underscore form `iso_a3` (verified 2026-05-14, RESEARCH P7).
    require_columns(gdf, AFRICA_REQUIRED_COLUMNS, dataset="shapefiles/AFRICA_ADM0")
    return gdf


def _empty_africa_geometry() -> gpd.GeoDataFrame:
    """Canonical empty GeoDataFrame for the AFRICA_ADM0 missing-file path.

    Natural Earth ships AFRICA_ADM0 in WGS84 (RESEARCH §3); the empty frame
    matches that CRS so downstream callers (folium, the SSA map page) do
    not need a special-case branch when the file is absent.
    """
    return gpd.GeoDataFrame(
        {
            "iso_a3": pd.Series(dtype="object"),
            "name": pd.Series(dtype="object"),
        },
        geometry=gpd.GeoSeries(dtype="geometry"),
        crs="EPSG:4326",
    )


def load_country_geometry(country: str) -> gpd.GeoDataFrame:
    """Load a single country's ADM0 GeoDataFrame from ``<ISO3>_ADM0.shp``.

    Args:
        country: ISO3 country code (e.g. ``"AGO"``). Normalized to upper
            case via ``country.upper()`` to match the project's ISO3
            invariant (CLAUDE.md §3) and the Phase-1 ``load_country``
            convention.

    Returns:
        GeoDataFrame with one row whose columns are ``ADM0`` (the country's
        display name, per the per-country DBF schema -- single field;
        verified RESEARCH §3) and ``geometry`` (the polygon added by
        geopandas). The ISO3 is NOT inside the DataFrame -- it lives only
        in the input argument / filename prefix.

    Empty-state contract (D-39, mirrors D-10):

    - If the ``shapefiles/`` subdir is absent OR the
      ``<ISO3>_ADM0.shp/.shx/.dbf`` set is incomplete -> return an empty
      GeoDataFrame with ``ADM0`` and ``geometry`` columns plus the
      ``EPSG:4326`` CRS, and emit a ``logging.warning``. Same defensive
      ``.shp/.shx/.dbf`` guard as ``load_africa_geometry()`` (RESEARCH
      P11).
    - If the file is present but the DBF lacks the required attribute
      -> raise ``SchemaMismatchError`` (D-12 strict-on-schema).

    Caching: the disk read runs through ``_read_country_geometry_cached``
    (``@st.cache_data(show_spinner=False)``, keyed on ``(path_str, mtime)``)
    -- same pattern as ``load_africa_geometry``. Each ISO3 has its own
    cache entry.

    Consumer note: Phase 5 LAYER-06 ("shapefiles view") is the primary
    consumer of this function; Phase 2 adds it for surface-completeness
    (D-38) but does not wire it into any page (CONTEXT.md / RESEARCH
    §"Open Questions" Q4).

    Raises:
        SchemaMismatchError: When ``<ISO3>_ADM0.shp`` is present but its
            DBF lacks ``ADM0``.
    """
    # Defensive normalization (matches the Phase 1 load_country pattern).
    stem = country.upper()
    root = resolve_data_root()
    shp_path = root / SHAPEFILES_SUBDIR / f"{stem}_ADM0.shp"

    # Same .shp/.shx/.dbf defensive check as load_africa_geometry (RESEARCH
    # P11). Pyogrio raises hard on missing .shx; we surface the empty-state
    # contract D-39 specifies regardless.
    required_sidecars = (".shp", ".shx", ".dbf")
    missing_sidecars = [
        ext for ext in required_sidecars if not shp_path.with_suffix(ext).exists()
    ]
    if missing_sidecars:
        log.warning(
            "%s_ADM0 shapefile incomplete at %s (missing %s) -- "
            "returning empty GeoDataFrame",
            stem,
            shp_path.parent,
            ", ".join(missing_sidecars),
        )
        return _empty_country_geometry()

    mtime = shp_path.stat().st_mtime
    return _read_country_geometry_cached(str(shp_path), mtime)


@st.cache_data(show_spinner=False)
def _read_country_geometry_cached(path: str, mtime: float) -> gpd.GeoDataFrame:
    """Cached per-country shapefile read; keyed on ``(path, mtime)``.

    The ``mtime`` parameter is in the signature SOLELY to participate in
    Streamlit's cache key (mirrors ``_read_africa_geometry_cached`` and the
    Phase 1 ``_who_*_cached`` style). When the file's mtime changes, the
    cache misses and the file is re-read.

    Uses ``Path(path).stem`` (e.g. ``"AGO_ADM0"``) in the dataset name so a
    ``SchemaMismatchError`` clearly identifies which country's shapefile
    triggered the failure.
    """
    gdf = gpd.read_file(path)
    require_columns(
        gdf,
        COUNTRY_REQUIRED_COLUMNS,
        dataset=f"shapefiles/{Path(path).stem}",
    )
    return gdf


def _empty_country_geometry() -> gpd.GeoDataFrame:
    """Canonical empty GeoDataFrame for the ``<ISO3>_ADM0`` missing-file path.

    Per-country shapefiles ship in EPSG:4326 (Natural Earth convention --
    verified RESEARCH §3); the empty frame matches that CRS so downstream
    callers do not need a special-case branch when the file is absent.
    """
    return gpd.GeoDataFrame(
        {"ADM0": pd.Series(dtype="object")},
        geometry=gpd.GeoSeries(dtype="geometry"),
        crs="EPSG:4326",
    )
