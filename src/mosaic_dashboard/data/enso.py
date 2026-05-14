"""ENSO climate-index loaders.

Three granularities — daily, weekly, monthly — over the compiled ENSO indices
(DMI, ENSO3, ENSO34, ENSO4) bundled into `MOSAIC-data/processed/ENSO/`.

**No country filter.** ENSO is a set of global climate indices that apply to
all countries simultaneously; per RESEARCH.md §"Per-subdir loader module map"
and §"Open Questions" item 2, the public signatures take **no** ``country``
argument. The Phase 3 ENSO view will pair each country with the full index
series.

Empty-state contract (D-08, D-10, D-13):
- Missing `ENSO/` subdir or missing expected CSV → empty DataFrame +
  `logging.warning(...)`.
- File present, missing required columns → `SchemaMismatchError` (D-12).

Cache contract (D-18, D-20): public/private split; private reader is
`@st.cache_data`-decorated and keyed on (path, mtime).

Upstream column names sourced verbatim from `COLUMN_DISCOVERY.md`. Long-format
(one row per (date, variable)).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from mosaic_dashboard.config import resolve_data_root
from mosaic_dashboard.data._schema import require_columns

log = logging.getLogger(__name__)

# Required-column sets are per-granularity and do NOT include country_iso3 —
# ENSO indices are global. See COLUMN_DISCOVERY.md §ENSO.

#: Daily ENSO indices (compiled_ENSO_1970_2025_daily.csv).
ENSO_REQUIRED_COLUMNS_DAILY: set[str] = {"date", "variable", "value"}

#: Weekly ENSO indices (compiled_ENSO_1970_2025_weekly.csv). Weekly file uses
#: ``date_start`` / ``date_stop`` interval instead of a single ``date`` column.
ENSO_REQUIRED_COLUMNS_WEEKLY: set[str] = {
    "year",
    "week",
    "date_start",
    "date_stop",
    "variable",
    "value",
}

#: Monthly ENSO indices (compiled_ENSO_1970_2025_monthly.csv).
ENSO_REQUIRED_COLUMNS_MONTHLY: set[str] = {
    "year",
    "month",
    "date_start",
    "date_stop",
    "variable",
    "value",
}

# Canonical filenames per COLUMN_DISCOVERY.md.
_ENSO_DAILY_FILENAME = "compiled_ENSO_1970_2025_daily.csv"
_ENSO_WEEKLY_FILENAME = "compiled_ENSO_1970_2025_weekly.csv"
_ENSO_MONTHLY_FILENAME = "compiled_ENSO_1970_2025_monthly.csv"


# --- Daily -----------------------------------------------------------------


def load_daily() -> pd.DataFrame:
    """Load daily ENSO indices (global; not country-filtered).

    Returns:
        DataFrame with canonical columns ``{date, variable, value}`` in long
        format (one row per (date, variable)). Empty (canonical columns, zero
        rows) when the ENSO subdir is missing or the expected CSV is absent
        (D-10, D-13).

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column (D-12).
    """
    csv_path = _resolve_enso_csv(_ENSO_DAILY_FILENAME)
    if csv_path is None:
        return _empty_daily()
    mtime = csv_path.stat().st_mtime
    return _read_enso_daily_cached(str(csv_path), mtime).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_enso_daily_cached(path: str, mtime: float) -> pd.DataFrame:
    """Cached daily-ENSO read keyed on (path, mtime)."""
    df = pd.read_csv(path, parse_dates=["date"])
    require_columns(df, ENSO_REQUIRED_COLUMNS_DAILY, dataset="ENSO/daily")
    return df


def _empty_daily() -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in ENSO_REQUIRED_COLUMNS_DAILY}
    )


# --- Weekly ----------------------------------------------------------------


def load_weekly() -> pd.DataFrame:
    """Load weekly ENSO indices (global; not country-filtered).

    Returns:
        DataFrame with canonical columns ``{year, week, date_start, date_stop,
        variable, value}``. Empty (canonical columns, zero rows) when the
        ENSO subdir is missing or the expected CSV is absent.

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column.
    """
    csv_path = _resolve_enso_csv(_ENSO_WEEKLY_FILENAME)
    if csv_path is None:
        return _empty_weekly()
    mtime = csv_path.stat().st_mtime
    return _read_enso_weekly_cached(str(csv_path), mtime).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_enso_weekly_cached(path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date_start", "date_stop"])
    require_columns(df, ENSO_REQUIRED_COLUMNS_WEEKLY, dataset="ENSO/weekly")
    return df


def _empty_weekly() -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in ENSO_REQUIRED_COLUMNS_WEEKLY}
    )


# --- Monthly ---------------------------------------------------------------


def load_monthly() -> pd.DataFrame:
    """Load monthly ENSO indices (global; not country-filtered).

    Returns:
        DataFrame with canonical columns ``{year, month, date_start,
        date_stop, variable, value}``. Empty (canonical columns, zero rows)
        when the ENSO subdir is missing or the expected CSV is absent.

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column.
    """
    csv_path = _resolve_enso_csv(_ENSO_MONTHLY_FILENAME)
    if csv_path is None:
        return _empty_monthly()
    mtime = csv_path.stat().st_mtime
    return _read_enso_monthly_cached(str(csv_path), mtime).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_enso_monthly_cached(path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date_start", "date_stop"])
    require_columns(df, ENSO_REQUIRED_COLUMNS_MONTHLY, dataset="ENSO/monthly")
    return df


def _empty_monthly() -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in ENSO_REQUIRED_COLUMNS_MONTHLY}
    )


# --- Internal helper -------------------------------------------------------


def _resolve_enso_csv(filename: str) -> Path | None:
    """Resolve ``<root>/ENSO/<filename>``; warn + return None on miss.

    Centralises the subdir-missing / file-missing branches shared across the
    three granularities. Subdir absence and missing expected file are BOTH
    warned and treated as empty per D-13 (interpretation re-confirmed during
    planning revision).
    """
    root = resolve_data_root()
    subdir = root / "ENSO"
    if not subdir.exists():
        log.warning("ENSO subdir not found at %s — returning empty", subdir)
        return None
    csv_path = subdir / filename
    if not csv_path.exists():
        log.warning(
            "ENSO expected file not found at %s — returning empty", csv_path
        )
        return None
    return csv_path


__all__ = [
    "ENSO_REQUIRED_COLUMNS_DAILY",
    "ENSO_REQUIRED_COLUMNS_WEEKLY",
    "ENSO_REQUIRED_COLUMNS_MONTHLY",
    "load_daily",
    "load_weekly",
    "load_monthly",
]
