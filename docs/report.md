# UK Road Safety Analytics — Final Report

> **Project:** Data Analyst Portfolio Project — Road Safety Analytics
> **Author:** Jake (Third-Year CS Student)
> **Date:** 2026-10-07
> **Data Source:** DfT Road Safety Data (formerly STATS19), 2021–2025 five-year extract
> **Licence:** UK Open Government Licence (OGL v3.0)

---

## 1. Executive Summary

This project transforms raw DfT road-safety data into a governed SQL data warehouse and an interactive Power BI report that answers 11 business questions for a road-safety authority. The analysis covers **652,821 casualties** across **375 districts** over five years (2021–2025), with **137,044 serious or fatal** outcomes (21.0%).

**Headline finding:** Car occupants are the largest serious/fatal category (**37.7%**), followed by **pedestrians (21.2%)** and **cyclists (14.2%)**. Vulnerable road users (pedestrians + cyclists) account for **35.5%** of all serious/fatal casualties. Motorcyclists (all classes) add a further 19.6%, bringing the total for "vulnerable" road users to ~55%. The 2025 data shows a **6.0% year-on-year increase** in serious/fatal casualties (29,296 vs 27,642 in 2024), partly driven by improved coding of e-scooter and powered personal transporter casualties in the September 2026 DfT revision.

**Top recommendation:** Prioritise pedestrian and cyclist safety interventions in the top 10% of districts by serious/fatal rate (led by district S12000034, Scotland, at 0.809 serious/fatal per accident over 5 years), with a focus on the small hours (0–5am) and weekends, where severity share peaks at 26.6–27.9% versus 17.0% at 8am.

---

## 2. Background & Objectives

- **Business owner:** Road-safety authority / local council
- **Problem:** Road-safety authorities need to understand where, when, and to whom serious harm is happening so they can allocate limited resources effectively. Raw DfT data is voluminous and unstructured; it needs to be cleaned, governed, and analysed to produce actionable insights.
- **Objectives:**
  - **O1:** Build a governed SQL data warehouse from raw DfT CSVs
  - **O2:** Answer 11 business questions (BQ1–BQ11) with validated SQL queries
  - **O3:** Create an interactive Power BI report for self-service analysis
  - **O4:** Distil findings into evidence-based insights and recommendations
  - **O5:** Document the full pipeline for reproducibility
- **Scope:** 2021–2025 five-year DfT extract, UK-wide, all casualty types
- **Out of scope:** Exposure-adjusted rates (traffic volume / population), international comparison, predictive modelling

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
- **Visualisation:** Power BI Desktop — see `dax/measures.dax` (16 measures)
- **Data quality:** Refer to `docs/data_quality.md`

---

## 4. Findings

### BQ1 — Casualty trend over time

- **Question:** How do casualties and serious/fatal outcomes vary month-by-month across 2021–2025?
- **Method:** `sql/queries/BQ1_casualty_trend.sql` — groups `fact_casualty` by month via `dim_date`, with month-over-month change via `LAG()`
- **Finding:**
  - Total casualties (5 years): **652,821**
  - Total serious/fatal (5 years): **137,044** (21.0%)
  - Monthly casualties range from **~8,900** (February) to **~11,400** (November)
  - Serious/fatal share is relatively stable across months (19.9%–22.3%)
  - 60 rows returned (5 years × 12 months)
- **Interpretation:** Casualty volumes show a clear seasonal pattern — February is consistently the lowest month, while November is the highest. The serious/fatal share is relatively stable across months, with a slight peak in summer months (June–August). The month-over-month change column reveals recurring seasonal dips in February and spikes in June/July.
- **Evidence:** Power BI report page 1 (Trend & KPIs) — monthly line chart with serious/fatal share overlay

### BQ2 — Highest-risk districts / road classes

- **Question:** Which districts have the highest rate of serious/fatal casualties over 2021–2025?
- **Method:** `sql/queries/BQ2_top_districts.sql` — groups by ONS district code, orders by serious/fatal per accident
- **Finding:**
  - **375 districts** with non-null district attribution (363 after the ≥50-accident reliability floor)
  - Top district (**S12000034**, Scotland): **702** accidents, **568** serious/fatal (**0.809** serious/fatal per accident)
  - Second (**S12000020**, Scotland): **198** accidents, **148** serious/fatal (**0.747**)
  - Third (**S12000026**, Scotland): **464** accidents, **327** serious/fatal (**0.705**)
  - Fourth (**S12000017**, Scotland): **1,190** accidents, **833** serious/fatal (**0.700**)
  - Fifth (**S12000035**, Scotland): **455** accidents, **302** serious/fatal (**0.664**)
  - Range: **0.809** (top) to **~0.13** (bottom) — a **~6x** difference
- **Interpretation:** There is significant variation in serious/fatal rates across districts. The top 5 districts are all in Scotland, suggesting that rural road networks with higher speed limits and fewer traffic calming measures may be a contributing factor. The ~6x difference between the top and bottom districts suggests that local factors (road design, traffic volume, enforcement) are playing a significant role. The 5-year aggregation provides more stable rates than single-year figures.
- **Evidence:** Power BI report page 2 (Districts & Risk) — bar chart of top 20 districts by serious/fatal rate

### BQ3 — Weather / lighting / road-surface effects

- **Question:** How do weather conditions affect the severity of casualties?
- **Method:** `sql/queries/BQ3_conditions.sql` — groups by weather condition, calculates serious/fatal percentage
- **Finding:**
  - **Weather — Fog or mist:** 5,786 casualties, 1,466 serious/fatal (**25.3%**)
  - **Weather — Rain, showers, sleet, hail:** 2,874 casualties, 695 serious/fatal (**24.2%**)
  - **Weather — Fine no precipitation:** 526,489 casualties, 112,661 serious/fatal (**21.4%**)
  - **Weather — Thunder:** 19,525 casualties, 3,428 serious/fatal (**17.6%**)
  - **Lighting — Darkness, no lights:** 40,476 casualties, 11,806 serious/fatal (**29.2%**)
  - **Lighting — Darkness, lights unlit:** 4,772 casualties, 1,217 serious/fatal (**25.5%**)
  - **Lighting — Darkness, lights lit:** 133,173 casualties, 29,178 serious/fatal (**21.9%**)
  - **Lighting — Daylight:** 464,154 casualties, 92,972 serious/fatal (**20.0%**)
  - **Lighting — Twilight:** 10,198 casualties, 1,859 serious/fatal (**18.2%**)
  - **Road surface — Oil/gravel/obstruction:** 1,103 casualties, 251 serious/fatal (**22.8%**)
  - **Road surface — Wet or slippery:** 158,102 casualties, 34,414 serious/fatal (**21.8%**)
  - **Road surface — Dry:** 472,355 casualties, 99,487 serious/fatal (**21.1%**)
- **Interpretation:** Adverse weather conditions (fog, rain) are associated with a higher proportion of serious/fatal casualties. Fog (25.3%) and rain (24.2%) both exceed the fine-conditions rate (21.4%). Darkness with no lights is the single highest-risk lighting condition at 29.2%, nearly 1.5x the daylight rate (20.0%). Wet or slippery road surfaces (21.8%) are slightly higher risk than dry (21.1%), while oil/gravel obstructions (22.8%) are significantly higher risk. This suggests that reduced visibility, poor road surface conditions, and darkness are all contributing to more severe outcomes.
- **Evidence:** Power BI report page 3 (Conditions & VRU) — bar chart of weather conditions by serious/fatal rate

### BQ4 — Age & sex profile

- **Question:** What is the age and sex profile of casualties, and how does it compare to the driver population?
- **Method:** `sql/queries/BQ4_age_sex_profile.sql` — maps both casualty and driver ages onto a common grid (0-17, 18-24, 25-34, 35-44, 45+, Unknown), splits by sex, and compares casualty vs driver distributions
- **Finding:**
  - **45+ age band:** Largest casualty and driver age band — **36.5%** of female casualties (90,730) and **31.8%** of male casualties (126,627); also **36.7%** of female drivers (87,759) and **35.2%** of male drivers (202,576).
  - **25-34 age band:** Second-largest casualty band — **19.5%** of female casualties (48,459) and **21.4%** of male casualties (85,015).
  - **18-24 age band:** **14.2%** of female casualties (35,391) and **17.0%** of male casualties (67,615), but **16.2%** of female drivers (38,783) and **18.6%** of male drivers (106,963).
  - **Unknown sex/age:** **6,433** casualties (1.0% of all) and **122,370** drivers — a significant data-quality gap. The largest unknown group is "Unknown age + Unknown sex" (105,447 drivers).
- **Interpretation:** Older people (45+) are the largest casualty and driver age band, well-represented in both populations. Younger drivers (18-24) are over-represented in the driver population relative to their casualty share, suggesting they are less likely to be seriously injured when involved in an accident. The high "Unknown" sex/age category for drivers (122,370) is a significant data-quality issue that should be addressed in future extracts.
- **Evidence:** Power BI report page 3 (Conditions & VRU) — age/sex profile chart

### BQ5 — Vehicle type & manoeuvre risk

- **Question:** Which vehicle types and manoeuvres are most associated with serious/fatal casualties?
- **Method:** `sql/queries/BQ5_vehicle_manoeuvre.sql` — groups by vehicle type and manoeuvre, calculates serious/fatal percentage, ranks by severity
- **Finding:**
  - **Rank 1:** Motorcycle >500cc, U-turn — 40 accidents, 25 serious/fatal (**62.5%**)
  - **Rank 2:** Motorcycle >500cc, Overtaking offside — 2,189 accidents, 1,362 serious/fatal (**62.2%**)
  - **Rank 3:** Motorcycle >500cc, Changing lane left — 191 accidents, 110 serious/fatal (**57.6%**)
  - **Rank 4:** Motorcycle >500cc, Going ahead — 14,537 accidents, 8,279 serious/fatal (**57.0%**)
  - **Rank 5:** Motorcycle >500cc, Changing lane right — 168 accidents, 89 serious/fatal (**53.0%**)
  - **Rank 6:** Motorcycle >500cc, Overtaking nearside — 462 accidents, 240 serious/fatal (**51.9%**)
  - **Rank 7:** Motorcycle 125–500cc, Overtaking offside — 648 accidents, 312 serious/fatal (**48.1%**)
  - **Rank 8:** Electric motorcycle, Going ahead — 1,238 accidents, 596 serious/fatal (**48.1%**)
- **Interpretation:** Motorcycles (>500cc) dominate the top 8 high-risk vehicle/manoeuvre combinations, with 6 of the top 8 slots. Overtaking and lane-changing manoeuvres are the highest-risk actions, with serious/fatal rates of 51.9–62.2%. The "Going ahead" manoeuvre (14,537 accidents) is the most common high-risk action, suggesting that straight-ahead travel at speed is a major risk factor for motorcyclists. Electric motorcycles also appear in the top 8, reflecting the growing presence of powered two-wheelers in the 2025 DfT revision.
- **Evidence:** Power BI report page 3 (Conditions & VRU) — vehicle type and manoeuvre breakdown

### BQ6 — Geographic clusters

- **Question:** Are there geographic clusters of high-risk accidents?
- **Method:** `sql/queries/BQ6_geo_clusters.sql` — groups by 0.1° grid cell (lat/long), identifies top 25 cells by serious/fatal count
- **Finding:**
  - **Rank 1:** Grid cell (51.5, -0.2) — 17,506 casualties, 3,027 serious/fatal (district E09000005)
  - **Rank 2:** Grid cell (51.5, -0.1) — 15,913 casualties, 2,804 serious/fatal (district E09000001)
  - **Rank 3:** Grid cell (52.5, -1.9) — 12,313 casualties, 1,878 serious/fatal (district E08000025)
  - **Rank 4:** Grid cell (51.4, -0.1) — 11,660 casualties, 1,858 serious/fatal (district E09000006)
  - **Rank 5:** Grid cell (51.5, 0.0) — 11,995 casualties, 1,674 serious/fatal (district E09000011)
  - **Top 5 cells** are all in the London area (lat ~51.4–51.5), accounting for **11,241 serious/fatal** casualties combined
- **Interpretation:** The top 5 high-risk grid cells are all in the London area, suggesting that urban density and traffic volume are major drivers of serious/fatal casualties. The 5-year aggregation provides more stable counts than single-year figures. This suggests that interventions should focus on these high-risk urban areas, with particular attention to road design, speed limits, and enforcement.
- **Evidence:** Power BI report page 2 (Districts & Risk) — geographic cluster map

### BQ7 — Vulnerable road user share

- **Question:** What proportion of serious/fatal casualties are vulnerable road users (pedestrians and cyclists)?
- **Method:** `sql/queries/BQ7_vru_share.sql` — filters by `vru_flag = TRUE`, calculates share of serious/fatal
- **Finding:**
  - **35.5%** of all serious/fatal casualties (48,595 of 137,044) are VRUs (pedestrians + cyclists)
  - **Pedestrians:** 21.2% of serious/fatal casualties (29,092)
  - **Cyclists:** 14.2% of serious/fatal casualties (19,503)
  - **Car occupants** are the single largest serious/fatal category at **37.7%** (51,624)
  - **Motorcyclists (all classes):** a further **19.6%** (26,972), bringing the total for "vulnerable" road users (VRUs + motorcyclists + mopeds + PPTs) to **~57.2%** (78,443)
  - VRU share is stable across the five years: 36.0% (2021), 35.3% (2022), 35.6% (2023), 34.6% (2024), 35.8% (2025)
- **Interpretation:** Car occupants are the largest serious/fatal category, but vulnerable road users collectively account for more than half of all serious/fatal casualties. Pedestrians are the most vulnerable group, followed by cyclists. The VRU share is remarkably stable across the five years (34.6–36.0%), indicating a persistent structural risk rather than a one-off phenomenon. This should be a primary focus of any road-safety strategy.
- **Evidence:** Power BI report page 3 (Conditions & VRU) — VRU share donut chart

### BQ8 — Time-of-day / day-of-week patterns

- **Question:** When are serious/fatal casualties most likely to occur?
- **Method:** `sql/queries/BQ8_time_patterns.sql` — groups by hour and day-of-week, calculates serious/fatal percentage
- **Finding:**
  - **Sunday:** 77,509 casualties, 17,893 serious/fatal (**23.1%**) — highest of any day
  - **Saturday:** 93,624 casualties, 20,918 serious/fatal (**22.3%**) — second-highest day
  - **3am:** 4,563 casualties, 1,274 serious/fatal (**27.9%**) — highest of any hour
  - **0am:** 11,002 casualties, 2,923 serious/fatal (**26.6%**) — second-highest hour
  - **22:00:** 19,611 casualties, 4,837 serious/fatal (**24.7%**) — third-highest hour
  - **8am:** 39,833 casualties, 6,760 serious/fatal (**17.0%**) — lowest of any hour, despite the 6th-highest casualty count
  - **4pm:** 54,616 casualties, 10,986 serious/fatal (**20.1%**) — near the overall average
- **Interpretation:** Serious/fatal casualties are most likely to occur on weekends and in the small hours (0–5am), when lighting is poor, driver alertness is lower, and traffic is less predictable. The 8am trough is a dilution effect: it has a high absolute casualty count (39,833, 6th of 24 hours) but the lowest S/F proportion, meaning the morning commute produces many minor collisions but few serious/fatal ones. Interventions should target weekend and small-hours driving with improved lighting, speed enforcement, and fatigue-awareness campaigns.
- **Evidence:** Power BI report page 4 (Time & Patterns) — time-of-day and day-of-week heatmaps

### BQ9 — Annual trend & year-on-year change

- **Question:** How do casualties and serious/fatal outcomes change year-on-year across 2021–2025?
- **Method:** `sql/queries/BQ9_annual_trend.sql` — groups by year, calculates YoY change and a 12-month moving average of serious/fatal
- **Finding:**
  - **2021:** 128,209 casualties, 24,921 serious/fatal (**19.4%**)
  - **2022:** 135,480 casualties, 27,531 serious/fatal (**20.3%**) — **+2,610 (+10.5%)** YoY
  - **2023:** 132,977 casualties, 27,654 serious/fatal (**20.8%**) — +123 (+0.4%) YoY
  - **2024:** 128,272 casualties, 27,642 serious/fatal (**21.5%**) — −12 (0.0%) YoY
  - **2025:** 127,883 casualties, 29,296 serious/fatal (**22.9%**) — **+1,654 (+6.0%)** YoY
  - The serious/fatal **share** of all casualties rises every year: 19.4% → 20.3% → 20.8% → 21.5% → 22.9%
- **Interpretation:** Total casualty volumes are broadly stable (128k–135k per year), but the serious/fatal share is rising steadily — from 19.4% in 2021 to 22.9% in 2025. The 2025 jump (+6.0% YoY) is partly driven by the September 2026 DfT revision, which improved vehicle/road-user coding to identify powered personal transporters (e-scooters) and introduced new vehicle_type codes (22/23/33). Even accounting for the coding change, the underlying trend is a rising severity share, suggesting that the mix of casualties is shifting toward more vulnerable road users.
- **Evidence:** Power BI report page 1 (Trend & KPIs) — annual bar chart with YoY change and 12-month moving average

### BQ10 — Seasonality index

- **Question:** Which months are over- or under-represented in serious/fatal casualties relative to the annual average?
- **Method:** `sql/queries/BQ10_seasonality.sql` — calculates a seasonality index (month S/F ÷ monthly average S/F × 100) for each month across the five years
- **Finding:**
  - **February:** lowest month — 8,857 serious/fatal, seasonality index **81.2** (18.8% below average)
  - **June:** highest month — 12,662 serious/fatal, seasonality index **109.0** (9.0% above average)
  - **July:** second-highest — 12,678 serious/fatal, seasonality index **107.1**
  - **January:** 9,412 serious/fatal, index **86.1**
  - **December:** 10,876 serious/fatal, index **99.2** (near average)
- **Interpretation:** There is a clear seasonal pattern: winter months (January–February) are under-represented in serious/fatal casualties, while summer months (June–July) are over-represented. This is consistent with the BQ1 finding that February is the lowest month and November the highest in total casualties. The seasonality index provides a normalised measure that can be used to adjust for seasonal variation in predictive models.
- **Evidence:** Power BI report page 1 (Trend & KPIs) — seasonality index bar chart

### BQ11 — Inflection points & anomalies

- **Question:** Are there months where serious/fatal casualties deviate significantly from the trailing 12-month average?
- **Method:** `sql/queries/BQ11_inflection_points.sql` — calculates the trailing 12-month moving average and flags months where the actual S/F count deviates by more than ±10%
- **Finding:**
  - **Recurring February dips:** 2022 (−16.9%), 2023 (−14.1%), 2024 (−15.2%), 2025 (−14.8%) — February is consistently 14–17% below the trailing 12-month average
  - **June/July spikes:** 2022 (+11.2%), 2023 (+12.4%), 2024 (+15.7%), 2025 (+11.8%) — June and July are consistently 11–16% above the trailing 12-month average
  - **No other months** consistently exceed the ±10% threshold
- **Interpretation:** The recurring February dips and June/July spikes are the most significant seasonal anomalies in the data. These are not one-off events but persistent patterns that recur every year. This suggests that seasonal factors (weather, daylight hours, holiday travel) are driving the variation, and that interventions should be timed to target the high-risk summer months.
- **Evidence:** Power BI report page 1 (Trend & KPIs) — inflection point scatter plot with trailing 12-month average

---

## 5. Insights & Recommendations

| # | Insight (evidence) | Recommendation | Priority |
|---|--------------------|----------------|----------|
| 1 | **Vulnerable road users account for ~57.2% of serious/fatal casualties** — car occupants are the largest single category (37.7%), but VRUs (pedestrians 21.2% + cyclists 14.2%) plus motorcyclists (19.6%) together make up the majority (BQ7 narrow = 35.5%) | Prioritise pedestrian and cyclist safety interventions: protected crossings, cycle lanes, speed limits in high-VRU areas, and enforcement of driver behaviour near VRUs. Also develop motorcycle-specific interventions: rider training, protective equipment, and road design that reduces conflict points | **High** |
| 2 | **Top 5 districts by serious/fatal rate** are ~6x higher than the bottom district (0.809 vs ~0.13 per accident) (BQ2) | Conduct targeted audits of the top 10% of districts, focusing on road design, speed limits, and enforcement. Allocate resources proportionally to risk | **High** |
| 3 | **Weekends and small hours (0–5am)** have the highest serious/fatal rates (23.1% on Sundays and 27.9% at 3am) (BQ8) | Increase lighting, speed enforcement, and driver alertness campaigns on weekends and in the small hours. Consider temporary speed limits in high-risk areas | **Medium** |
| 4 | **Adverse weather (fog, rain)** is associated with a 24–25.3% serious/fatal rate, vs 21.4% for fine conditions (BQ3) | Improve road surface drainage, signage, and driver awareness in adverse weather. Consider temporary speed limits during rain and fog | **Medium** |
| 5 | **Serious/fatal share is rising** — from 19.4% in 2021 to 22.9% in 2025, with a +6.0% YoY jump in 2025 (BQ9) | Monitor the trend closely and investigate whether the 2025 jump is driven by the DfT coding revision or a genuine increase in severity. Consider targeted interventions for the rising VRU share | **High** |

---

## 6. Limitations

- **District attribution:** The 2025 `local_authority_district` field is 100% `-1` (unknown). District attribution therefore uses `local_authority_ons_district` (ONS codes), which resolved `dim_location` from 396 → 2,492 rows. This is a data-quality issue that should be addressed in future extracts.
- **Field sparsity:** Some fields (e.g., weather, lighting) have a non-trivial proportion of "Unknown" values, which limits the precision of the analysis.
- **No exposure data:** The analysis does not account for exposure (e.g., traffic volume, population), so the serious/fatal rates are not adjusted for differences in activity levels across districts.
- **No causal inference:** The analysis is descriptive, not causal. Correlations (e.g., between weather and severity) do not imply causation.
- **DfT coding revision:** The September 2026 DfT revision improved vehicle/road-user coding to identify powered personal transporters (e-scooters) and introduced new vehicle_type codes (22/23/33). This may partially explain the 2025 serious/fatal jump (+6.0% YoY) and should be considered when interpreting year-on-year trends.

---

## 7. Conclusion

This project has successfully transformed raw DfT road-safety data into a governed SQL data warehouse and an interactive Power BI report that answers 11 business questions. The analysis covers **652,821 casualties** across **375 districts** over five years (2021–2025), with **137,044 serious or fatal** outcomes (21.0%).

The most important finding is that **vulnerable road users collectively account for ~57.2% of all serious/fatal casualties** — car occupants are the largest single category (37.7%), but VRUs (pedestrians 21.2% + cyclists 14.2%) plus motorcyclists (19.6%) together make up the majority. The serious/fatal share is also rising steadily, from 19.4% in 2021 to 22.9% in 2025. The top 5 districts by serious/fatal rate are ~6x higher than the bottom district, suggesting that targeted interventions in high-risk areas could have a significant impact.

**Next steps:**
1. Incorporate exposure data (traffic volume, population) to adjust serious/fatal rates
2. Develop predictive models to identify high-risk locations and time periods
3. Conduct a cost-benefit analysis of the recommended interventions
4. Extend the analysis to include IMD (Index of Multiple Deprivation) data to explore inequality in road-safety outcomes

---

## 8. Reproducibility

- **Repo layout:** See `README.md`
- **How to run:**
  1. Create the database: `createdb road_safety`
  2. Apply the schema: `psql road_safety -f sql/schema.sql`
  3. Add the raw data: Download the 5-year extracts from DfT into `data/`:
     - `https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-last-5-years.csv` → `accidents.csv`
     - `https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-last-5-years.csv` → `vehicles.csv`
     - `https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-casualty-last-5-years.csv` → `casualties.csv`
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
  1. Trend & KPIs (BQ1, BQ9, BQ10, BQ11)
  2. Districts & Risk (BQ2, BQ6)
  3. Conditions & VRU (BQ3, BQ4, BQ5, BQ7)
  4. Time & Patterns (BQ8)
- **E. Row-count reconciliation** — from the data-quality log
