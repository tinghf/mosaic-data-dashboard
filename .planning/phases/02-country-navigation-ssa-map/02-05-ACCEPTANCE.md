---
phase: 02-country-navigation-ssa-map
plan: 05
walkthrough_started: 2026-05-14
walkthrough_owner: Claude (headless probes) + user (browser walkthrough)
---

# Phase 2 Acceptance Log — B1 through B10

> Walk-through split into two halves: B1, B2, B9, B10 run headless from the
> command line by Claude (this Task 1); B3, B4, B5, B6, B7, B8 are exercised
> by the user against a live `uv run streamlit run src/mosaic_dashboard/app.py`
> session in the Task 2 checkpoint. Each section records: status (PASS / FAIL /
> Pending), maps-to (research/decision/requirement), and observed evidence.

---

## B1: `uv add` updated pyproject.toml + uv.lock cleanly; cold venv resync succeeds — PASS

**Maps to:** D-22, ROADMAP §2 (deps reproducibility)

**Probe 1a — pyproject.toml carries the three new deps:**

```
$ grep -E "geopandas|folium|streamlit-folium" pyproject.toml
    "geopandas>=1.1,<2.0",
    "folium>=0.20,<1.0",
    "streamlit-folium>=0.27,<1.0",
```

**Probe 1b — uv.lock has the resolved packages:**

```
$ grep -E "^name = \"(geopandas|folium|streamlit-folium)\"" uv.lock
name = "folium"
name = "geopandas"
name = "streamlit-folium"
```

`uv tree --depth 1` confirms the three direct dependencies at versions
`folium v0.20.0`, `geopandas v1.1.3`, `streamlit-folium v0.27.2`.

**Probe 1c — cold venv resync succeeds:**

```
$ rm -rf .venv && uv sync
[...]
 + streamlit==1.57.0
 + streamlit-folium==0.27.2
 [...]
$ echo $?
0
```

`.venv/` recreated cleanly; exit 0; no resolver errors.

**Observed:** All three probes succeed. The 3 new Phase 2 deps (with soft `>=major.minor,<next_major` pins) appear in pyproject.toml + uv.lock; the resolver builds a fresh `.venv/` from cold in a single `uv sync`.

---

## B2: `country_metadata.iter_countries()` returns 54 entries; cross-check with `shapefiles.available_countries()` matches — PASS

**Maps to:** D-25, D-29, NAV-01

**Probe:**

```
$ uv run python -c "
from mosaic_dashboard.data import country_metadata, shapefiles
meta_set = set(iso3 for iso3, _ in country_metadata.iter_countries())
shape_set = set(shapefiles.available_countries())
print(f'metadata count: {len(meta_set)}')
print(f'shapefile count: {len(shape_set)}')
print(f'in meta, no shape: {sorted(meta_set - shape_set)}')
print(f'in shape, no meta: {sorted(shape_set - meta_set)}')
"
metadata count: 54
shapefile count: 54
in meta, no shape: []
in shape, no meta: []
```

Additional confirmation: `ISO3_SET` is a 54-entry frozenset; `iter_countries()[0] == ('AGO', 'Angola')` confirms the alphabetical-by-name order with Angola first (D-26, D-27).

**Note on the RESEARCH §"CRITICAL FINDING" prediction:** RESEARCH predicted
`in meta, no shape: {'MUS', 'SYC'}` because the CRITICAL FINDING contrasts
metadata against the AFRICA_ADM0.dbf iso_a3 column. That divergence is real
(see B10 below) but is NOT what `shapefiles.available_countries()` surfaces —
the latter walks per-country `XXX_ADM0.shp` files, and `MUS_ADM0.*` /
`SYC_ADM0.*` DO exist on disk, while `ESH_ADM0.*` / `-99_ADM0.*` do NOT.
So `available_countries()` and `iter_countries()` converge perfectly at the
same 54 ISO3s. The CRITICAL FINDING divergence only surfaces against the
AFRICA_ADM0.dbf set — exercised by B10 below.

**Observed:** Metadata count is 54; per-country shapefile count is 54; both
sets are identical. No drift between `iter_countries()` and
`available_countries()` — the picker covers the entire per-country shapefile
inventory.

---

## B3: `pages/01_SSA_Map.py` is reachable from the sidebar — Pending user walkthrough

**Maps to:** D-34, MAP-01

**Verify procedure:** Launch the app (`uv sync && uv run streamlit run src/mosaic_dashboard/app.py`); sidebar should list (top-down): the "Data root override" text input, a divider, the "Country" selectbox, then Streamlit-auto-discovered page list with "Data Status" and "SSA Map" entries. Click "SSA Map" — the page should render with title "SSA Map" and subtitle "Click a country to select it, or use the Country picker in the sidebar."

**Observed:** Pending — user to report `B3 PASS` / `B3 FAIL` in the checkpoint resume.

---

## B4: Selecting "Burundi" in the sidebar selectbox writes "BDI" to session_state — Pending user walkthrough

**Maps to:** NAV-01, D-31, D-32

**Verify procedure:** Open the sidebar Country selectbox; pick "Burundi"; navigate to SSA Map; verify "Selected: Burundi (BDI)" caption appears, AND the Burundi polygon is highlighted with the red fill (`#FF4B4B`) + thicker stroke; other countries remain neutral gray (`#F0F2F6`).

**Observed:** Pending — user to report `B4 PASS` / `B4 FAIL` in the checkpoint resume.

---

## B5: Clicking on Angola in the map writes "AGO" to session_state — Pending user walkthrough

**Maps to:** MAP-01, MAP-02, D-36

**Verify procedure:** With Burundi selected from B4, click on Angola (large country on the southwest coast) on the SSA Map page. After Streamlit's rerun, verify: (a) sidebar selectbox now shows "Angola"; (b) page caption now reads "Selected: Angola (AGO)"; (c) Angola polygon is highlighted (Burundi reverts to neutral). All three feedbacks must update within the same rerun cycle.

**Observed:** Pending — user to report `B5 PASS` / `B5 FAIL` in the checkpoint resume.

---

## B6: Selectbox visually updates after a map click — Pending user walkthrough

**Maps to:** MAP-02, D-37

**Verify procedure:** Confirmation step after B5 — open the sidebar selectbox; its current value should be "Angola" (not the prior "Burundi"). This is the bidirectional half of MAP-02.

**Observed:** Pending — user to report `B6 PASS` / `B6 FAIL` in the checkpoint resume.

---

## B7: Map highlight uses the UI-SPEC colors — Pending user walkthrough

**Maps to:** UI-SPEC, MAP-02

**Verify procedure:** Cycle through five different countries via picker or click (e.g., AGO, BDI, EGY, ZAF, NGA). For each: highlighted country has red fill (`#FF4B4B`) with darker red stroke (`#B71C1C`) at 3px; unselected countries have light-gray fill (`#F0F2F6`) with neutral gray stroke (`#9AA0A6`) at 1px.

**Observed:** Pending — user to report `B7 PASS` / `B7 FAIL` in the checkpoint resume.

---

## B8: Offline-with-cached-tiles works — Pending user walkthrough

**Maps to:** DATA-03 (partial — Phase 1 A4 was the formal coverage)

**Verify procedure:** (1) Populate browser tile cache by panning/zooming the map once. (2) Disconnect network (WSL2: `sudo ip link set <iface> down`; macOS: toggle Wi-Fi off; Windows: disable the active adapter). (3) Browser hard-reload (Ctrl/Cmd+Shift+R) the SSA Map page. (4) Confirm: (a) page still loads; (b) country polygons render (SVG from local geometry — DATA-03 holds); (c) base map tiles may be cached or blank — EITHER outcome is acceptable per RESEARCH §"Offline behavior". (5) Reconnect network.

**Observed:** Pending — user to report `B8 PASS` / `B8 FAIL` in the checkpoint resume.

---

## B9: With AFRICA_ADM0.shp missing, `load_africa_geometry()` returns an empty GeoDataFrame and logs a warning (no traceback) — PASS

**Maps to:** D-39, DATA-04

**Probe (move-and-restore with shell `trap` for safety):**

```
$ SHAPE_DIR=~/MOSAIC/MOSAIC-data/processed/shapefiles
$ SRC="$SHAPE_DIR/AFRICA_ADM0.shp"
$ BAK="$SHAPE_DIR/AFRICA_ADM0.shp.bak"
$ trap 'mv "$BAK" "$SRC" 2>/dev/null' EXIT INT TERM
$ mv "$SRC" "$BAK"
$ uv run python -c "
from mosaic_dashboard.data import shapefiles
gdf = shapefiles.load_africa_geometry()
print('empty:', gdf.empty, 'rows:', len(gdf))
"
WARNING mosaic_dashboard.data.shapefiles AFRICA_ADM0 shapefile incomplete at /home/tinghf/MOSAIC/MOSAIC-data/processed/shapefiles (missing .shp) -- returning empty GeoDataFrame
empty: True rows: 0
$ # trap restored AFRICA_ADM0.shp on exit
$ ls -la "$SRC"
-rw-r--r-- 1 tinghf tinghf 210524 Feb 12 16:02 /home/tinghf/MOSAIC/MOSAIC-data/processed/shapefiles/AFRICA_ADM0.shp
```

**Observed:** Python-side empty-state contract holds — the missing-`.shp`
branch returns an empty `GeoDataFrame` (rows = 0, `.empty == True`) and emits
a single `WARNING` log line naming the missing extension. No traceback. The
`trap`-based restore left the data root with the original layout intact.

**Browser-side half of B9 — deferred to the user walkthrough:** the
in-page `st.warning("SSA shapefile not found. Check Data Status, or set the
data-root override in the sidebar.")` banner is verified by the user during
Task 2 (alongside B3/B4/B5/B6/B7/B8). For this Task 1 record we only confirm
the Python-side contract; the user is invited but not required to repeat the
file-move during their walkthrough.

---

## B10: `country_metadata.warn_if_drifted_from_shapefiles(...)` logs a warning when metadata diverges from the available ISO3 set — PASS

**Maps to:** D-29

**Probe (against the AFRICA_ADM0.dbf iso_a3 set, where the documented
CRITICAL FINDING divergence lives):**

```
$ uv run python -c "
import logging, sys
logging.basicConfig(level=logging.WARNING, format='%(levelname)s %(name)s %(message)s', stream=sys.stderr)
from mosaic_dashboard.data import country_metadata
import geopandas as gpd
africa = gpd.read_file('/home/tinghf/MOSAIC/MOSAIC-data/processed/shapefiles/AFRICA_ADM0.shp')
africa_iso3s = set(africa['iso_a3'].tolist())
country_metadata.warn_if_drifted_from_shapefiles(africa_iso3s)
print('drift check complete')
" 2>&1
WARNING mosaic_dashboard.data.country_metadata Country metadata / shapefile drift detected: in metadata but no shapefile: ['MUS', 'SYC']; in shapefiles but not metadata: ['-99', 'ESH']
drift check complete
```

**Observed:** Exactly one `WARNING` line from `mosaic_dashboard.data.country_metadata` matching the documented divergence — `['MUS', 'SYC']` listed under "in metadata but no shapefile" (these are absent from the AFRICA_ADM0.dbf even though `MUS_ADM0.*` / `SYC_ADM0.*` per-country files exist), and `['-99', 'ESH']` under "in shapefiles but not metadata" (Western Sahara and disputed Somaliland live in the DBF only). Function returns `None` (does not raise). This precisely matches RESEARCH §"CRITICAL FINDING" and confirms D-29 wiring works end-to-end.

**Secondary probe — against `shapefiles.available_countries()` (the actual
runtime call site in `app.py`):**

```
$ uv run python -c "
import logging, sys
logging.basicConfig(level=logging.WARNING, format='%(levelname)s %(name)s %(message)s', stream=sys.stderr)
from mosaic_dashboard.data import country_metadata, shapefiles
country_metadata.warn_if_drifted_from_shapefiles(shapefiles.available_countries())
print('drift check complete')
" 2>&1
drift check complete
```

No drift warning fires (the per-country file set and the metadata set are
identical at 54 ISO3s each). This is **the expected production runtime
behavior** documented in 02-01-SUMMARY: the launch logs will be quiet on a
clean data root, and the warning will only fire when MOSAIC-data upstream
changes the per-country file inventory. The CRITICAL-FINDING divergence
recorded in RESEARCH is real but lives at the AFRICA_ADM0.dbf level, NOT at
the per-country-file level — `available_countries()` walks the latter, so the
runtime drift check stays silent on a clean checkout. **This is by design**;
RESEARCH B10's expected-warning text was written against the AFRICA_ADM0.dbf
set rather than the per-country set, and the primary probe above confirms the
function emits the documented warning when given the divergent set.

---

## Requirements Coverage Map (preliminary — completes after B3-B8 walkthrough)

| Requirement                                  | B-check coverage                | Headless status |
| -------------------------------------------- | ------------------------------- | --------------- |
| NAV-01 (country picker drives every panel)   | B4 (browser)                    | Pending B4      |
| NAV-02 (country persists across views)       | implicit via B4 + sidebar       | Pending B4      |
| MAP-01 (SSA map clickable countries)         | B3, B5 (browser)                | Pending B3/B5   |
| MAP-02 (map + dropdown bidirectional sync)   | B5, B6, B7 (browser)            | Pending B5-B7   |
| D-22 (geopandas/folium/streamlit-folium pin) | B1                              | PASS            |
| D-25 / D-29 (54-entry metadata + drift)      | B2, B10                         | PASS            |
| D-39 / DATA-04 (missing-file empty state)    | B9 (Python contract)            | PASS            |
| DATA-03 (offline in hot path)                | B8 (browser); Phase-1 A4 formal | Pending B8      |

---

## Final signoff

- [ ] approved
- date:
- notes:
