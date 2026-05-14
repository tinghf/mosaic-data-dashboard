"""Lightweight schema enforcement: required column-set check.

Phase 1 scope (D-12 in CONTEXT.md): verify required columns are present. Dtype,
value-range, and nullability checks are deferred to later phases if needed. This
deliberately avoids pulling in pandera for one type of check — a 20-line helper
is clearer and adds zero deps.

Contract:
- Required column subset present → returns None.
- Required column missing → raises SchemaMismatchError naming dataset + missing cols.
- Extra columns beyond `required` are tolerated silently (DATA-04 / D-13).
- Dtype and value-range checks are OUT OF SCOPE for Phase 1.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from .errors import SchemaMismatchError


def require_columns(
    df: pd.DataFrame,
    required: Iterable[str],
    dataset: str,
) -> None:
    """Raise SchemaMismatchError if any column in `required` is missing from `df`.

    Args:
        df: The DataFrame to check (typically just-read from CSV).
        required: Column names that MUST be present. Iterable of strings.
        dataset: Human-readable dataset name used in the error message
            (e.g., "WHO/weekly").

    Returns:
        None on success.

    Raises:
        SchemaMismatchError: If any name in `required` is absent from `df.columns`.
            Extra columns in `df` beyond `required` are tolerated (D-13).
    """
    required_set = set(required)
    missing = required_set - set(df.columns)
    if missing:
        raise SchemaMismatchError(
            dataset=dataset,
            missing=missing,
            present=set(df.columns),
        )
