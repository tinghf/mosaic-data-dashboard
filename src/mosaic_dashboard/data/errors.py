"""Typed exceptions for the data layer.

Phase 1 ships a minimal hierarchy per D-09 (CONTEXT.md): two classes only.
Future phases can introduce sibling exceptions (e.g., DataTypeMismatchError) if
dtype/value-range validation is added — they slot in under DataLayerError without
disturbing existing call sites.
"""

from __future__ import annotations


class DataLayerError(Exception):
    """Base class for all data-layer errors."""


class SchemaMismatchError(DataLayerError):
    """Raised when an expected dataset is present but its schema does not match contract.

    Per D-12 (CONTEXT.md): strict on schema mismatch within an expected dataset.
    Loaders tolerate missing subdirs and unknown extra files silently (D-10/D-13),
    but a known CSV missing a required column is loud and explicit.

    Attributes:
        dataset: Human-readable dataset name (e.g., "WHO/annual").
        missing: Set of required column names absent from the DataFrame.
        present: Set of columns actually present in the DataFrame (empty if not provided).
    """

    def __init__(
        self,
        dataset: str,
        missing: set[str],
        present: set[str] | None = None,
    ) -> None:
        self.dataset = dataset
        self.missing = set(missing)
        self.present = set(present) if present else set()
        missing_str = ", ".join(sorted(self.missing))
        msg = (
            f"Schema mismatch in dataset '{dataset}': "
            f"missing required columns {{{missing_str}}}"
        )
        super().__init__(msg)
