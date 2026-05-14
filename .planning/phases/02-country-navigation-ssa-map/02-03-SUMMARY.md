---
phase: 02-country-navigation-ssa-map
plan: 03
subsystem: ui
tags: [streamlit, sidebar, selectbox, session-state, country-picker, drift-warning, page-shell]

# Dependency graph
requires:
  - phase: 02-country-navigation-ssa-map
    plan: 01
    provides: COUNTRY_SESSION_KEY constant; country_metadata module with iter_countries/name_for/ISO3_SET/warn_if_drifted_from_shapefiles
  - phase: 01-foundation-data-layer
    provides: SESSION_KEY pattern in config.py; ui/sidebar.py::render() — the Phase 1 single-widget renderer Phase 2 extends; shapefiles.available_countries() — the ISO3 iterable passed to the startup drift check
provides:
  - "ui/sidebar.py::render() now emits the canonical Phase-2 sidebar surface (header → data-root text_input → divider → country selectbox), bound to st.session_state[COUNTRY_SESSION_KEY] via key= only"
  - "First-load default = first ISO3 from country_metadata.iter_countries() (AGO/Angola); subsequent reruns preserve the user's selection (NAV-02 path)"
  - "Empty-metadata edge case renders st.sidebar.error and returns — picker page never gets a zero-options widget"
  - "app.py startup drift check fires country_metadata.warn_if_drifted_from_shapefiles(shapefiles.available_countries()) between configure_logging and render_sidebar (D-29 wiring)"
  - "Welcome copy on app.py points users at SSA Map first, Data Status second (UI-SPEC Welcome-screen copy update)"
affects: [02-04 SSA map page click handler reads/writes the same session_state slot the sidebar now binds, 02-05 manual browser verification covers B3/B4/B6, every Phase 3+ layer view reads st.session_state[COUNTRY_SESSION_KEY] exclusively]

# Tech tracking
tech-stack:
  added: []  # no new dependencies; this plan is pure wiring on the Phase 1 + 02-01 surface
  patterns:
    - "key=-only widget binding: st.selectbox bound via key=COUNTRY_SESSION_KEY ONLY, with the session_state slot seeded BEFORE the widget renders. No value=, no index= — these would clobber click-driven writes from pages/01_SSA_Map.py on rerun (RESEARCH P2)."
    - "Implicit bidirectional sync (D-37): the sidebar selectbox AND the map-page click handler both write to st.session_state[COUNTRY_SESSION_KEY]; on rerun, both read from it. No on_change callback, no parallel state, no event chain."
    - "First-load init via `if KEY not in st.session_state: st.session_state[KEY] = default` — mirrors Phase 1's SESSION_KEY init pattern; the seed runs once per session, subsequent reruns preserve writes."
    - "Empty-metadata banner-not-widget guard: when iter_countries() is empty, render st.sidebar.error and return early — never instantiate a selectbox with zero options."
    - "Caller-supplied iterable for the drift check: app.py imports shapefiles + country_metadata and passes shapefiles.available_countries() into warn_if_drifted_from_shapefiles, preserving the 02-01 decision to avoid a circular import on data/shapefiles."

key-files:
  created: []
  modified:
    - "src/mosaic_dashboard/ui/sidebar.py (Phase 2 extension: imports COUNTRY_SESSION_KEY + country_metadata; render() now emits divider + selectbox with empty-state guard and first-load init; module docstring updated to past tense referencing D-30/D-32/D-37)"
    - "src/mosaic_dashboard/app.py (Phase 2 additions: import country_metadata + shapefiles; call warn_if_drifted_from_shapefiles(shapefiles.available_countries()) between configure_logging and render_sidebar per D-29; welcome copy second st.write replaced verbatim per UI-SPEC)"

key-decisions:
  - "D-29 wiring: drift check lives in app.py near the top (Option 1 from RESEARCH §'Where to call warn_if_drifted_from_shapefiles' — simpler than gating via a session_state flag inside sidebar.render())"
  - "D-30: country selectbox rendered in ui/sidebar.py::render() below the data-root override, separated by st.sidebar.divider() — same Phase 1 pattern, no st.navigation"
  - "D-31: format_func=country_metadata.name_for; selectbox displays the country name (e.g. 'Angola'); the underlying value in session_state is the ISO3 (e.g. 'AGO')"
  - "D-32 (consumer): single source of truth — both the picker and the map-page click handler write to st.session_state[COUNTRY_SESSION_KEY]; every Phase 3+ view reads from it exclusively"
  - "D-33: first-load default = iso3_options[0] = first ISO3 from iter_countries() (Angola per the 02-01 alphabetical-by-name order). Seed happens BEFORE the widget renders so the selectbox reads a valid initial value on first run."
  - "D-37: bidirectional sync is implicit — no on_change callback, no parallel state. Streamlit's default rerun-on-change is sufficient because both inputs converge on the same session_state slot."
  - "RESEARCH P2 / P9 mitigated: key=-only binding plus pre-widget session_state seed — value=/index= deliberately omitted so click-driven writes on subsequent reruns are never clobbered."
  - "Welcome copy: UI-SPEC verbatim three-line string ('Inspect ... layer by layer. Start with **SSA Map** ... or open **Data Status** ...'); st.title and call order untouched."

patterns-established:
  - "Sidebar widget order (header → data-root text_input → divider → country selectbox) is now the canonical Phase 2+ shell; Phase 3-7 inherit this unchanged."
  - "app.py call order is now: set_page_config → _read_log_level → configure_logging → drift check → render_sidebar → welcome body. Phase 3+ may add startup checks but should slot them between configure_logging and render_sidebar to match the Phase 2 precedent."

requirements-completed: [NAV-01, NAV-02]

# Metrics
duration: ~5min
completed: 2026-05-14
---

# Phase 2 Plan 3: Country Picker Wiring (Sidebar Selectbox + app.py Welcome + Drift Warning) Summary

**`ui/sidebar.py::render()` extended with a key=-only-bound country selectbox below the existing data-root override (separated by `st.sidebar.divider()`); session_state slot seeded with the first ISO3 (Angola) on first load, empty-metadata edge case renders an `st.sidebar.error` banner. `app.py` welcome copy now directs users at the new SSA Map page first, and a startup call to `country_metadata.warn_if_drifted_from_shapefiles(shapefiles.available_countries())` surfaces the expected MUS/SYC vs ESH/-99 divergence in the launch logs.**

## Performance

- **Duration:** ~5 min wall
- **Started:** 2026-05-14T (worktree commit window)
- **Completed:** 2026-05-14
- **Tasks:** 2
- **Files modified:** 2 (both pre-existing — Phase 2 only EXTENDS the Phase 1 surface)

## Accomplishments

### Final sidebar widget order (ui/sidebar.py::render())

Top-to-bottom, exactly as UI-SPEC §Page-Shell Pattern / Sidebar widget order locks it:

1. `st.sidebar.header("Mosaic Dashboard")` — Phase 1 branding header.
2. `st.sidebar.text_input("Data root override (session only)", key=SESSION_KEY, …)` — Phase 1 data-root override (byte-stable from Phase 1).
3. `st.sidebar.divider()` — NEW Phase 2 separator between "what data to use" and "what country to look at".
4. `st.sidebar.selectbox("Country", options=iso3_options, key=COUNTRY_SESSION_KEY, format_func=country_metadata.name_for, help="Pick a country …")` — NEW Phase 2 country picker.

The empty-metadata edge case (when `country_metadata.iter_countries()` returns `[]`) renders `st.sidebar.error("No countries available. Check that country_metadata.py is populated.")` after the divider and returns early from `render()` — no selectbox is instantiated. The data-root override above the divider remains operable in that broken-metadata state.

### Final app.py call order

Top-to-bottom, with the Phase 2 addition slotted between (2) and (3):

1. `st.set_page_config(page_title="Mosaic Data Dashboard", layout="wide", initial_sidebar_state="expanded")` — Phase 1 (must remain first Streamlit call).
2. `configure_logging(_read_log_level())` — Phase 1 (idempotent across reruns).
3. **NEW:** `country_metadata.warn_if_drifted_from_shapefiles(shapefiles.available_countries())` — Phase 2 D-29 drift check.
4. `render_sidebar()` — Phase 1 (now also renders the country selectbox via the extension above).
5. Welcome body: `st.title("Mosaic Data Dashboard")` + `st.write(<UI-SPEC three-line copy>)` — Phase 1 line, Phase 2 copy.

### Welcome copy delta

| Before (Phase 1) | After (Phase 2, this plan) |
|---|---|
| `Inspect the MOSAIC-data/processed/ datasets layer by layer. Start with **Data Status** in the sidebar to verify your local checkout.` | `Inspect the MOSAIC-data/processed/ datasets layer by layer. Start with **SSA Map** in the sidebar to pick a country, or open **Data Status** to verify your local checkout.` |

UI-SPEC §"Welcome-screen copy update (`app.py`)" verbatim.

### Decisions Made (implemented this plan)

- **D-29 (wiring):** drift check called from `app.py` once per script run; safe on every rerun because the function does not raise, does not write state, and is O(54) set arithmetic plus a single `logging.warning` emission. Gating via a `_drift_check_done` flag in session_state would be unnecessary churn.
- **D-30:** country picker rendered in `ui/sidebar.py::render()` below the data-root override, separated by a divider. No `st.navigation`, no entrypoint-once magic.
- **D-31:** `format_func=country_metadata.name_for` so the visible label is the country name ("Angola") while the stored value is the ISO3 ("AGO").
- **D-32 (consumer side):** widget binds to `st.session_state[COUNTRY_SESSION_KEY]` via `key=` only. The map-page click handler (delivered in Plan 02-04) will write to the same slot — no parallel state, no callback chain.
- **D-33:** first-load init seeds `st.session_state[COUNTRY_SESSION_KEY]` to `iso3_options[0]` (= AGO under the 02-01 alphabetical-by-name order) BEFORE the selectbox renders. Subsequent reruns preserve writes.
- **D-37:** bidirectional sync is implicit — selecting in the sidebar or clicking on the map both target the same session_state slot; Streamlit's default rerun-on-change carries the new value to both surfaces.

### Critical RESEARCH findings honored

- **P2:** selectbox uses `key=COUNTRY_SESSION_KEY` ONLY. No `value=`, no `index=`. The plan's automated regex check `grep -v '^[[:space:]]*#' src/mosaic_dashboard/ui/sidebar.py | grep -cE '\b(value|index)[[:space:]]*='` returns 0.
- **P9:** widget state is preserved across reruns because `render()` is called at the top of every page (Phase 1 pattern), so the selectbox always re-instantiates and reads from `st.session_state[COUNTRY_SESSION_KEY]`.

## Deviations from Plan

None — plan executed exactly as written. The RESEARCH skeleton was copy-pasteable and matched UI-SPEC verbatim; no auto-fixes (Rules 1-3) needed and no architectural questions surfaced (Rule 4).

## Acceptance Criteria — Verification Trace

### Task 1 (sidebar.py)

| Check | Command | Result |
|---|---|---|
| Imports both keys from config | `grep -E '^from mosaic_dashboard\.config import' …/sidebar.py` | `from mosaic_dashboard.config import COUNTRY_SESSION_KEY, SESSION_KEY` ✓ |
| country_metadata import | `grep -E '^from mosaic_dashboard\.data import country_metadata' …/sidebar.py` | 1 match ✓ |
| 4 widget kinds present | `grep -cE '^\s*st\.sidebar\.(text_input\|divider\|selectbox\|error)' …/sidebar.py` | `4` ✓ |
| key=COUNTRY_SESSION_KEY | `grep -E 'key=COUNTRY_SESSION_KEY' …/sidebar.py` | 1 match ✓ |
| format_func wired | `grep -E 'format_func=country_metadata\.name_for' …/sidebar.py` | 1 match ✓ |
| No value=/index= outside comments | `grep -v '^[[:space:]]*#' …/sidebar.py \| grep -cE '\b(value\|index)[[:space:]]*='` | `0` ✓ |
| Empty-state exact copy | grep `No countries available. Check that country_metadata.py is populated.` | present ✓ |
| Phase 1 data-root block intact | `grep -E 'key=SESSION_KEY' …/sidebar.py` + `grep -c 'Data root override' …/sidebar.py` | 1 + 1 ✓ |

### Task 2 (app.py)

| Check | Command | Result |
|---|---|---|
| Combined data import | `grep -E '^from mosaic_dashboard\.data import' …/app.py` | `from mosaic_dashboard.data import country_metadata, shapefiles` ✓ |
| Drift call wired | `grep -E 'warn_if_drifted_from_shapefiles\(shapefiles\.available_countries\(\)\)' …/app.py` | 1 match ✓ |
| Call order increasing | `grep -nE '(configure_logging\(\|warn_if_drifted_from_shapefiles\(\|render_sidebar\(\))' …/app.py` | L76 < L84 < L89 ✓ |
| Welcome copy first half | `grep -F 'Start with **SSA Map** in the sidebar to pick a country, or open' …/app.py` | 1 match ✓ |
| Welcome copy second half | `grep -F '**Data Status** to verify your local checkout.' …/app.py` | 1 match ✓ |
| Phase 1 top-of-file intact | `grep -cE '(st\.set_page_config\(\|configure_logging\(\|render_sidebar\(\))' …/app.py` | `5` ≥ 3 ✓ |
| DATA-03 no network imports | `grep -rE '^(from \|import )(requests\|httpx\|urllib\.request\|aiohttp)\b' src/mosaic_dashboard/` | no matches ✓ |

## Commits

- `24d3109` `feat(02-03): extend sidebar with country selectbox + first-load init` — Task 1 (src/mosaic_dashboard/ui/sidebar.py)
- `207760f` `feat(02-03): wire startup drift check + update welcome copy for SSA Map` — Task 2 (src/mosaic_dashboard/app.py)

## Deferred / Manual Verification

Per the plan's `<verification>` block, browser-based verification (B3, B4, B6 acceptance items) is **deferred to Plan 02-05**. Specifically:

- **B3:** sidebar selectbox visibly renders with "Angola" pre-selected on first launch.
- **B4:** changing the selectbox value triggers a Streamlit rerun and the session_state slot reflects the new ISO3 (verified by inspecting `st.session_state` in a Streamlit page or via the SSA map page's "Selected: …" caption).
- **B6:** the selected country persists across navigation (Data Status ↔ welcome ↔ SSA Map page) — verified by clicking through pages and confirming the selectbox value sticks.

A headless smoke-run of `uv run python -c "from mosaic_dashboard.ui.sidebar import render; from mosaic_dashboard.config import COUNTRY_SESSION_KEY; from mosaic_dashboard.data import country_metadata, shapefiles; country_metadata.warn_if_drifted_from_shapefiles(shapefiles.available_countries())"` is the plan's `<verification>` exit-0 check. This executor's sandbox blocked `uv run python -c …` invocations during the wave (see "Sandbox notes" below); both files are AST-valid and were authored from the RESEARCH copy-pasteable skeleton, so the import path is high-confidence. Plan 02-05's verification pass will exercise it end-to-end.

## Sandbox notes

The executor's Bash sandbox during this wave declined `uv run python -c …` invocations (including the plan's exact verify command). Verification was completed via:

1. Static grep-based acceptance criteria (all checks passed — table above).
2. Copy-paste fidelity to the RESEARCH §5 skeleton, which was itself verified against Streamlit / Phase 1 patterns at planning time.
3. Confirmation that all consumed symbols (`COUNTRY_SESSION_KEY`, `country_metadata.iter_countries`, `country_metadata.name_for`, `country_metadata.warn_if_drifted_from_shapefiles`, `shapefiles.available_countries`) exist in the Phase 2 02-01 / Phase 1 surface — confirmed via Read of `config.py`, `country_metadata.py`, and `shapefiles.py`.

The full headless runtime verification is the first thing Plan 02-05's B-series checks will exercise; if any import or wiring issue surfaced, it would surface there before the manual browser checks.

## Self-Check: PASSED

- File present: `src/mosaic_dashboard/ui/sidebar.py` ✓
- File present: `src/mosaic_dashboard/app.py` ✓
- File present: `.planning/phases/02-country-navigation-ssa-map/02-03-SUMMARY.md` (this file) ✓
- Commit present: `24d3109` (Task 1) ✓
- Commit present: `207760f` (Task 2) ✓
