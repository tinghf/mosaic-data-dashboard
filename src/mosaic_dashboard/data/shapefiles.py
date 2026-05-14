"""Shapefile presence/metadata loader -- Path-only in Phase 1.

Phase 1 returns presence/mtime metadata only -- no shapefile parsing. Phase 2
(SSA map) replaces these with full geometry reads via the geo-stack library.
The function signatures stay stable; only the return-DataFrame schema gains
geometry columns.

Per D-19 (CONTEXT.md), no heavy geo-stack dependency (the geo-pandas family --
including its underlying drivers fiona, shapely, pyproj) lands in Phase 1 --
that ~50MB surface arrives with Phase 2 (MAP). For the Data Status page
(Plan 05), Path-only file enumeration is sufficient.

Public surface:
- `available_countries() -> list[str]` -- ISO3 codes parsed from `XXX_ADM0.shp`
  filenames in `<root>/shapefiles/`. Plan 05's Data Status calls this to
  confirm shapefile presence; Phase 2's country picker reuses it.
- `load_africa() -> pd.DataFrame` -- Per-extension metadata rows for the SSA
  regional shape (`AFRICA_ADM0.{shp,shx,dbf,prj}`). Phase 2 replaces the
  return type with a geometry-carrying DataFrame.
- `load_country(country: str) -> pd.DataFrame` -- Same metadata shape as
  `load_africa()` but for a specific ISO3-prefixed country shape.

Caching note: these functions are NOT wrapped in `@st.cache_data`. Each call
performs a small number of `Path.stat()` lookups (O(1) per file); we want
fresh mtime values on every Data Status reload, so caching would defeat the
purpose.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from mosaic_dashboard.config import resolve_data_root

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
