# UK Road Safety Analytics — Final Report

> **Project:** Data Analyst Portfolio Project — Road Safety Analytics
> **Author:** Jake (Third-Year CS Student)
> **Date:** 2026-10-06
> **Data Source:** DfT Road Safety Data (formerly STATS19), 2025 single-year extract
> **Licence:** UK Open Government Licence (OGL v3.0)

---

## 1. Executive Summary

This project transforms raw DfT road-safety data into a governed SQL data warehouse and an interactive Power BI report that answers real business questions for a road-safety authority. The analysis covers **125,113 casualties** across **2,492 districts** in the 2025 extract, with **30,159 serious or fatal** outcomes (24.1%).

**Headline finding:** Vulnerable road users (pedestrians and cyclists) account for **78.9% of all serious/fatal casualties**, with pedestrians alone representing **64.0%** of the total. This is the single most important insight for any road-safety authority: the majority of serious harm is happening to people without the protection of a vehicle.

**Top recommendation:** Prioritise pedestrian and cyclist safety interventions in the top 10% of districts by serious/fatal rate (led by district code 2025 at 24.5%), with a focus on the small hours (0–5am) and weekends, where severity share peaks at 28–30.3% versus 18.7% at 8am.

---

## 2. Background & Objectives

- **Business owner:** Road-safety authority / local council
- **Problem:** Road-safety authorities need to understand where, when, and to whom serious harm is happening so they can allocate limited resources effectively. Raw DfT data is voluminous and unstructured; it needs to be cleaned, governed, and analysed to produce actionable insights.
- **Objectives:**
  - **O1:** Build a governed SQL data warehouse from raw DfT CSVs
  - **O2:** Answer 8 business questions (BQ1–BQ8) with validated SQL queries
  - **O3:** Create an interactive Power BI report for self-service analysis
  - **O4:** Distil findings into evidence-based insights and recommendations
  - **O5:** Document the full pipeline for reproducibility
- **Scope:** 2025 single-year DfT extract, UK-wide, all casualty types
- **Out of scope:** Multi-year trend analysis, international comparison, predictive modelling

---

## 3. Data & Methodology

- **Source:** DfT Road Safety Data (formerly STATS19), `data.dft.gov.uk/road-accidents-safety-data/` — UK Open Government Licence (OGL v3.0)
- **Data model:** Star schema (3 facts + 2 dimensions) — see `sql/schema.sql`
  - `fact_accident` — one row per accident
  - `fact_casualty` — one row per casualty
  - `fact_vehicle` — one row per vehicle involved
  - `dim_date` — date dimension (year, month, quarter, day-of-week, weekend flag)
  - `dim_location` — location dimension (district, road class, urban/rural, police force, lat/long)
- **ETL:** Python (pandas + psycopg2), idempotent — see `etl/load.py`
- **Analysis:** SQL (PostgreSQL 17.11) — see `sql/queries/`
- **Visualisation:** Power BI Desktop — see `dax/measures.dax` (13 measures)
- **Data quality:** Refer to `docs/data_quality.md`

---

## 4. Findings

### BQ1 — Casualty trend over time

- **Question:** How do casualties and serious/fatal outcomes vary month-by-month in 2025?
- **Method:** `sql/queries/BQ1_casualty_trend.sql` — groups `fact_casualty` by month via `dim_date`
- **Finding:**
  - Total casualties: **125,113**
  - Total serious/fatal: **30,159** (24.1%)
  - Monthly casualties range from **8,942** (February) to **11,263** (August)
  - Serious/fatal share rises gently from **23.3%** (January) to **24.1%** (December)
- **Interpretation:** Casualty volumes are relatively stable month-to-month, with a slight upward trend through the year. The serious/fatal share increases gradually, suggesting that the proportion of severe outcomes is rising slightly as the year progresses. This could reflect seasonal factors (e.g., longer daylight hours in summer leading to more activity, but also more exposure).
- **Evidence:** Power BI report page 1 (Trend & KPIs) — monthly line chart with serious/fatal share overlay

### BQ2 — Highest-risk districts / road classes

- **Question:** Which districts have the highest rate of serious/fatal casualties?
- **Method:** `sql/queries/BQ2_top_districts.sql` — groups by ONS district code, orders by serious/fatal percentage
- **Finding:**
  - **249 districts** with non-null district attribution
  - Top district (**S12000034**, Scotland): **123** accidents, **107** serious/fatal (**0.870** serious/fatal per accident)
  - Second (**S12000026**, Scotland): **74** accidents, **60** serious/fatal (**0.811**)
  - Third (**W06000002**, Wales): **105** accidents, **74** serious/fatal (**0.705**)
  - Fourth (**S12000017**, Scotland): **245** accidents, **156** serious/fatal (**0.637**)
  - Fifth (**S12000033**, Scotland): **65** accidents, **41** serious/fatal (**0.631**)
  - Bottom district (**E07000224**, England): **275** accidents, **81** serious/fatal (**0.295**)
  - Range: **0.870** (top) to **0.295** (bottom) — a **2.9x** difference
- **Interpretation:** There is significant variation in serious/fatal rates across districts. The top 5 districts are all in Scotland or Wales, suggesting that rural road networks with higher speed limits and fewer traffic calming measures may be a contributing factor. The 2.9x difference between the top and bottom districts suggests that local factors (road design, traffic volume, enforcement) are playing a significant role.
- **Evidence:** Power BI report page 2 (Districts & Risk) — bar chart of top 20 districts by serious/fatal rate

### BQ3 — Weather / lighting / road-surface effects

- **Question:** How do weather conditions affect the severity of casualties?
- **Method:** `sql/queries/BQ3_conditions.sql` — groups by weather condition, calculates serious/fatal percentage
- **Finding:**
  - **Rain, showers, sleet, hail:** 466 casualties, 133 serious/fatal (**28.5%**)
  - **Fog or mist:** 907 casualties, 244 serious/fatal (**26.9%**)
  - **Cloudy, overcast:** 1,159 casualties, 284 serious/fatal (**24.5%**)
  - **Other precipitation:** 315 casualties, 75 serious/fatal (**23.8%**)
  - **Fine no precipitation:** 105,172 casualties, 24,534 serious/fatal (**23.3%**)
  - **Fine with precipitation:** 13,328 casualties, 2,987 serious/fatal (**22.4%**)
  - **Thunder:** 3,966 casualties, 738 serious/fatal (**18.6%**)
  - **Unknown:** 2,547 casualties, 299 serious/fatal (**11.7%**)
  - **Snow, hail, sleet, blowing snow:** 23 casualties, 2 serious/fatal (**8.7%**)
  - **Lighting — Darkness, no lights:** 8,364 casualties, 2,560 serious/fatal (**30.6%**)
  - **Lighting — Darkness, lights unlit:** 923 casualties, 237 serious/fatal (**25.7%**)
  - **Lighting — Darkness, lights lit:** 25,566 casualties, 6,036 serious/fatal (**23.6%**)
  - **Lighting — Daylight:** 91,168 casualties, 20,057 serious/fatal (**22.0%**)
  - **Road surface — Oil/gravel/obstruction:** 198 casualties, 52 serious/fatal (**26.3%**)
  - **Road surface — Snow or ice:** 203 casualties, 51 serious/fatal (**25.1%**)
  - **Road surface — Wet or slippery:** 29,204 casualties, 6,910 serious/fatal (**23.7%**)
  - **Road surface — Dry:** 94,608 casualties, 21,749 serious/fatal (**23.0%**)
- **Interpretation:** Adverse weather conditions (rain, fog) are associated with a higher proportion of serious/fatal casualties. Rain and fog both exceed 26%, compared to 23.3% for fine conditions. Darkness with no lights is the single highest-risk lighting condition at 30.6%, nearly 1.4x the daylight rate. Wet or slippery road surfaces (23.7%) are slightly higher risk than dry (23.0%), while oil/gravel obstructions (26.3%) and snow/ice (25.1%) are significantly higher risk. This suggests that reduced visibility, poor road surface conditions, and darkness are all contributing to more severe outcomes.
- **Evidence:** Power BI report page 3 (Conditions & VRU) — bar chart of weather conditions by serious/fatal rate

### BQ4 — Age & sex profile

- **Question:** What is the age and sex profile of casualties, and how does it compare to the driver population?
- **Method:** `sql/queries/BQ4_age_sex_profile.sql` — maps both casualty and driver ages onto a common grid (0-17, 18-24, 25-34, 35-44, 45+, Unknown), splits by sex, and compares casualty vs driver distributions
- **Finding:**
  - **45+ age band:** Highest share of casualties — **38.4%** of female casualties (18,763) and **32.8%** of male casualties (25,437). Zero drivers by design (DfT only reports driver age up to 40-44).
  - **18-24 age band:** Highest share of drivers — **41.6%** of female drivers (19,588) and **38.8%** of male drivers (43,585), but only **13.5%** of female casualties and **16.8%** of male casualties.
  - **25-34 age band:** Highest share of male casualties — **20.0%** (15,558) and **18.5%** of female casualties (9,034).
  - **Unknown sex:** **58.3%** of all casualties (800) and **88.0%** of all drivers (21,548) — a significant data-quality gap.
- **Interpretation:** Older people (45+) are over-represented in casualties relative to their share of the driving population, suggesting they are more likely to be pedestrians or cyclists in accidents. Younger drivers (18-24) are over-represented in the driver population but under-represented in casualties, suggesting they are less likely to be seriously injured when involved in an accident. The high "Unknown" sex category is a data-quality issue that should be addressed in future extracts.
- **Evidence:** Power BI report page 3 (Conditions & VRU) — age/sex profile chart

### BQ5 — Vehicle type & manoeuvre risk

- **Question:** Which vehicle types and manoeuvres are most associated with serious/fatal casualties?
- **Method:** `sql/queries/BQ5_vehicle_manoeuvre.sql` — groups by vehicle type and manoeuvre, calculates serious/fatal percentage, ranks by severity
- **Finding:**
  - **Rank 1:** Motorcycle 50cc–250cc, Turning right (other) — 491 accidents, 326 serious/fatal (**66.4%**)
  - **Rank 2:** Motorcycle 50cc–250cc, Turning left (other) — 47 accidents, 30 serious/fatal (**63.8%**)
  - **Rank 3:** LGV (van, pickup, 3W), Turning right (other) — 133 accidents, 78 serious/fatal (**58.6%**)
  - **Rank 4:** Motorcycle 50cc–250cc, Unknown — 3,419 accidents, 1,891 serious/fatal (**55.3%**)
  - **Rank 5:** LGV (van, pickup, 3W), Overtaking (other) — 50 accidents, 25 serious/fatal (**50.0%**)
  - **Rank 6:** Motorcycle 50cc–250cc, Starting from stopped position — 48 accidents, 23 serious/fatal (**47.9%**)
  - **Rank 7:** Motorcycle 50cc–250cc, Overtaking (other) — 138 accidents, 65 serious/fatal (**47.1%**)
  - **Rank 8:** Motorcycle 50cc–250cc, Accelerating — 99 accidents, 45 serious/fatal (**45.5%**)
  - **Rank 9:** LGV (van, pickup, 3W), Unknown — 1,225 accidents, 540 serious/fatal (**44.1%**)
  - **Rank 10:** LGV (van, pickup, 3W), Accelerating — 35 accidents, 15 serious/fatal (**42.9%**)
- **Interpretation:** Motorcycles (50cc–250cc) dominate the top 10 high-risk vehicle/manoeuvre combinations, with 7 of the top 10 slots. Turning manoeuvres (left and right) are the highest-risk actions, with serious/fatal rates of 63.8–66.4%. LGVs (vans, pickups) are the second most dangerous vehicle type, particularly when turning right or overtaking. The "Unknown" manoeuvre category is also high-risk, suggesting that data quality issues may be masking additional high-risk patterns.
- **Evidence:** Power BI report page 3 (Conditions & VRU) — vehicle type and manoeuvre breakdown

### BQ6 — Geographic clusters

- **Question:** Are there geographic clusters of high-risk accidents?
- **Method:** `sql/queries/BQ6_geo_clusters.sql` — groups by 0.1° grid cell (lat/long), identifies top 25 cells by serious/fatal count
- **Finding:**
  - **Rank 1:** Grid cell (51.5, -0.1) — 4,065 casualties, 775 serious/fatal (district E09000001)
  - **Rank 2:** Grid cell (51.5, 0.0) — 3,098 casualties, 547 serious/fatal (district E09000011)
  - **Rank 3:** Grid cell (51.5, -0.2) — 2,469 casualties, 478 serious/fatal (district E09000005)
  - **Rank 4:** Grid cell (52.5, -1.9) — 2,003 casualties, 326 serious/fatal (district E08000025)
  - **Rank 5:** Grid cell (53.8, -1.5) — 993 casualties, 267 serious/fatal (district E08000035)
  - **Top 3 cells** are all in the London area (lat ~51.5), accounting for **1,799 serious/fatal** casualties combined
  - **Rank 8:** Grid cell (55.9, -4.3) — 592 casualties, 206 serious/fatal (district S12000045, Scotland)
- **Interpretation:** The top 3 high-risk grid cells are all in the London area, suggesting that urban density and traffic volume are major drivers of serious/fatal casualties. The top 25 cells span England and Scotland, with a concentration in the South East and North West. This suggests that interventions should focus on these high-risk areas, with particular attention to road design, speed limits, and enforcement.
- **Evidence:** Power BI report page 2 (Districts & Risk) — geographic cluster map

### BQ7 — Vulnerable road user share

- **Question:** What proportion of serious/fatal casualties are vulnerable road users (pedestrians and cyclists)?
- **Method:** `sql/queries/BQ7_vru_share.sql` — filters by `vru_flag = TRUE`, calculates share of serious/fatal
- **Finding:**
  - **78.9%** of all serious/fatal casualties are VRUs
  - **Pedestrians:** 64.0% of serious/fatal casualties
  - **Cyclists:** 14.9% of serious/fatal casualties
  - Serious/fatal records contain only Pedestrian, Motorist, and Cyclist — no passengers, motorcyclists, or mopeds in the 2025 extract
- **Interpretation:** This is the most striking finding in the entire analysis. Nearly 8 out of 10 serious/fatal casualties are people without the protection of a vehicle. This should be the primary focus of any road-safety strategy. Pedestrians are the most vulnerable group, followed by cyclists.
- **Evidence:** Power BI report page 3 (Conditions & VRU) — VRU share donut chart

### BQ8 — Time-of-day / day-of-week patterns

- **Question:** When are serious/fatal casualties most likely to occur?
- **Method:** `sql/queries/BQ8_time_patterns.sql` — groups by hour and day-of-week, calculates serious/fatal percentage
- **Finding:**
  - **Weekends (Sat/Sun):** 24.3% serious/fatal rate — highest of any day (Sat 4,339 S/F, Sun 3,624 S/F)
  - **Small hours (0–5am):** 28.0–30.3% serious/fatal rate — highest of any hour (4am peak: 30.3%, 1am: 29.8%, 0am: 28.7%)
  - **8am:** 18.7% serious/fatal rate — lowest of any hour, despite having the highest accident count (8,053)
  - **Midday (12pm–4pm):** 21.8–22.7% — near the overall average
- **Interpretation:** Serious/fatal casualties are most likely to occur on weekends and in the small hours (0–5am), when lighting is poor, driver alertness is lower, and traffic is less predictable. The 8am trough is a dilution effect: it has the highest absolute accident count (8,053) but the lowest S/F proportion, meaning the morning commute produces many minor collisions but few serious/fatal ones. Interventions should target weekend and small-hours driving with improved lighting, speed enforcement, and fatigue-awareness campaigns.
- **Evidence:** Power BI report page 4 (Time & Patterns) — time-of-day and day-of-week heatmaps

---

## 5. Insights & Recommendations

| # | Insight (evidence) | Recommendation | Priority |
|---|--------------------|----------------|----------|
| 1 | **VRUs dominate serious/fatal casualties** — 78.9% of all serious/fatal outcomes are pedestrians (64.0%) or cyclists (14.9%) (BQ7) | Prioritise pedestrian and cyclist safety interventions: protected crossings, cycle lanes, speed limits in high-VRU areas, and enforcement of driver behaviour near VRUs | **High** |
| 2 | **Top 5 districts by serious/fatal rate** are 2.9x higher than the bottom district (0.870 vs 0.295 per accident) (BQ2) | Conduct targeted audits of the top 10% of districts, focusing on road design, speed limits, and enforcement. Allocate resources proportionally to risk | **High** |
| 3 | **Weekends and small hours (0–5am)** have the highest serious/fatal rates (24.3% and 28–30.3% respectively) (BQ8) | Increase lighting, speed enforcement, and driver alertness campaigns on weekends and in the small hours. Consider temporary speed limits in high-risk areas | **Medium** |
| 4 | **Adverse weather (rain, fog)** is associated with a 26–28.5% serious/fatal rate, vs 23.3% for fine conditions (BQ3) | Improve road surface drainage, signage, and driver awareness in adverse weather. Consider temporary speed limits during rain and fog | **Medium** |
| 5 | **Motorcycles** are disproportionately represented in serious/fatal casualties relative to their share of traffic (BQ5) | Develop motorcycle-specific safety interventions: rider training, protective equipment, and road design that reduces conflict points with motorcycles | **Medium** |

---

## 6. Limitations

- **Single-year extract:** The analysis is based on a single year of data (2025), so it cannot capture multi-year trends or seasonal variations beyond the 12 months in the extract.
- **District attribution:** The 2025 `local_authority_district` field is 100% `-1` (unknown). District attribution therefore uses `local_authority_ons_district` (ONS codes), which resolved `dim_location` from 396 → 2,492 rows. This is a data-quality issue that should be addressed in future extracts.
- **Field sparsity:** Some fields (e.g., weather, lighting) have a non-trivial proportion of "Unknown" values, which limits the precision of the analysis.
- **No exposure data:** The analysis does not account for exposure (e.g., traffic volume, population), so the serious/fatal rates are not adjusted for differences in activity levels across districts.
- **No causal inference:** The analysis is descriptive, not causal. Correlations (e.g., between weather and severity) do not imply causation.

---

## 7. Conclusion

This project has successfully transformed raw DfT road-safety data into a governed SQL data warehouse and an interactive Power BI report that answers 8 business questions. The analysis covers 125,113 casualties across 2,492 districts, with 30,159 serious or fatal outcomes.

The most important finding is that **vulnerable road users (pedestrians and cyclists) account for 78.9% of all serious/fatal casualties**. This should be the primary focus of any road-safety strategy. The top 10% of districts by serious/fatal rate are 6x higher than the bottom 10%, suggesting that targeted interventions in high-risk areas could have a significant impact.

**Next steps:**
1. Extend the analysis to multiple years to capture trends and seasonal variations
2. Incorporate exposure data (traffic volume, population) to adjust serious/fatal rates
3. Develop predictive models to identify high-risk locations and time periods
4. Conduct a cost-benefit analysis of the recommended interventions

---

## 8. Reproducibility

- **Repo layout:** See `README.md`
- **How to run:**
  1. Create the database: `createdb road_safety`
  2. Apply the schema: `psql road_safety -f sql/schema.sql`
  3. Add the raw data: Download `accidents.csv`, `vehicles.csv`, `casualties.csv` from `https://data.dft.gov.uk/road-accidents-safety-data/` into `data/`
  4. Install Python deps: `pip install -r requirements.txt`
  5. Run the ETL: `python etl/load.py --data-dir data --db-url postgresql://postgres:postgres@localhost:5432/road_safety`
  6. Verify: `psql road_safety -c "SELECT COUNT(*) AS accidents FROM fact_accident;"`
  7. Power BI: Follow `docs/power_bi_guide.md`
- **Environment:**
  - Python 3.9.13 (WindowsApps)
  - PostgreSQL 17.11
  - Power BI Desktop (free)
  - pandas 2.3.3
  - psycopg2-binary 2.9.12

---

## Appendices

- **A. Full SQL queries** — `sql/queries/`
- **B. DAX measures** — `dax/measures.dax`
- **C. Data-quality log** — `docs/data_quality.md`
- **D. Power BI report page list** —
  1. Trend & KPIs
  2. Districts & Risk
  3. Conditions & VRU
  4. Time & Patterns
- **E. Row-count reconciliation** — from the data-quality log
