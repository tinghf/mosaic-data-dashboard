"""Stdlib logging setup for the dashboard.

Idempotent across Streamlit reruns. Streamlit re-executes each page script on
every interaction; a naive `logging.basicConfig()` (or repeated handler
attachment) would stack duplicate handlers on every rerun, producing one log
line per re-render per attachment. The `_CONFIGURED` flag + defensive
StreamHandler check guard against that.

Logging surface:
- All loaders use stdlib `logging` via `logging.getLogger(__name__)`, which
  resolves to children of the `mosaic_dashboard` namespace (e.g.,
  `mosaic_dashboard.data.who`).
- Output goes to stderr — the terminal where `streamlit run` is executing.
  NOT to the browser. For browser-visible messages, the caller uses
  `st.warning()` / `st.error()` on the Data Status page (Plan 05).
- `propagate=False` keeps our logs off the root logger so we don't double-print
  through any handler Streamlit installs at the root.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED: bool = False


def configure(level: str = "INFO") -> None:
    """Configure stdlib logging for the `mosaic_dashboard` namespace.

    Call once near the top of `app.py` (and any page that may be hit before
    `app.py` runs). Subsequent calls are no-ops — handlers are not
    re-attached and the level is not re-set, preserving idempotence across
    Streamlit reruns and across multiple invocations from different pages.

    Args:
        level: Logging level name ("DEBUG", "INFO", "WARNING", "ERROR").
            Case-insensitive. Falls back to INFO if unrecognized. Only applied
            on the first call; subsequent calls early-return.

    Returns:
        None.

    Notes:
        Logs surface in the terminal (stderr) where `streamlit run` is running,
        NOT in the browser. For browser-visible messages, the caller uses
        `st.warning()` / `st.error()` (per RESEARCH.md "logging.warning vs
        st.warning" table).
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    logger = logging.getLogger("mosaic_dashboard")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    # Defensive double-add guard: only attach if no StreamHandler already exists
    # on this logger. Belt-and-suspenders against the _CONFIGURED flag — covers
    # the case where the module was reimported (e.g., during dev hot reload).
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.addHandler(handler)

    # Keep our logs off the root logger so we don't double-emit through any
    # handler Streamlit attaches at the root level.
    logger.propagate = False

    _CONFIGURED = True
