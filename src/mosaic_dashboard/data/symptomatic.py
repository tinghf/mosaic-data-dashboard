"""Symptomatic-fraction loader — stub-with-discovery for Phase 1.

Global summary of symptomatic-case fractions from review papers. The
upstream `location` column is mostly NA (review papers are typically global),
so this is effectively a global summary not scoped to country. The
`country` parameter is a contract placeholder for API uniformity.

Phase 1 contract: public API surface is locked; Phase 5 will decide the
final reshape / metadata-filter approach. Plan 05's Data Status page handles
file enumeration generically.

Empty-state contract (D-08, D-10, D-13): same as immunity / big-five.
Cache contract (D-18, D-20): public/private split, mtime-keyed, reversible
internals.

Upstream column names sourced from `COLUMN_DISCOVERY.md` §symptomatic.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from mosaic_dashboard.config import resolve_data_root
from mosaic_dashboard.data._schema import require_columns

log = logging.getLogger(__name__)

#: Required columns from `summary_symptomatic_cases.csv` (post-load). Phase 5
#: may extend if it adds a rename map.
SYMPTOMATIC_REQUIRED_COLUMNS: set[str] = {
    "mean",
    "ci_lo",
    "ci_hi",
    "source",
    "location",
    "year",
}

_SYMPTOMATIC_FILENAME = "summary_symptomatic_cases.csv"


def load(country: str | None = None) -> pd.DataFrame:
    """Load the symptomatic-fraction summary.

    Args:
        country: Currently unused — most rows have NA `location`. Kept for
            API uniformity. Phase 5 may treat this as a metadata filter
            where `location` is populated.

    Returns:
        DataFrame with canonical columns ``{mean, ci_lo, ci_hi, source,
        location, year}``. Empty (canonical columns, zero rows) when the
        `symptomatic/` subdir is missing or the expected CSV is absent.

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column.
    """
    csv_path = _resolve_symptomatic_csv(_SYMPTOMATIC_FILENAME)
    if csv_path is None:
        return _empty()
    mtime = csv_path.stat().st_mtime
    return _read_symptomatic_cached(str(csv_path), mtime).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_symptomatic_cached(path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    require_columns(df, SYMPTOMATIC_REQUIRED_COLUMNS, dataset="symptomatic")
    return df


def _empty() -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in SYMPTOMATIC_REQUIRED_COLUMNS}
    )


def _resolve_symptomatic_csv(filename: str) -> Path | None:
    root = resolve_data_root()
    subdir = root / "symptomatic"
    if not subdir.exists():
        log.warning(
            "symptomatic subdir not found at %s — returning empty", subdir
        )
        return None
    csv_path = subdir / filename
    if not csv_path.exists():
        log.warning(
            "symptomatic expected file not found at %s — returning empty",
            csv_path,
        )
        return None
    return csv_path


__all__ = [
    "SYMPTOMATIC_REQUIRED_COLUMNS",
    "load",
]
