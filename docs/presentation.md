# UK Road Safety Analytics — Presentation

> **Format:** 10–15 minute talk. Each `---` is a slide. Speaker notes are in
> italics under each slide. Suggested pacing is given per slide.
> **Companion artefacts:** `docs/report.md` (full evidence),
> `road_safety_visuals.pbix` (live report), `docs/performance.md` (EXPLAIN).

---

## Slide 1 — Title

# UK Road Safety Analytics

**Turning raw DfT road-safety data into governed, actionable insight**

- Data Analyst Portfolio Project
- Author: Jake
- Data: DfT Road Safety Data (formerly STATS19), 2021–2025 five-year extract + DfT Traffic Estimates (exposure)
- Stack: PostgreSQL · Python (pandas) · SQL · Power BI

> *Speaker note (30s):* "I'll walk you through how I took a raw government
> CSV dump and turned it into a governed data warehouse and an interactive
> Power BI report that answers real questions a road-safety authority cares
> about. I'll focus on the findings and the engineering that makes them
> trustworthy."

---

## Slide 2 — Agenda

1. The business problem
2. My approach & data model
3. Data quality — what I found and fixed
4. **The findings** (where, when, who, what, exposure-adjusted rates)
5. Recommendations
6. Engineering: performance & testing
7. Limitations & next steps

> *Speaker note (20s):* "Quick roadmap. The meat is in the findings — that's
> where I'll spend most of the time."

---

## Slide 3 — The business problem

**Who is this for?** A road-safety authority / local council.

**Their problem:** limited budget, and they need to know
**where, when, and to whom** serious harm is happening so they can spend
money where it saves the most lives.

**The obstacle:** the raw DfT data is voluminous, coded (integers, not
words), and full of quirks. It's not analysis-ready.

**My job:** clean it, govern it, model it, and answer 14 concrete business
questions with evidence (11 Phase A + 3 Phase B exposure-adjusted).

> *Speaker note (45s):* Frame it as a resource-allocation problem, not a
> data problem. The data is just the means. Emphasise that "actionable" is
> the bar — a number only matters if it changes a decision."

---

## Slide 4 — Approach & pipeline

```
 Raw CSVs  ──►  ETL (Python/pandas)  ──►  PostgreSQL star schema
 (DfT)          clean + decode            3 facts + 2 dims + 6 exposure
                                                        │
        Power BI report  ◄──  21 DAX measures  ◄──  14 SQL queries (BQ1–BQ14)
        (5 pages)
```

- **Idempotent ETL** — safe to re-run, decodes coded fields to labels
- **Exposure ETL** — parses 10 DfT ODS tables (TRA, VEH, RAS) into 6 exposure tables
- **Star schema** — the right shape for "slice by dimension, aggregate fact"
- **Every query validated** against the live warehouse before I trusted it
- **36 automated tests** guard the cleaning logic

> *Speaker note (45s):* "The pipeline is deliberately boring and
> reproducible. Idempotent means I can re-run the whole thing any time and
> get the same warehouse. That's what makes the findings defensible."

---

## Slide 5 — Data model

**Star schema** — 3 fact tables, 2 dimensions:

| Table | Grain | Rows (2021–2025) |
|-------|-------|-------------|
| `fact_accident` | one row per accident | 513,801 |
| `fact_casualty` | one row per casualty | 652,821 |
| `fact_vehicle` | one row per vehicle | 937,265 |
| `dim_date` | one row per day | 1,826 |
| `dim_location` | one row per district | 2,901 |

- 5 single-directional relationships (exposure tables disconnected), `dim_date` marked as the date table
- 8 B-tree indexes on the join/filter columns
- **Phase B:** 6 additional exposure tables (`exposure_vehicle_km`, `exposure_licensed_vehicles`, `ras0201_numbers`, `ras0201_rates`, `ras4001_cost_per_casualty`, `ras4001_total_cost`) loaded from 10 DfT ODS files (TRA, VEH, RAS) — disconnected, joined via DAX

> *Speaker note (40s):* "A star schema is the classic choice for this kind of
> 'aggregate a fact, slice by a dimension' analysis. The surrogate keys are
> composite because the DfT reference numbers are per-collision counters, not
> globally unique — a subtle trap I caught and documented."

---

## Slide 6 — Data quality: what I found & fixed

This is where the real analyst work happened. Highlights:

- **Coded fields** — the new DfT spec uses integers (1/2/3), not words. I
  decoded weather, lighting, road surface, vehicle type, etc. to labels.
- **Degenerate district** — `local_authority_district` was **100% `-1`** in
  the 2025 extract. Every accident would have collapsed into one district.
  I switched to the ONS district code → `dim_location` grew 396 → 2,492.
- **Unknown-age codes** — `-1`/0/99/999 mapped to a real "Unknown" band.
- **Honest "Unknown" buckets** — ~67% of vehicle records have unknown type.
  That's a genuine source gap, not my bug — I verified it and said so.

> *Speaker note (60s):* "The district one is my favourite. If I'd trusted the
> obvious field, my entire 'top districts' analysis would have been one
> meaningless bar. I'd rather show you a data-quality log than a pretty chart
> built on sand."

---

## Slide 7 — Headline finding: who is hurt

# Vulnerable road users are 57.2% of serious/fatal casualties

- **Car occupants: 37.7%** — the largest single group
- **Pedestrians: 21.2%** · **Cyclists: 14.2%** · **Motorcyclists: 19.6%**
- Broad vulnerable (ped + cyc + moto + moped + PPT): **57.2%** (78,443 of 137,044)
- Narrow VRU (ped + cyc only, BQ7): **35.5%** (48,595)

**The single most important insight:** more than half of all serious harm
is happening to people **without the full protection of a car**.

> *Speaker note (60s):* Pause here. This is the number to remember. "More
> than half of all serious or fatal casualties are people on foot, on a bike,
> or on a motorcycle. Car occupants are the largest single group, but the
> vulnerable road-user cohort is the one we can most directly protect."

---

## Slide 8 — Finding: where

**Districts vary ~5.8× in serious/fatal rate** (per accident):

- Top: **S12000034** (Scotland) — 0.628 serious/fatal per accident (441/702)
- Bottom: **EHEATHROW** — 0.109 (13/119)
- Top 3 districts are all in **Scotland**

**Geographic clusters** (0.1° grid):

- Top 6 high-risk cells: **5 in the London area** + 1 in Leeds (~12,800
  serious/fatal combined) — urban density + traffic volume

> *Speaker note (50s):* "Two different stories: rural Scotland has the
> highest *rate* (speed, road design), while London has the highest *volume*
> (density). Both matter, but they call for different interventions."

---

## Slide 9 — Finding: when

**Weekends and the small hours are the most dangerous:**

- **Weekends:** Sunday 23.1% serious/fatal rate — highest of any day (Saturday 22.3%)
- **0–5am:** 26.6–27.9% serious/fatal rate — highest of any hour (3am peak 27.9%)
- **8am:** 17.0% — the *lowest*, despite a high accident count (39,833, 6th of 24 hours)

**Interpretation:** the 8am trough is a dilution effect — the morning
commute produces many minor collisions but few serious ones.

> *Speaker note (50s):* "This is a rate, not a count, and that distinction is
> the whole point. 8am has the most casualties but the fewest *serious* ones.
> Target the small hours and weekends, not the commute."

---

## Slide 10 — Finding: conditions & vehicles

**Conditions that raise severity:**

- **Darkness, no lights:** 29.2% serious/fatal (vs 20.0% daylight)
- **Fog/mist:** 25.3% · **Rain:** 24.2% (vs 21.4% fine)
- **Wet road:** 21.8% (vs 21.1% dry)

**Vehicles & manoeuvres:**

- **Motorcycles (over 500cc)** hold **6 of the top 8** high-risk
  vehicle/manoeuvre combinations
- Highest: motorcycle **U-turn** — 62.5% serious/fatal; overtaking offside 62.2%

> *Speaker note (50s):* "Reduced visibility and poor surfaces consistently
> push severity up. And motorcycles are dramatically over-represented in
> serious outcomes relative to their share of traffic."

---

## Slide 11 — Finding: exposure-adjusted rates (Phase B)

**Per-vehicle risk is genuinely rising — not just fleet growth:**

- **BQ13:** S/F per 100K licensed vehicles: 61.9 (2021) → **69.3 (2025)** — **+12.0%**
- **BQ12:** Motorway has the **highest** S/F rate per 100M km (25.7) — speed amplifies severity
- **BQ14:** **Inner London boroughs** dominate the top exposure-adjusted rates (17–45 per 100M km)

**The key insight:** adjusting for exposure reveals that the risk per unit of
traffic is *increasing*, not just the volume. And the highest-risk areas are
not the same as the highest-volume areas.

> *Speaker note (60s):* "This is the Phase B addition. I brought in DfT's own
> traffic estimates — vehicle-kilometres, licensed fleet sizes, and DfT's
> published casualty rates — to adjust the raw counts. The result: per-vehicle
> risk is up 12% over five years. That's not a data artefact, that's a real
> trend. And the highest-risk districts by exposure-adjusted rate are Inner
> London, not rural Scotland."

---

## Slide 12 — Recommendations

| # | Insight (evidence) | Recommendation | Priority |
|---|--------------------|----------------|----------|
| 1 | Vulnerable road users = 57.2% of S/F (broad; BQ7 narrow = 35.5%) | Pedestrian/cyclist/motorcycle interventions: crossings, cycle lanes, speed limits | **High** |
| 2 | Top districts ~5.8× higher rate (BQ2) | Targeted audits of top 10% of districts | **High** |
| 3 | Weekends + 0–5am peak (BQ8) | Lighting, enforcement, fatigue campaigns | Medium |
| 4 | Rain/fog raise severity (BQ3) | Drainage, signage, weather speed limits | Medium |
| 5 | Motorcycles over-represented (BQ5) | Rider training, protective gear, conflict-point design | Medium |
| 6 | Per-vehicle risk +12% over 5 years (BQ13) | Investigate root causes: speed, road design, vehicle mix | **High** |
| 7 | Motorway highest S/F rate per 100M km (BQ12) | Motorway-specific interventions: speed management, rest areas | Medium |
| 8 | Inner London highest exposure-adjusted rates (BQ14) | Targeted London borough audits & interventions | **High** |

> *Speaker note (60s):* "Every recommendation traces back to a specific query
> and a specific number. That's what makes this actionable rather than
> aspirational."

---

## Slide 13 — Engineering: performance & testing

**Performance (EXPLAIN ANALYZE evidence):**

- Planner chose **hash joins** for full-table aggregates — correct
- **Parallel scans** kick in where beneficial (BQ1: 29 ms)
- One inefficiency found: a `GROUP BY` sort **spilling to disk**
  (`external merge, 6.5 MB`) — fixed by raising `work_mem` → in-memory
  quicksort, 832 ms → 763 ms
- All 14 queries run in **29 ms – 832 ms** — well within interactive limits

**Testing:** 36 pytest cases guard the cleaning rules (age banding, severity,
VRU flags, coded-field decoding).

> *Speaker note (50s):* "I didn't just make it work — I proved it's sound.
> The EXPLAIN analysis caught a real disk-spill, and the test suite means a
> future data change can't silently break a cleaning rule."

---

## Slide 14 — Limitations

- **Five-year extract** (2021–2025) — no causal inference
- **Exposure coverage** — TRA8904 covers 186 of 375 districts (England/Wales); Scotland national-level only
- **Miles vs km** — RAS0201 uses miles; conversion 1.609344 km/mile applied
- **Proxy rates** — vehicle-km is a proxy; pedestrian/cyclist exposure not directly captured
- **Descriptive, not causal** — weather↔severity is correlation, not causation
- **Field sparsity** — some "Unknown" buckets limit precision
- **District attribution** — relied on ONS codes because the standard field
  was 100% unknown

> *Speaker note (40s):* "Being honest about what this *can't* tell you is as
> important as what it can. These are the caveats I'd put in front of a
> decision-maker."

---

## Slide 15 — Next steps

1. ~~**Exposure adjustment**~~ — ✅ **DONE (Phase B)** — vehicle-km, fleet sizes, DfT rates
2. **IMD inequality** — link deprivation to serious/fatal rates
3. **Predictive modelling** — flag high-risk locations & time windows
4. **Cost-benefit analysis** — RAS4001 cost data loaded; build intervention ROI model

> *Speaker note (30s):* "The natural evolution: from 'what happened' to
> 'what's likely to happen' and 'what's it worth fixing'."

---

## Slide 16 — Summary & Q&A

**In one line:** I turned a raw, coded, quirky government CSV dump into a
governed warehouse and a Power BI report that shows a road-safety authority
**where, when, and to whom** serious harm is happening — and that
**vulnerable road users are 57.2% of serious/fatal casualties**.

- 14 business questions answered with validated SQL (11 Phase A + 3 Phase B)
- 21 DAX measures, 5 report pages, 6 exposure tables
- 36 tests, EXPLAIN-verified performance, full data-quality log
- Reproducible end-to-end from a clean state in < 30 minutes

**Questions?**

> *Speaker note (30s):* Land the headline number one last time, then open the
> floor. Have `road_safety_visuals.pbix` ready to click through if asked.
