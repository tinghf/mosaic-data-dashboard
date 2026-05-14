"""Shared sidebar UI for the Mosaic Data Dashboard.

This helper exists because the locked Streamlit native ``pages/`` directory
pattern (D-15) does NOT support the entrypoint-widget persistence idiom — that
is ``st.navigation``-only. With ``pages/``, each page is its own top-level
script and ``app.py`` is NOT re-executed when the user clicks a sidebar page
link. The workaround is straightforward: render the sidebar via this shared
helper at the top of every page (and the entrypoint), keep the widget value in
``st.session_state`` so it survives page navigation, and let Streamlit auto-sync
the widget through its ``key=`` parameter.

Phase 1 ships a single widget here — the ephemeral data-root override (D-03).
Phase 2 adds a second selectbox below the data-root override that binds to
``st.session_state[COUNTRY_SESSION_KEY]``. Both the picker AND the map-page
click handler (``pages/01_SSA_Map.py``) write to that single key —
bidirectional sync is implicit (D-32, D-37). Picker order and the first-load
default both come from ``country_metadata.iter_countries()`` (D-30, D-33).

The function is intentionally NOT cached: UI re-renders on every Streamlit
script run, and the widget reads its current value from session_state every
time anyway.
"""

from __future__ import annotations

import streamlit as st

from mosaic_dashboard.config import COUNTRY_SESSION_KEY, SESSION_KEY
from mosaic_dashboard.data import country_metadata


def render() -> None:
    """Render the shared sidebar. Call once per page (including the entrypoint).

    The data-root override is bound to ``st.session_state[SESSION_KEY]`` via
    the widget's ``key`` parameter — Streamlit reads the existing
    session_state value on each render, so the displayed value survives page
    navigation as long as this function is called on every page (P9
    mitigation: widgets not rendered on a given run have their state cleaned
    up at the end of that run).

    The session_state slot is initialized to an empty string before the widget
    renders if absent, so callers reading ``st.session_state[SESSION_KEY]``
    before the first widget render don't hit ``KeyError``. An empty string
    intentionally means "no override" — ``resolve_data_root()`` falls through
    to ``config.toml`` and then to the default.

    Phase 2 widgets (NEW): country picker selectbox, bound to
    ``st.session_state[COUNTRY_SESSION_KEY]`` (D-30, D-32). The session_state
    slot is seeded with the first ISO3 from ``country_metadata.iter_countries()``
    on first session load (D-33). Empty-metadata edge case renders an
    ``st.sidebar.error`` banner instead of the widget (UI-SPEC empty states).

    Returns:
        None. Side effect: renders sidebar widgets into the current Streamlit
        script run.
    """
    st.sidebar.header("Mosaic Dashboard")

    # --- Phase 1: data-root override (unchanged) ---
    # P9 mitigation: initialize the session_state slot BEFORE the widget
    # renders, so reads of `st.session_state[SESSION_KEY]` from any page (even
    # before the widget itself runs on that page) never hit KeyError. We
    # deliberately store the empty string rather than `None` because
    # `resolve_data_root()` treats falsy values as "no override".
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

    # --- Phase 2: divider + country picker (D-30, UI-SPEC Sidebar widget order) ---
    # Visual separator between "what data to use" (data-root override above)
    # and "what country to look at" (country picker below).
    st.sidebar.divider()

    # `iter_countries()` returns the ordered (iso3, name) list (D-25, D-27).
    countries = country_metadata.iter_countries()

    # Empty-metadata guard (UI-SPEC "Empty / error states"). If the metadata
    # module is somehow empty, render the banner and stop — do NOT render a
    # selectbox with an empty options list. The data-root override above this
    # divider already rendered, so the user can still recover via that input.
    if not countries:
        st.sidebar.error(
            "No countries available. Check that country_metadata.py is populated."
        )
        return

    # The selectbox `options` argument needs a plain list of values; the
    # `format_func` turns each ISO3 into its display name. The underlying
    # value stored in session_state is the ISO3 (D-31).
    iso3_options = [iso3 for iso3, _name in countries]

    # First-load init (D-33, RESEARCH P9): seed the session_state slot BEFORE
    # the widget renders. The guard ensures we only seed on first load —
    # subsequent reruns preserve whatever the picker or the map-page click
    # handler last wrote. Given the alphabetical-by-name ordering shipped in
    # 02-01, `iso3_options[0]` is "AGO" (Angola).
    if COUNTRY_SESSION_KEY not in st.session_state:
        st.session_state[COUNTRY_SESSION_KEY] = iso3_options[0]

    # CRITICAL: bind via key= ONLY. Do NOT pass value= or index= — that would
    # clobber click-driven writes from pages/01_SSA_Map.py on rerun (RESEARCH
    # P2). With key= alone, the widget reads its value from
    # st.session_state[COUNTRY_SESSION_KEY] on every render — so when the map
    # page writes a new ISO3 to that slot, the next rerun renders the
    # selectbox with the updated selection automatically (D-37 implicit sync).
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
