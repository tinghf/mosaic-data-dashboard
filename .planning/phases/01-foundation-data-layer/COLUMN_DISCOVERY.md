# Upstream CSV Column Discovery — `MOSAIC-data/processed/`

**Discovered:** 2026-05-13
**Source:** `~/MOSAIC/MOSAIC-data/processed/` (read-only)
**Method:** `head -2` on each primary CSV (read-only operation, no upstream modifications)

This document records the verbatim upstream column names per `processed/` subdir
so Plans 03 and 04 can populate accurate `required_columns` sets and
`rename(columns={...})` maps for each loader without re-reading source files.

**Naming convention applied below:**

- "Upstream column" = the literal name in the CSV header row (quoted in CSV; unquoted here).
- "Canonical (post-rename)" = the project's normalized name per D-06/D-07. ISO3 country
  identifier is always renamed to `country_iso3`.
- `required_columns` sets are the **post-rename** column set the loader should enforce
  via `_schema.require_columns(...)` per D-12.

---

## WHO/annual/

**Files present:**
- `who_afro_annual_1949_2024.csv` (primary — broadest coverage 1949–2024)
- `who_afro_annual_1949_2021.csv` (subset; older snapshot)
- `who_afro_annual_2022.csv` (subset; year-2022 only)
- `who_afro_annual_2023_2024.csv` (subset; recent additions)
- `case_fatality_ratio_2014_2024.csv` (auxiliary CFR table — different shape, NOT a primary loader target)

**Upstream columns (verbatim, primary file `who_afro_annual_1949_2024.csv`):**
`country, iso_code, year, cases_total, region, cases_imported, cfr, deaths_total, cfr_hi, cfr_lo`

**Country column (upstream → canonical):** `iso_code` → `country_iso3`

**Date column (upstream → canonical):** None (year-resolution). `year` is integer; no `parse_dates=` needed.

**Recommended `required_columns` set (post-rename):**
`{"country_iso3", "year", "cases_total", "deaths_total", "cfr"}`

**Sample row (primary file):**
`"Algeria","DZA",1971,1332,"AFRO",NA,0.0825825825825826,110,0.0986780078613035,0.068359342212249`

**Notes for Plan 03 loader:**
- Primary file `who_afro_annual_1949_2024.csv` is the broadest; other files are redundant or auxiliary. Loader can default to this file.
- Auxiliary `case_fatality_ratio_2014_2024.csv` has shape `country, iso_code, cases_total, deaths_total, cfr, shape2, shape1, cfr_hi, cfr_lo` (no `year`) — not the primary annual table; treat as optional supplementary loader if needed.
- `cases_imported` is sometimes `NA` — pandas will read as float NaN. Loader should NOT include it in `required_columns` since it's not always populated.

---

## WHO/weekly/

**Files present:**
- `cholera_country_weekly_processed.csv` (primary — cases only)
- `cholera_country_weekly_suitability_data.csv` (extended — cases + weather suitability covariates; 68 MB)

**Upstream columns (verbatim, `cholera_country_weekly_processed.csv`):**
`country, iso_code, year, month, week, date_start, date_stop, cases, deaths, cases_binary`

**Upstream columns (verbatim, `cholera_country_weekly_suitability_data.csv`):**
`iso_code, year, week, country, month, date_start, date_stop, cases, deaths, cases_binary, cloud_cover_mean, dew_point_2m_max, dew_point_2m_mean, dew_point_2m_min, et0_fao_evapotranspiration_sum, precipitation_sum, pressure_msl_mean, relative_humidity_2m_max, relative_humidity_2m_mean, relative_humidity_2m_min, shortwave_radiation_sum, soil_moisture_0_to_10cm_mean, temperature_2m_max, temperature_2m_mean, temperature_2m_min, wind_speed_10m_max, wind_speed_10m_mean, DMI, ENSO3, ENSO34, ENSO4`

**Country column (upstream → canonical):** `iso_code` → `country_iso3`

**Date column (upstream → canonical):** `date_start` → `date_start` (parse_dates=["date_start", "date_stop"]). Format: ISO 8601 (`2023-01-02`).

**Recommended `required_columns` set (post-rename):**
`{"country_iso3", "year", "week", "date_start", "date_stop", "cases", "deaths"}`

**Sample row (primary):**
`"Burundi","BDI",2023,1,1,2023-01-02,2023-01-08,0,0,0`

**Notes for Plan 03 loader:**
- Default to `cholera_country_weekly_processed.csv` (smaller, focused on cases). Suitability covariates file is a Phase 4/5 overlay concern, not a Phase 1 loader target.
- `cases_binary` is a derived 0/1 flag (cases > 0). Not required for `required_columns` since it's reconstructable.

---

## WHO/daily/

**Files present:**
- `cholera_country_daily_processed.csv` (single file)

**Upstream columns (verbatim):**
`country, iso_code, month, week, date, cases, deaths`

**Country column (upstream → canonical):** `iso_code` → `country_iso3`

**Date column (upstream → canonical):** `date` → `date` (parse_dates=["date"]). Format: ISO 8601 (`2023-01-02`).

**Recommended `required_columns` set (post-rename):**
`{"country_iso3", "date", "cases", "deaths"}`

**Sample row:**
`"Burundi","BDI","01","1",2023-01-02,0,0`

**Notes for Plan 03 loader:**
- `month` and `week` are stored as **quoted strings** ("01", "1"), not integers. Loader may need to cast if joining on them downstream. Not required in `required_columns` since `date` carries the same info.

---

## WASH/

**Files present:**
- `WASH_data_Sikder_2023.csv` (single file, per CONTEXT.md canonical_refs)

**Upstream columns (verbatim):**
`Country, Piped_Water, Other_Improved_Water, Septic_or_Sewer_Sanitation, Other_Improved_Sanitation, Unimproved_Water, Surface_Water, Unimproved_Sanitation, Open_Defecation, Incidence_per_1000, iso_code`

**Country column (upstream → canonical):** `iso_code` → `country_iso3`

**Date column (upstream → canonical):** None (cross-sectional 2023 snapshot — no time series).

**Recommended `required_columns` set (post-rename):**
`{"country_iso3", "Piped_Water", "Other_Improved_Water", "Septic_or_Sewer_Sanitation", "Other_Improved_Sanitation", "Unimproved_Water", "Surface_Water", "Unimproved_Sanitation", "Open_Defecation", "Incidence_per_1000"}`

**Sample row:**
`"Angola",32,26.6,32.6,9.5,11.5,29.9,28.4,29.5,0.09904,"AGO"`

**Notes for Plan 03 loader:**
- Mixed-case upstream column names (e.g., `Piped_Water`) — loader may either keep them or snake-case them. Recommend keeping verbatim to preserve traceability to the Sikder 2023 source; document the choice in loader docstring.
- `Country` (with capital C) is the upstream country-name column; `iso_code` is the ISO3 code. Loader keeps ISO3 as canonical and may drop the long-form `Country` column or rename it to `country_name` for display.

---

## ENSO/

**Files present:**
- `compiled_ENSO_1970_2025_daily.csv`
- `compiled_ENSO_1970_2025_weekly.csv`
- `compiled_ENSO_1970_2025_monthly.csv`

**Upstream columns (verbatim, daily):**
`date, year, month, month_name, week, doy, variable, value`

**Upstream columns (verbatim, weekly):**
`variable, year, week, value, date_start, date_stop`

**Upstream columns (verbatim, monthly):**
`variable, year, month, value, month_name, date_start, date_stop`

**Country column (upstream → canonical):** **None** — ENSO indices are global (per D-decision context: ENSO is not country-scoped). Loaders for ENSO take **no `country` parameter**.

**Date column (upstream → canonical):**
- daily: `date` → `date` (parse_dates=["date"]), format `1970-01-01`.
- weekly: `date_start` → `date_start` (parse_dates=["date_start", "date_stop"]), format `1969-12-29`.
- monthly: `date_start` → `date_start` (parse_dates=["date_start", "date_stop"]), format `1970-01-01`.

**Recommended `required_columns` set (post-rename):**
- daily: `{"date", "variable", "value"}`
- weekly: `{"year", "week", "date_start", "date_stop", "variable", "value"}`
- monthly: `{"year", "month", "date_start", "date_stop", "variable", "value"}`

**Sample rows:**
- daily: `1970-01-01,1970,1,"January",1,1,"DMI",0.297`
- weekly: `"DMI",1970,1,0.298403225806452,1969-12-29,1970-01-04`
- monthly: `"DMI",1970,1,0.300532258064516,"January",1970-01-01,1970-01-31`

**Notes for Plan 03 loader:**
- Long-format (one row per (date, variable)). Variables observed: `DMI`, `ENSO3`, `ENSO34`, `ENSO4` (confirmed from the suitability data file in WHO/weekly which carries the same indices). Loader may pivot to wide format internally if needed by views; not Phase 1 concern.
- `variable` column is the index name (DMI = Dipole Mode Index; ENSO3/34/4 = Niño region SST anomalies).

---

## demographics/

**Files present:**
- `UN_world_population_prospects_1967_2100.csv` (global, ISO3-keyed, 1967–2100)
- `demographics_africa_2000_2023.csv` (Africa-only, with daily birth/death rates)

**Upstream columns (verbatim, UN WPP):**
`iso_code, year, total_population, births_per_1000, deaths_per_1000`

**Upstream columns (verbatim, Africa 2000–2023):**
`country, iso_code, year, population, births_per_day, deaths_per_day, birth_rate_per_day, death_rate_per_day`

**Country column (upstream → canonical):** `iso_code` → `country_iso3` (both files).

**Date column (upstream → canonical):** None — both files are year-resolution (annual).

**Recommended `required_columns` set (post-rename):**
- `load_un_wpp`: `{"country_iso3", "year", "total_population", "births_per_1000", "deaths_per_1000"}`
- `load_africa_2000_2023`: `{"country_iso3", "year", "population", "births_per_day", "deaths_per_day"}`

**Sample rows:**
- UN WPP: `"AGO",1967,5641807,52.229,26.362`
- Africa: `"Burundi","BDI",2000,6403276,757.394520547945,281.043835616438,0.000118282348058704,4.38906327974053e-05`

**Notes for Plan 03 loader:**
- UN WPP `total_population` matches the column name; Africa file uses `population` — different. Loader functions are per-file (D-05 grouping under one module), so this is fine; views pick the appropriate function.

---

## OAG/

**Files present:**
- `oag_africa_2017_mean_daily.csv`
- `oag_africa_2017_mean_weekly.csv`
- `oag_africa_2017_mean_monthly.csv`

**Upstream columns (verbatim, all three identical except `count` value scaling):**
`origin_iso2, origin_iso3, origin_name, origin_lat, origin_lon, destination_iso2, destination_iso3, destination_name, destination_lat, destination_lon, year, count`

**Country column (upstream → canonical):** **TWO** ISO3 columns — `origin_iso3` and `destination_iso3`. Loaders filter by `country` parameter against EITHER origin or destination (bidirectional, per Plan 01-03 contract noted in 01-RESEARCH.md §"Open Questions" item 2).

**Date column (upstream → canonical):** None — `year` is a single fixed value (2017) in this dataset. No parse_dates needed.

**Recommended `required_columns` set (post-rename — keeping both ISO3 columns; no rename since both are already iso3):**
`{"origin_iso3", "destination_iso3", "year", "count"}`

**Sample row (all three files, same shape, daily example):**
`"GW","GNB","Guinea-Bissau",12.0477507880705,-14.9499240572075,"GM","GMB","Gambia",13.4509534899632,-15.3963233373991,2017,1.48767123287671`

**Notes for Plan 03 loader:**
- Two ISO3 columns means OAG is the **one exception** to the "loader renames to single `country_iso3`" rule. Document this explicitly in `oag.py` docstring.
- `count` represents mean passenger flow per the specified granularity (daily/weekly/monthly).
- `origin_iso2` and `destination_iso2` are 2-letter codes; redundant with iso3 — can be dropped after load.
- Lat/lon are origin/destination centroids — useful for Phase 2 map rendering.

---

## shapefiles/

**Files present:** 55 ADM0 shapefiles (one regional + 54 per-country). Pattern: `XXX_ADM0.{shp,shx,dbf,prj}` where XXX is either `AFRICA` (regional) or a 3-letter ISO3 country code.

**ISO3 prefixes observed (54 countries):**
`AGO, BDI, BEN, BFA, BWA, CAF, CIV, CMR, COD, COG, COM, CPV, DJI, DZA, EGY, ERI, ETH, GAB, GHA, GIN, GMB, GNB, GNQ, KEN, LBR, LBY, LSO, MAR, MDG, MLI, MOZ, MRT, MUS, MWI, NAM, NER, NGA, RWA, SDN, SEN, SLE, SOM, SSD, STP, SWZ, SYC, TCD, TGO, TUN, TZA, UGA, ZAF, ZMB, ZWE`

Plus regional: `AFRICA_ADM0.*`

**Upstream columns:** N/A — shapefile binary format (not CSV). Phase 1 reads filenames only via `Path.glob('*_ADM0.shp')`. Geopandas/fiona is **deferred to Phase 2** per 01-RESEARCH.md §"Open Questions" item 3.

**Country column (upstream → canonical):** Derived from filename: split `XXX_ADM0.shp` on `_` → first token is ISO3 (or `AFRICA` for the regional shape).

**Date column (upstream → canonical):** N/A (static geometry).

**Recommended `required_columns` set:** N/A (Phase 1 exposes `available_countries()` returning a `list[str]` of ISO3 codes, NOT a DataFrame with required columns).

**Notes for Plan 04 loader:**
- `data/shapefiles.py` uses `Path.glob('*_ADM0.shp')` only. Filename ISO3 prefix IS the country identifier — no need to crack open the `.dbf` for ADM0_PCODE in Phase 1.
- `AFRICA_ADM0.*` is the regional outline; exclude from `available_countries()` or surface separately (Plan 04 decision).
- **No ADM1/ADM2 shapefiles** shipped at Phase 1 time (consistent with CONTEXT.md). Plan 06 (DRILL) will face this.

---

## immunity/

**Files present:**
- `immune_decay_data.csv`
- `immune_durability_data.csv`

**Upstream columns (verbatim, both files identical):**
`day, effectiveness, effectiveness_hi, effectiveness_lo, source`

**Country column (upstream → canonical):** **None** — these are global decay/durability curves (effectiveness vs. days since vaccination), not country-scoped. The loader takes a `country` parameter but ignores it (returns full curve regardless) — or, if a country-scoped overlay is desired, the loader can filter by `source` upstream. Plan 04 will decide.

**Date column (upstream → canonical):** None — `day` is an integer offset (days since vaccination), not a calendar date.

**Recommended `required_columns` set (post-rename):**
`{"day", "effectiveness", "effectiveness_hi", "effectiveness_lo", "source"}`

**Sample rows:**
- decay: `90,0.95,0.95,0.95,"Assumption"` then `1080,0.65,0.81,0.37,"Ali et al (2011)"`
- durability: identical schema, different curve.

**Notes for Plan 04 loader:**
- Two files share the same schema but represent different concepts (decay vs. durability). Recommend two functions: `load_decay()` and `load_durability()` — neither takes a country parameter since data is global.
- If D-08 (per-country empty DataFrame on absent-country) is invoked, it's a no-op for immunity loaders since there's no country dimension to filter on.

---

## vaccine_effectiveness/

**Files present:**
- `vaccine_effectiveness_data.csv`

**Upstream columns (verbatim):**
`day, effectiveness, effectiveness_hi, effectiveness_lo, day_min, day_max, source`

**Country column (upstream → canonical):** **None** — like immunity, this is a global decay curve from published studies.

**Date column (upstream → canonical):** None — `day` is days post-vaccination.

**Recommended `required_columns` set (post-rename):**
`{"day", "effectiveness", "effectiveness_hi", "effectiveness_lo", "source"}` (`day_min`/`day_max` are optional study-window bounds; not all rows have them.)

**Sample rows:**
- `60,0.873,0.99,0.702,NA,NA,"Azman et al (2016)"`
- `93.5,0.4,0.6,0.11,7,180,"Qadri et al (2016)"`

**Notes for Plan 04 loader:**
- `day` can be non-integer (e.g., `93.5`) — read as float, not int.
- `day_min` / `day_max` are commonly `NA` — float NaN after read.

---

## symptomatic/

**Files present:**
- `summary_symptomatic_cases.csv`

**Upstream columns (verbatim):**
`mean, ci_lo, ci_hi, source, location, year, note, note2`

**Country column (upstream → canonical):** Effectively none for filtering purposes — `location` is the column but its values are mostly `NA` (review papers are global). Loader treats this as a global summary; country parameter is ignored or used only as a metadata filter where present.

**Date column (upstream → canonical):** None — `year` is the publication year, not a time-series index.

**Recommended `required_columns` set (post-rename):**
`{"mean", "ci_lo", "ci_hi", "source", "year"}` (`location`, `note`, `note2` are optional metadata).

**Sample rows:**
- `0.57,NA,NA,"Nelson et al (2009)",NA,2009,"Review",""`
- `0.25,NA,NA,"Lueng & Matrajt (2021)",NA,2021,"Review",""`

**Notes for Plan 04 loader:**
- `note2` is sometimes empty string; not always present semantically.
- `mean` is the symptomatic fraction estimate (proportion of infections that are symptomatic).

---

## similarity_matrix/

**Files present:**
- `similarity_matrix_africa.csv`

**Upstream columns:** **Space-delimited (not comma-delimited)** square matrix. First row is column headers (one empty leading cell then 51 ISO3 codes); subsequent rows have an ISO3 row label and 51 numeric values.

**Header row (verbatim, space-delimited):**
`"" "AGO" "BDI" "BEN" "BFA" "BWA" "CAF" "CIV" "CMR" "COD" "COG" "CPV" "DJI" "DZA" "EGY" "ERI" "ETH" "GAB" "GHA" "GIN" "GMB" "GNB" "GNQ" "KEN" "LBR" "LBY" "LSO" "MAR" "MDG" "MLI" "MOZ" "MRT" "MUS" "MWI" "NAM" "NER" "NGA" "RWA" "SDN" "SEN" "SLE" "SOM" "SSD" "SWZ" "TCD" "TGO" "TUN" "TZA" "UGA" "ZAF" "ZMB" "ZWE"`

(51 country columns; row count is the same 51 — confirmed square.)

**Country column (upstream → canonical):** Country identifiers are **already ISO3** in both the row index (first cell of each data row) and column headers. Loader reads as `pd.read_csv(path, sep=' ', index_col=0)` (or equivalent) — the resulting DataFrame has `country_iso3` as both index and columns.

**Date column (upstream → canonical):** None — static (epidemiological similarity / connectivity matrix).

**Recommended `required_columns` set (post-rename):** **N/A — this is a square matrix, not a flat table.** Loader returns the full DataFrame (51×51) and views slice it. Schema check is "shape is square AND index == columns" rather than a column-set check. Plan 04 documents this exception.

**Sample row (first data row, leading `"AGO"`, then 51 numeric values, space-separated):**
`"AGO" 0 29.7 29.2 34.9 36.1 29.4 32.4 27.5 26.6 26.1 35.9 44 51 50.2 40.9 37.1 33.4 32.2 29.2 38.3 27.8 30.8 32.7 32.4 54.9 34.8 49.5 32 36 19.7 42.6 48.3 33.2 35.2 37.5 30.9 30.3 40.7 35.4 34.1 40.4 31.2 34.1 33.6 27.9 53.6 28.4 31.1 39.7 28.4 29.4 ...`

**Notes for Plan 04 loader:**
- **Delimiter is space, not comma** — must use `pd.read_csv(path, sep=r'\s+', index_col=0)` or `pd.read_csv(path, sep=' ', index_col=0, quotechar='"')`. The `.csv` extension is misleading.
- Diagonal is `0` (self-similarity = 0 distance).
- Returned DataFrame's index and columns are both ISO3 codes — no rename needed.
- 51 countries in this matrix is a subset of the 54 shapefile countries; the loader should make this difference visible to the Data Status / view layer.

---

## Read-only verification

Per the threat model (T-01-01), this discovery task only reads file headers via
`head -2`. No upstream files were modified. Stable mtime hash (sort input for
determinism — `find` traversal order is otherwise unstable):

```
$ find ~/MOSAIC/MOSAIC-data/processed/ -maxdepth 3 -type f -name "*.csv" \
      -printf "%T@ %p\n" | sort | md5sum
1a473661099f6a9059b51469b6053b0a  -
```

All file mtimes are pinned at `1770940938+` (2026-02-12 16:02 UTC, the original
upstream-data placement time) — unchanged by this discovery pass.
