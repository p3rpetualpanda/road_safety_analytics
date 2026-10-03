# UK Road Safety Analytics — Final Report

> Template. Replace every `(placeholder)` and delete this guidance
> before submission. Target length: 2,500–4,000 words + appendices.

## 1. Executive summary

*(3–5 sentences. The single most important page. State the business
problem, the headline finding, and the top recommendation. A busy
road-safety officer should be able to act on this page alone.)*

## 2. Background & objectives

- **Business owner**: (road-safety authority / local council)
- **Problem**: (why this analysis matters to them)
- **Objectives**: O1–O5 from the project plan
- **Scope & out-of-scope**: (what you did / did not cover)

## 3. Data & methodology

- **Source**: DfT Road Safety Data (formerly STATS19),
  `data.dft.gov.uk/road-accidents-safety-data/` — UK Open Government Licence (OGL v3.0)
- **Data model**: star schema (3 facts + 2 dimensions) — see
  `sql/schema.sql`
- **ETL**: Python (pandas + psycopg2), idempotent — see `etl/load.py`
- **Analysis**: SQL (PostgreSQL) — see `sql/queries/`
- **Visualisation**: Power BI — see `dax/measures.dax`
- **Data quality**: refer to `docs/data_quality.md`

## 4. Findings (one subsection per business question)

For each BQ, follow this structure:

### BQ1 — Casualty trend over time
- **Question**: (restate)
- **Method**: (query / measure used)
- **Finding**: (the number, with the trend)
- **Interpretation**: (what it means for the business owner)
- **Evidence**: (screenshot of the Power BI visual or SQL output)

### BQ2 — Highest-risk districts / road classes
*(repeat structure)*

### BQ3 — Weather / lighting / road-surface effects
*(repeat structure)*

### BQ4 — Age & sex profile
*(repeat structure)*

### BQ5 — Vehicle type & manoeuvre risk
*(repeat structure)*

### BQ6 — Geographic clusters
*(repeat structure)*

### BQ7 — Vulnerable road user share
*(repeat structure)*

### BQ8 — Time-of-day / day-of-week patterns
*(repeat structure)*

## 5. Insights & recommendations

Distil the findings into **3–5 evidence-based insights**, each with a
concrete, actionable recommendation:

| # | Insight (evidence) | Recommendation | Priority |
|---|--------------------|----------------|----------|
| 1 | | | High/Med/Low |
| 2 | | | |
| 3 | | | |

## 6. Limitations

*(Honesty scores marks. Reference `docs/data_quality.md`. Sample bias,
time coverage, field sparsity, etc.)*

## 7. Conclusion

*(Tie back to the objectives. What would you do next?)*

## 8. Reproducibility

- **Repo layout**: (link to README)
- **How to run**: (the 6 steps from the README)
- **Environment**: Python version, PostgreSQL version, Power BI version

## Appendices

- **A. Full SQL queries** — `sql/queries/`
- **B. DAX measures** — `dax/measures.dax`
- **C. Data-quality log** — `docs/data_quality.md`
- **D. Power BI report page list** — (list the 3–4 pages)
- **E. Row-count reconciliation** — from the data-quality log
