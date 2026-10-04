# Power BI Build Guide — Road Safety Analytics

Phase 4 deliverable: a working, interactive `.pbix` report with a documented
star-schema data model, DAX measures, and 4 report pages.

This guide is written so a marker can reproduce the report in < 30 minutes.
All DAX lives in version control at [`dax/measures.dax`](../dax/measures.dax).

---

## Run-through (do these in order)

Work top to bottom. Each step links to the section with the detail.

| # | Step | Where |
|---|---|---|
| 1 | Confirm the `road_safety` DB is up and loaded (101,525 accidents / 127,883 casualties) | §1 |
| 2 | Connect: Get Data → PostgreSQL → `localhost` / `road_safety` / `postgres:postgres` | §1 |
| 3 | Load the 5 tables (Navigator GUI **or** paste `dax/power_query.m`) | §3 |
| 4 | **Close & Apply** — verify 5 tables appear in the Fields pane | §3 |
| 5 | Wire the 5 single-directional relationships (or apply `dax/model.tmdl`) | §2 |
| 6 | Mark `dim_date` as the date table on `full_date` | §2 |
| 7 | Add the 13 DAX measures (or they come with the TMDL) | §4 |
| 8 | Build the 4 report pages | §5 |
| 9 | Add slicers / drill-down / tooltips + theme + "how to read" note | §6 |
| 10 | Save as `road_safety_visuals.pbix` (repo root) and tick the checklist | §7 |

> **Fastest path:** steps 5–7 collapse into one action if you apply
> `dax/model.tmdl` via Tabular Editor 3 (see §4 shortcut).

---

## 1. Connection — Import mode (and why)

**Choice: Import.** Not DirectQuery.

| Factor | Import (chosen) | DirectQuery |
|---|---|---|
| Dataset size | ~413k rows total — trivially small | overkill |
| Report-time dependency | none (data cached in `.pbix`) | DB must be running |
| Visual performance | best (in-memory VertiPaqi) | per-visual round-trip to Postgres |
| Reproducibility | `.pbix` is self-contained | needs `road_safety` DB present |
| Data freshness | static 2025 extract — no live updates needed | only matters for live data |

The warehouse is a **single-year (2025) static extract** rebuilt idempotently by
`etl/load.py`. There is no live-refresh requirement, so Import is the correct
call: fastest visuals, zero runtime dependency on the database, and the `.pbix`
is fully portable.

### Connect steps

1. Power BI Desktop → **Get Data** → **PostgreSQL**.
2. Server name: `localhost`
3. Database name: `road_safety`
4. File name: *(leave blank)*
5. Click **OK** → sign in with:
   - User: `postgres`
   - Password: `postgres`
6. In the Navigator, tick the 5 tables:
   - `dim_date`
   - `dim_location`
   - `fact_accident`
   - `fact_casualty`
   - `fact_vehicle`
7. Click **Transform Data** (optional — see §3 for the one cleanup) or **Load**.

> **Driver note:** Power BI Desktop ships its own PostgreSQL connector; no ODBC
> driver install is required for Import.

---

## 2. Data model — star schema, single-directional

Five tables, five relationships. Every relationship is **single-directional**
(filter flows from the "one" side to the "many" side) and the graph is
**acyclic** — no circular relationships.

```
                 dim_date (1)
                /            \
        (many) /              \ (many)
              /                \
        fact_accident (1)   fact_casualty
              |
        (many) |
              v
         fact_vehicle

                 dim_location (1)
                /            \
        (many) /              \ (many)
              /                \
        fact_accident        fact_casualty
```

### Relationships to create (Modeling view)

| # | "One" side (unique) | "Many" side | Direction | Active |
|---|---|---|---|---|
| 1 | `dim_date[date_key]` | `fact_accident[date_key]` | Single | Yes |
| 2 | `dim_date[date_key]` | `fact_casualty[date_key]` | Single | Yes |
| 3 | `dim_location[location_key]` | `fact_accident[location_key]` | Single | Yes |
| 4 | `dim_location[location_key]` | `fact_casualty[location_key]` | Single | Yes |
| 5 | `fact_accident[accident_index]` | `fact_vehicle[accident_index]` | Single | Yes |

**Why relationship #5 is fact-to-fact:** `fact_vehicle` has no `date_key` or
`location_key` of its own. It chains through `fact_accident`, so a date or
district filter reaches vehicles via `dim_date → fact_accident → fact_vehicle`.
This is the only fact-to-fact edge and it introduces no cycle.

### Mark the date table (required for time intelligence)

1. Select the `dim_date` table.
2. **Modeling → Mark as date table** → Date column: `full_date`.

Without this, the `DATEADD` measures in `dax/measures.dax` will not resolve.

> **Single-year caveat:** with only 2025 loaded, the LY / YoY measures return
> blank/0 (no prior-year rows). This is expected, not a bug — the measures are
> in place for when a second year is loaded.

---

## 3. Power Query — load the 5 tables

Two equivalent ways to get the data in. Pick one.

### Option A — Navigator GUI (fastest)

Follow the **Connect steps** in §1: Get Data → PostgreSQL → tick the 5 tables
→ **Transform Data** (optional) → **Close & Apply**. Power BI generates the M
for you.

### Option B — paste the M script (reproducible)

[`dax/power_query.m`](../dax/power_query.m) contains five self-contained
queries (one per table) with explicit column types mirroring `sql/schema.sql`.
For each table: **Home → New Query → Advanced Editor** → clear the template →
paste the matching block → **Done**. Then **Home → Close & Apply**.

> `dax/power_query.m` is a local convenience and is **gitignored** — the
> reproducible source of truth is the database plus `dax/model.tmdl`.

### Optional cleanup

The warehouse is already clean (ETL handles decoding, age bands, VRU flags).
The only thing worth doing in Power Query is **removing surrogate keys** you
don't want on visuals:

- `fact_accident[accident_index]`, `fact_casualty[casualty_rec]`,
  `fact_vehicle[vehicle_rec]` — keep (needed for relationships / row counts).
- `dim_date[date_key]`, `dim_location[location_key]` — keep (relationship keys).

No transforms are strictly required. If you load straight from the DB, skip
this section.

---

## 4. DAX measures

All measures are in [`dax/measures.dax`](../dax/measures.dax). Add them via
**Modeling → New measure** (or paste the whole file into a new measure's
definition one at a time). Summary of what's provided:

> **Shortcut — apply the whole model at once:** [`dax/model.tmdl`](../dax/model.tmdl)
> encodes the 5 tables, the 5 relationships, the marked date table, and every
> measure above in one text file. Apply it with Tabular Editor 3 (free):
> open the `.pbix` → right-click the model → **Replace Model with TMDL** →
> select `dax/model.tmdl` → **Process**. That replaces the manual
> relationship-wiring and measure-pasting in §2 and §4 in one step.

| Measure | Purpose |
|---|---|
| `Total Accidents` | row count of `fact_accident` |
| `Total Casualties` | row count of `fact_casualty` |
| `Serious Fatal Casualties` | casualties where `severity IN {1,2}` |
| `Serious Fatal Share` | serious/fatal ÷ total casualties |
| `Casualties Per 100 Accidents` | severity-adjusted rate |
| `VRU Share` | VRU casualties ÷ total casualties |
| `VRU Serious Fatal Share` | VRU serious/fatal ÷ serious/fatal |
| `Serious Fatal Casualties LY` | prior-year (time intelligence) |
| `Serious Fatal YoY Change` | current − prior year |
| `Serious Fatal YoY %` | % change vs prior year |
| `Serious Per Accident by District` | serious/fatal ÷ accidents (ranking) |
| `Vehicles Involved` | row count of `fact_vehicle` (vehicle_type / manoeuvre visuals) |
| `Serious Fatal Accidents` | accidents where `severity IN {1,2}` (weather / lighting visuals) |

> **Note:** `Total Accidents` and the old `Accidents` duplicate were merged —
> only `Total Accidents` remains (it is the one referenced by other measures).

### Why two "extra" measures exist (filter direction)

Power BI filters flow **only from the "one" side to the "many" side** of a
relationship. A measure therefore only responds to filters on the table it
counts (or tables whose filter flows *into* that table). This produced two
"every bar shows the same number" bugs during the build, fixed by counting the
table the filter actually lives in:

- **`vehicle_type` / `manoeuvre` live in `fact_vehicle`.** `Total Accidents`
  (`COUNTROWS(fact_accident)`) did **not** respond to them — every bar showed
  the full 101,525. Fix: `Vehicles Involved = COUNTROWS(fact_vehicle)`.
- **`weather` / `lighting` live in `fact_accident`.** `Serious Fatal
  Casualties` (`COUNTROWS(fact_casualty)`) did **not** respond to them — every
  bar showed 29,296. Fix: `Serious Fatal Accidents`, which counts the
  serious/fatal *accidents* (the correct semantics, since weather/lighting are
  recorded per accident).

> **Sorting gotcha:** to sort a text column (e.g. `day_of_week_name`) by a
> numeric column (`day_of_week`), use the **Sort by field** icon in the
> Fields-pane toolbar. If the numeric column is *already* set to sort by the
> text column, setting the reverse raises a **circular dependency** error.
> Clear the existing sort on `day_of_week` first, then set
> `day_of_week_name` → sort by `day_of_week`.

---

## 5. Report pages (4)

Narrative flow: **what happened → where → who/what → why (conditions)**.

> **What was actually built:** all four pages use **bar charts** (plus KPI
> cards on Page 1). The earlier draft of this guide described a map, donut and
> matrix; the final build is simpler and more consistent. The two
> visual-specific measures in §4 (`Vehicles Involved`, `Serious Fatal
> Accidents`) exist specifically to make the Page 3 and Page 4 bar charts
> respond to their filters.

### Page 1 — Executive overview
- **KPI cards:** `Total Accidents`, `Total Casualties`,
  `Serious Fatal Casualties`, `Serious Fatal Share`, `VRU Share`.
- **Bar chart:** `Serious Fatal Casualties` by `dim_date[month_name]`
  (2025 monthly trend).
- *Stakeholder question answered:* "How bad was 2025, and when did it peak?"

### Page 2 — Geographic / district analysis
- **Bar chart:** `Serious Fatal Casualties` by `dim_location[district]`.
- **Bar chart:** `Serious Fatal Casualties` by `dim_location[urban_rural]`.
- **Bar chart:** `Serious Per Accident by District` (district ranking).
- *Stakeholder question answered:* "Where should we focus resources?"

### Page 3 — Driver & vehicle analysis
- **Bar chart:** `Vehicles Involved` by `fact_vehicle[vehicle_type]`.
- **Bar chart:** `Vehicles Involved` by `fact_vehicle[manoeuvre]`.
- **Bar chart:** `Total Casualties` by `fact_casualty[age_band]`.
- **Bar chart:** `Total Casualties` by `fact_casualty[sex]`.
- *Stakeholder question answered:* "Who is involved, and in what vehicle role?"

### Page 4 — Time & conditions
- **Bar chart:** `Serious Fatal Accidents` by `fact_accident[weather]`.
- **Bar chart:** `Serious Fatal Accidents` by `fact_accident[lighting]`.
- **Bar chart:** `Serious Fatal Casualties` by `dim_date[day_of_week_name]`
  (sorted by `day_of_week` — see the sorting gotcha in §4).
- **Bar chart:** `Serious Fatal Casualties` by `dim_date[month_name]`.
- *Stakeholder question answered:* "When and under what conditions do the
  worst outcomes happen?"

---

## 6. Interactivity & polish

- **Slicers** on every page (severity, date, district, vehicle type, conditions).
- **Drill-down:** district → police force; month → day.
- **Tooltips:** on the map, show district + serious/fatal count on hover.
- **Theme:** apply a consistent colour palette (e.g. a single accent colour for
  serious/fatal, neutral greys for context) and one font family across all pages.
- **"How to read this report" note:** a one-paragraph text box on Page 1
  explaining the severity coding (1=fatal, 2=serious, 3=slight), the VRU
  definition (pedestrian + cyclist, motorcyclists excluded), and the
  single-year scope.

---

## 7. Deliverable checklist

- [ ] `.pbix` saved to the repo — `road_safety_visuals.pbix` (repo root)
- [ ] DAX in version control — `dax/measures.dax` ✅
- [ ] Data model in version control — `dax/model.tmdl` ✅
- [ ] Data model documented — this file, §2 ✅
- [ ] 4 report pages with narrative flow — §5 ✅
- [ ] Slicers / drill-down / tooltips — §6 ✅
- [ ] Consistent theme — §6 ✅
- [ ] "How to read this report" note — §6 ✅
- [ ] Connection mode + rationale documented — §1 ✅
