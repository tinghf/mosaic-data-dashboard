"""WASH (Water, Sanitation & Hygiene) loader.

Single CSV from Sikder et al. 2023 — cross-sectional country-level indicators
(no time series). One public `load(country)` function per RESEARCH.md §"Per-
subdir loader module map".

Empty-state contract (D-08, D-10, D-13):
- Missing `WASH/` subdir or missing expected CSV → empty DataFrame +
  `logging.warning(...)`.
- File present, missing required columns → `SchemaMismatchError` (D-12).
- Country absent → empty DataFrame.

Cache contract (D-18, D-20): public/private split; private reader is
`@st.cache_data`-decorated and keyed on (path, mtime).

Upstream column names sourced verbatim from `COLUMN_DISCOVERY.md`. Column
names use the upstream Sikder-2023 capitalisation (`Piped_Water`, etc.) per
the COLUMN_DISCOVERY note: keep verbatim to preserve traceability to source.
Only `iso_code` is renamed to canonical `country_iso3` per D-07.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from mosaic_dashboard.config import resolve_data_root
from mosaic_dashboard.data._schema import require_columns

log = logging.getLogger(__name__)

#: WASH indicators (post-rename). Mixed-case names preserved verbatim from
#: Sikder et al. 2023 for traceability.
WASH_REQUIRED_COLUMNS: set[str] = {
    "country_iso3",
    "Piped_Water",
    "Other_Improved_Water",
    "Septic_or_Sewer_Sanitation",
    "Other_Improved_Sanitation",
    "Unimproved_Water",
    "Surface_Water",
    "Unimproved_Sanitation",
    "Open_Defecation",
    "Incidence_per_1000",
}

_WASH_FILENAME = "WASH_data_Sikder_2023.csv"


def load(country: str | None = None) -> pd.DataFrame:
    """Load WASH indicators, optionally filtered to one ISO3 country.

    Args:
        country: ISO3 country code (e.g., "AGO"). When ``None``, returns the
            full table; when set, returns only rows where
            ``country_iso3 == country`` (empty DataFrame if absent — D-08).

    Returns:
        DataFrame with canonical columns ``{country_iso3, Piped_Water,
        Other_Improved_Water, Septic_or_Sewer_Sanitation,
        Other_Improved_Sanitation, Unimproved_Water, Surface_Water,
        Unimproved_Sanitation, Open_Defecation, Incidence_per_1000}``. Empty
        (canonical columns, zero rows) when the WASH subdir is missing, the
        expected CSV is missing, or the country is absent.

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column.
    """
    root = resolve_data_root()
    subdir = root / "WASH"
    if not subdir.exists():
        log.warning("WASH subdir not found at %s — returning empty", subdir)
        return _empty_wash()
    csv_path = subdir / _WASH_FILENAME
    if not csv_path.exists():
        log.warning(
            "WASH expected file not found at %s — returning empty", csv_path
        )
        return _empty_wash()
    mtime = csv_path.stat().st_mtime
    df = _read_wash_cached(str(csv_path), mtime)
    if country is not None:
        df = df[df["country_iso3"] == country]
        if df.empty:
            return _empty_wash()
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_wash_cached(path: str, mtime: float) -> pd.DataFrame:
    """Cached WASH-CSV read keyed on (path, mtime)."""
    df = pd.read_csv(path)
    df = df.rename(columns={"iso_code": "country_iso3"})
    require_columns(df, WASH_REQUIRED_COLUMNS, dataset="WASH")
    return df


def _empty_wash() -> pd.DataFrame:
    """Canonical empty DataFrame for WASH."""
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in WASH_REQUIRED_COLUMNS}
    )


__all__ = ["WASH_REQUIRED_COLUMNS", "load"]
