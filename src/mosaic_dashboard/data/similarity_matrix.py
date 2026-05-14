"""Country-similarity-matrix loader — stub-with-discovery for Phase 1.

The upstream file (`similarity_matrix_africa.csv`) is a **space-delimited**
square matrix with ISO3 country codes as both row labels and column headers
(51×51). Per Plan 04 contract, the loader returns this as a `pandas.DataFrame`
with `country_iso3` as both the index name and column name; the `country`
parameter filters to that country's row+column (the similarity row vector
and column vector) — Phase 5 will decide the exact return shape (single row,
row+col, or pivoted long-form).

In Phase 1, the stub returns the full matrix when `country=None` and an
empty DataFrame when the file is missing. When `country` is set, it returns
the filtered row(s) where that ISO3 is the row label.

Empty-state contract (D-08, D-10, D-13): same as the other small-five.
Cache contract (D-18, D-20): public/private split, mtime-keyed.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from mosaic_dashboard.config import resolve_data_root

log = logging.getLogger(__name__)

#: Schema validation is intentionally empty in Phase 1 — the file shape
#: (square ISO3 matrix) isn't a column-set contract; Phase 5 will add a
#: dedicated shape check (e.g., assert square, assert index == columns).
#: An empty frozenset means `require_columns` is a no-op for this loader.
SIMILARITY_MATRIX_REQUIRED_COLUMNS: frozenset[str] = frozenset()

_SIMILARITY_FILENAME = "similarity_matrix_africa.csv"


def load(country: str | None = None) -> pd.DataFrame:
    """Load the country-similarity matrix.

    Args:
        country: ISO3 country code. When ``None``, returns the full 51x51
            matrix; when set, returns only the row(s) where ``country`` is
            the row label (empty DataFrame if absent — D-08).

    Returns:
        DataFrame with ISO3 country codes as the index and column names.
        Empty (zero rows, zero columns) when the `similarity_matrix/` subdir
        is missing or the expected CSV is absent.

    Raises:
        SchemaMismatchError: Not raised in Phase 1 (Phase 5 will add a
            dedicated square-matrix shape check).
    """
    csv_path = _resolve_sim_csv(_SIMILARITY_FILENAME)
    if csv_path is None:
        return _empty()
    mtime = csv_path.stat().st_mtime
    df = _read_sim_cached(str(csv_path), mtime)
    if country is not None:
        if country not in df.index:
            return _empty()
        # Return as a 1-row DataFrame so the caller can index columns
        # uniformly with the unfiltered case.
        return df.loc[[country]]
    return df


@st.cache_data(show_spinner=False)
def _read_sim_cached(path: str, mtime: float) -> pd.DataFrame:
    """Cached similarity-matrix read keyed on (path, mtime).

    The CSV is space-delimited (NOT comma-delimited) with the first column
    being the row label. Phase 5 may switch to a tighter parser; the API
    contract (DataFrame with ISO3 index + columns) does not change (D-20).
    """
    df = pd.read_csv(path, sep=r"\s+", index_col=0)
    df.index.name = "country_iso3"
    df.columns.name = "country_iso3"
    return df


def _empty() -> pd.DataFrame:
    """Empty DataFrame; ISO3 index name preserved so callers can reason about it."""
    empty = pd.DataFrame()
    empty.index.name = "country_iso3"
    empty.columns.name = "country_iso3"
    return empty


def _resolve_sim_csv(filename: str) -> Path | None:
    root = resolve_data_root()
    subdir = root / "similarity_matrix"
    if not subdir.exists():
        log.warning(
            "similarity_matrix subdir not found at %s — returning empty", subdir
        )
        return None
    csv_path = subdir / filename
    if not csv_path.exists():
        log.warning(
            "similarity_matrix expected file not found at %s — returning empty",
            csv_path,
        )
        return None
    return csv_path


__all__ = [
    "SIMILARITY_MATRIX_REQUIRED_COLUMNS",
    "load",
]
