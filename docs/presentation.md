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
- Data: DfT Road Safety Data (formerly STATS19), 2025 extract
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
4. **The findings** (where, when, who, what)
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

**My job:** clean it, govern it, model it, and answer 8 concrete business
questions with evidence.

> *Speaker note (45s):* Frame it as a resource-allocation problem, not a
> data problem. The data is just the means. Emphasise that "actionable" is
> the bar — a number only matters if it changes a decision."

---

## Slide 4 — Approach & pipeline

```
 Raw CSVs  ──►  ETL (Python/pandas)  ──►  PostgreSQL star schema
 (DfT)          clean + decode            3 facts + 2 dims
                                                        │
        Power BI report  ◄──  13 DAX measures  ◄──  8 SQL queries (BQ1–BQ8)
        (4 pages)
```

- **Idempotent ETL** — safe to re-run, decodes coded fields to labels
- **Star schema** — the right shape for "slice by dimension, aggregate fact"
- **Every query validated** against the live warehouse before I trusted it
- **36 automated tests** guard the cleaning logic

> *Speaker note (45s):* "The pipeline is deliberately boring and
> reproducible. Idempotent means I can re-run the whole thing any time and
> get the same warehouse. That's what makes the findings defensible."

---

## Slide 5 — Data model

**Star schema** — 3 fact tables, 2 dimensions:

| Table | Grain | Rows (2025) |
|-------|-------|-------------|
| `fact_accident` | one row per accident | 101,525 |
| `fact_casualty` | one row per casualty | 127,883 |
| `fact_vehicle` | one row per vehicle | 183,948 |
| `dim_date` | one row per day | 365 |
| `dim_location` | one row per district | 2,492 |

- 5 single-directional relationships, `dim_date` marked as the date table
- 8 B-tree indexes on the join/filter columns

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

# Vulnerable road users are 78.9% of serious/fatal casualties

- **Pedestrians: 64.0%** of all serious/fatal casualties
- **Cyclists: 14.9%**
- Serious/fatal records contain *only* pedestrians, motorists, cyclists

**The single most important insight:** the majority of serious harm is
happening to people **without the protection of a vehicle**.

> *Speaker note (60s):* Pause here. This is the number to remember. "Nearly 8
> in 10 serious or fatal casualties are people on foot or on a bike. If you
> only remember one thing from this talk, make it this."

---

## Slide 8 — Finding: where

**Districts vary 2.9× in serious/fatal rate** (per accident):

- Top: **S12000034** (Scotland) — 0.870 serious/fatal per accident
- Bottom: **E07000224** (England) — 0.295
- Top 5 districts are all in **Scotland or Wales**

**Geographic clusters** (0.1° grid):

- Top 3 high-risk cells are all in the **London area** (~1,799 serious/fatal
  combined) — urban density + traffic volume

> *Speaker note (50s):* "Two different stories: rural Scotland/Wales have the
> highest *rate* (speed, road design), while London has the highest *volume*
> (density). Both matter, but they call for different interventions."

---

## Slide 9 — Finding: when

**Weekends and the small hours are the most dangerous:**

- **Weekends:** 24.3% serious/fatal rate — highest of any day
- **0–5am:** 28–30.3% serious/fatal rate — highest of any hour (4am peak 30.3%)
- **8am:** 18.7% — the *lowest*, despite the highest casualty count (8,053)

**Interpretation:** the 8am trough is a dilution effect — the morning
commute produces many minor collisions but few serious ones.

> *Speaker note (50s):* "This is a rate, not a count, and that distinction is
> the whole point. 8am has the most casualties but the fewest *serious* ones.
> Target the small hours and weekends, not the commute."

---

## Slide 10 — Finding: conditions & vehicles

**Conditions that raise severity:**

- **Darkness, no lights:** 30.6% serious/fatal (vs 22.0% daylight)
- **Rain/showers/sleet:** 28.5% · **Fog/mist:** 26.9% (vs 23.3% fine)
- **Oil/gravel/obstruction:** 26.3% · **Snow/ice:** 25.1%

**Vehicles & manoeuvres:**

- **Motorcycles (50–250cc)** hold **7 of the top 10** high-risk
  vehicle/manoeuvre combinations
- Highest: motorcycle **turning right** — 66.4% serious/fatal

> *Speaker note (50s):* "Reduced visibility and poor surfaces consistently
> push severity up. And motorcycles are dramatically over-represented in
> serious outcomes relative to their share of traffic."

---

## Slide 11 — Recommendations

| # | Insight (evidence) | Recommendation | Priority |
|---|--------------------|----------------|----------|
| 1 | VRUs = 78.9% of serious/fatal (BQ7) | Pedestrian/cyclist interventions: crossings, cycle lanes, speed limits | **High** |
| 2 | Top districts 2.9× higher rate (BQ2) | Targeted audits of top 10% of districts | **High** |
| 3 | Weekends + 0–5am peak (BQ8) | Lighting, enforcement, fatigue campaigns | Medium |
| 4 | Rain/fog raise severity (BQ3) | Drainage, signage, weather speed limits | Medium |
| 5 | Motorcycles over-represented (BQ5) | Rider training, protective gear, conflict-point design | Medium |

> *Speaker note (60s):* "Every recommendation traces back to a specific query
> and a specific number. That's what makes this actionable rather than
> aspirational."

---

## Slide 12 — Engineering: performance & testing

**Performance (EXPLAIN ANALYZE evidence):**

- Planner chose **hash joins** for full-table aggregates — correct
- **Parallel scans** kick in where beneficial (BQ1: 29 ms)
- One inefficiency found: a `GROUP BY` sort **spilling to disk**
  (`external merge, 6.5 MB`) — fixed by raising `work_mem` → in-memory
  quicksort, 832 ms → 763 ms
- All 8 queries run in **29 ms – 832 ms** — well within interactive limits

**Testing:** 36 pytest cases guard the cleaning rules (age banding, severity,
VRU flags, coded-field decoding).

> *Speaker note (50s):* "I didn't just make it work — I proved it's sound.
> The EXPLAIN analysis caught a real disk-spill, and the test suite means a
> future data change can't silently break a cleaning rule."

---

## Slide 13 — Limitations

- **Single year** (2025) — no multi-year trend or seasonality beyond 12 months
- **No exposure data** — rates aren't adjusted for traffic volume / population
- **Descriptive, not causal** — weather↔severity is correlation, not causation
- **Field sparsity** — some "Unknown" buckets limit precision
- **District attribution** — relied on ONS codes because the standard field
  was 100% unknown

> *Speaker note (40s):* "Being honest about what this *can't* tell you is as
> important as what it can. These are the caveats I'd put in front of a
> decision-maker."

---

## Slide 14 — Next steps

1. **Multi-year** analysis — trends & seasonality
2. **Exposure adjustment** — traffic volume / population denominators
3. **Predictive modelling** — flag high-risk locations & time windows
4. **Cost-benefit analysis** of the recommended interventions

> *Speaker note (30s):* "The natural evolution: from 'what happened' to
> 'what's likely to happen' and 'what's it worth fixing'."

---

## Slide 15 — Summary & Q&A

**In one line:** I turned a raw, coded, quirky government CSV dump into a
governed warehouse and a Power BI report that shows a road-safety authority
**where, when, and to whom** serious harm is happening — and that
**vulnerable road users are 78.9% of serious/fatal casualties**.

- 8 business questions answered with validated SQL
- 36 tests, EXPLAIN-verified performance, full data-quality log
- Reproducible end-to-end from a clean state in < 30 minutes

**Questions?**

> *Speaker note (30s):* Land the headline number one last time, then open the
> floor. Have `road_safety_visuals.pbix` ready to click through if asked.
