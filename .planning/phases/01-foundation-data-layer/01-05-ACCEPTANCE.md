# Phase 1 Acceptance Log — A1 through A10

> Scaffold authored by Plan 01-05 Task 3 (checkpoint). The user walks through
> A1-A10 from `01-RESEARCH.md` §"Validation Architecture" and records
> outcomes inline. Mark each section as **PASS**, **FAIL**, or **N/A** (with
> rationale for N/A). Set the overall phase status at the bottom.
>
> Plan 01-05 Tasks 1 and 2 are already complete and committed:
> - `bdbbaee` feat(01-05): shared sidebar helper + Streamlit entrypoint
> - `88afb3a` feat(01-05): Data Status page enumerating 12 expected processed/ subdirs
>
> Headless launch smoke checks during execution returned `STREAMLIT_LAUNCH_OK`
> (entrypoint `/`) and `DATA_STATUS_PAGE_OK` (`/Data_Status`); A2 + A3 are
> therefore expected to PASS on first interactive run.

---

## A1: `uv sync` succeeds from a fresh clone — PENDING

**Maps to:** ENV-01, ROADMAP §1 criterion 1

**How to verify:**
```bash
cd $(mktemp -d) && git clone <repo> . && uv sync
ls .venv uv.lock
```
Exit code 0; both `.venv/` and `uv.lock` exist.

**Result:**

**Observed:**

**Gap (if FAIL):**

---

## A2: `uv run streamlit run src/mosaic_dashboard/app.py` launches — PENDING

**Maps to:** ENV-02, ROADMAP §1 criterion 1

**How to verify:**
```bash
uv run streamlit run src/mosaic_dashboard/app.py
```
Terminal prints "You can now view your Streamlit app in your browser." and serves on port 8501.

**Result:**

**Observed:**

**Gap (if FAIL):**

---

## A3: Data Status page reachable and renders — PENDING

**Maps to:** D-11

**How to verify:**
Click "Data Status" in the sidebar (or visit `http://localhost:8501/Data_Status`).
The page renders a table with all 12 `EXPECTED_SUBDIRS` rows (`WHO/annual`,
`WHO/weekly`, `WHO/daily`, `WASH`, `ENSO`, `demographics`, `OAG`,
`shapefiles`, `immunity`, `vaccine_effectiveness`, `symptomatic`,
`similarity_matrix`), each showing status / file count / latest mtime.

**Result:**

**Observed (file counts + mtimes optional, status column is the key check):**

**Gap (if FAIL):**

---

## A4: Offline — dashboard still loads — PENDING

**Maps to:** DATA-03, ROADMAP §1 criterion 3

**How to verify:**
Disconnect from the network (e.g., `sudo ip link set <iface> down`, disable
wifi, or unplug ethernet). Reload `http://localhost:8501/` and navigate to
Data Status. The dashboard must render with the same content as A3.

**Result:**

**Observed:**

**Gap (if FAIL):**

---

## A5: Missing subdir produces empty DF + warning, no crash — PENDING

**Maps to:** DATA-04, D-10, ROADMAP §1 criterion 4

**How to verify:**
Either physically rename a `processed/` subdir OR set the sidebar override
to a sibling tempdir that has some subdirs missing:

```bash
# Option A: rename
mv ~/MOSAIC/MOSAIC-data/processed/WHO ~/MOSAIC/MOSAIC-data/processed/WHO.bak
# Option B: sidebar override pointing at an incomplete tempdir
```

Reload `/Data_Status`. The WHO/annual, WHO/weekly, WHO/daily rows show
`status=MISSING` with file_count=0 and mtime="—". A `logging.warning` line
appears in the terminal where `streamlit run` is executing. No traceback
appears in the browser. `st.warning(...)` banner lists the missing subdirs.

**REMEMBER to RESTORE the rename** (or clear the sidebar override) after
the check.

**Result:**

**Observed:**

**Gap (if FAIL):**

---

## A6: Malformed CSV produces SchemaMismatchError — PENDING

**Maps to:** D-12, D-13

**How to verify:**
Copy a WHO CSV into a tempdir, drop a required column, then invoke the
loader directly to force a schema check:

```bash
TMPROOT=$(mktemp -d)
mkdir -p "$TMPROOT/WHO/annual"
# Copy and mangle: drop one column (example uses cut to remove the first column)
head -n 1 ~/MOSAIC/MOSAIC-data/processed/WHO/annual/<WHO_annual_file>.csv | head
# (Adjust the column-drop step to match an actual REQUIRED column from
#  src/mosaic_dashboard/data/who.py's REQUIRED_COLUMNS_ANNUAL set.)
cut -d',' -f2- ~/MOSAIC/MOSAIC-data/processed/WHO/annual/<file>.csv > "$TMPROOT/WHO/annual/who_annual.csv"

MOSAIC_DATA_PATH= uv run python -c "
import streamlit as st
st.session_state['data_root_override'] = '$TMPROOT'
from mosaic_dashboard.data import who
try:
    who.load_annual('AGO')
    print('FAIL — no exception raised')
except Exception as e:
    print(type(e).__name__, e)
"
```

Expected output: `SchemaMismatchError ...` mentioning the dataset name
(`WHO/annual`) and the missing-column set.

If the streamlit-session-state route is awkward outside a running app, an
inline alternative is to call the underlying cached read function directly
with `_read_who_annual_cached(str(csv), csv.stat().st_mtime)` and confirm
the exception type.

**Result:**

**Observed:**

**Gap (if FAIL):**

---

## A7: Sidebar override changes effective path mid-session — PENDING

**Maps to:** DATA-01, D-03, D-04

**How to verify:**
With the app running, type a valid alternate path (e.g., a sibling
checkout, or `/tmp/empty-mosaic-root` created with only some subdirs) into
the sidebar's "Data root override (session only)" text input. Press Enter
or click elsewhere to trigger a rerun. The Data Status table refreshes to
reflect the new path's contents. Clearing the field reverts to the
config.toml / default path on the next interaction.

Confirm: editing the text input does NOT modify `config.toml` on disk
(check `git status` on the repo root afterward).

**Result:**

**Observed:**

**Gap (if FAIL):**

---

## A8: CSV edit shows on next page interaction without restart — PENDING

**Maps to:** DATA-02, D-18

**How to verify:**
Note the current `latest_mtime` for the WHO/annual row. Touch (or edit) one
of the WHO annual CSVs:

```bash
touch ~/MOSAIC/MOSAIC-data/processed/WHO/annual/*.csv
```

Reload `/Data_Status` (or click any sidebar link to trigger a rerun). The
WHO/annual `latest_mtime` updates to the new timestamp without restarting
the Streamlit process.

**Result:**

**Observed (before / after mtime):**

**Gap (if FAIL):**

---

## A9: `uv.lock` is committed — PENDING

**Maps to:** ENV-01

**How to verify:**
```bash
git ls-files | grep uv.lock
```
Returns a hit.

**Result:**

**Observed:**

**Gap (if FAIL):**

---

## A10: README documents the launch one-liner — PENDING

**Maps to:** ENV-02, ROADMAP §1 criterion 1

**How to verify:**
```bash
grep -F 'uv sync && uv run streamlit run src/mosaic_dashboard/app.py' README.md
```
Returns a hit (exact substring match).

**Result:**

**Observed:**

**Gap (if FAIL):**

---

## Requirements Coverage Map

| Requirement | A-check coverage |
| ----------- | ----------------- |
| DATA-01 (configurable data path) | A7 |
| DATA-02 (fresh-read with invisible caching) | A8 |
| DATA-03 (offline in hot path) | A4 |
| DATA-04 (missing subdir → empty + warning) | A5 (lenient half); A6 (strict half via SchemaMismatchError) |
| ENV-01 (reproducible setup with lockfile) | A1, A9 |
| ENV-02 (one-liner launches dashboard) | A2, A10 |

Every locked Phase 1 requirement is covered by at least one A-check.

---

## Phase 1 status: PENDING

<!--
Replace with EXACTLY ONE of the following two lines once A1-A10 are evaluated:

## Phase 1 status: READY TO TRANSITION

(All 10 checks PASS, or PASS with N/A rationales for any non-applicable items.
Every locked requirement (DATA-01..04, ENV-01, ENV-02) is satisfied by at
least one passing check.)

— OR —

## Phase 1 status: GAPS PRESENT

- A{N}: <one-line gap summary>
- A{N}: <one-line gap summary>

(List every failed check; the orchestrator may then run
`/gsd-plan-phase 01 --gaps` to scope closure work.)
-->
