# UK Road Safety Analytics — Final Report

> **Project:** Data Analyst Portfolio Project — Road Safety Analytics
> **Author:** Jake (Final-Year CS Student)
> **Date:** 2026-10-07
> **Data Source:** DfT Road Safety Data (formerly STATS19), 2021–2025 five-year extract
> **Licence:** UK Open Government Licence (OGL v3.0)

---

## 1. Executive Summary

This project transforms raw DfT road-safety data into a governed SQL data warehouse and an interactive Power BI report that answers 14 business questions for a road-safety authority. The analysis covers **652,821 casualties** across **370 districts** over five years (2021–2025), with **137,044 serious or fatal** outcomes (21.0%). Phase B adds exposure-adjusted rates using DfT road traffic estimates (TRA), vehicle licensing (VEH0101), and published casualty rates (RAS0201) to normalise serious/fatal counts by traffic volume and vehicle population.

**Headline finding:** Car occupants are the largest serious/fatal category (**37.7%**), followed by **pedestrians (21.2%)** and **cyclists (14.2%)**. Vulnerable road users (pedestrians + cyclists) account for **35.5%** of all serious/fatal casualties. Motorcyclists (all classes) add a further 19.7%, and e-scooter, e-motorcycle and mobility-scooter users 2.1%, bringing the total for vulnerable road users and riders to **~57.2%**. The 2025 data shows a **6.0% year-on-year increase** in serious/fatal casualties (29,296 vs 27,642 in 2024). The serious/fatal share rises every year (19.4% → 22.9%), and still rises on DfT's adjusted severity (20.6% → 23.4%), so it is not only a change in how police record injuries.

**Top recommendation:** Prioritise pedestrian and cyclist safety interventions in the top 10% of districts by serious/fatal rate (led by district S12000034, Scotland, at 0.809 serious/fatal per accident over 5 years), with a focus on the small hours (0–5am) and weekends, where severity share peaks at 26.6–27.9% versus 17.0% at 8am.

---

## 2. Background & Objectives

- **Business owner:** Road-safety authority / local council
- **Problem:** Road-safety authorities need to understand where, when, and to whom serious harm is happening so they can allocate limited resources effectively. Raw DfT data is voluminous and unstructured; it needs to be cleaned, governed, and analysed to produce actionable insights.
- **Objectives:**
  - **O1:** Build a governed SQL data warehouse from raw DfT CSVs
  - **O2:** Answer 14 business questions (BQ1–BQ14) with validated SQL queries
  - **O3:** Create an interactive Power BI report for self-service analysis
  - **O4:** Distil findings into evidence-based insights and recommendations
  - **O5:** Document the full pipeline for reproducibility
- **Scope:** 2021–2025 five-year DfT extract, Great Britain (STATS19 excludes Northern Ireland), all casualty types
- **Out of scope:** International comparison, predictive modelling, IMD inequality analysis (Phase C)

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
- **Exposure data (Phase B):** DfT Road Traffic Estimates (TRA0201/0202/0204/8904/8905/0401/0412), Vehicle Licensing (VEH0101), Published Casualty Rates (RAS0201), Cost of Prevention (RAS4001) — see `data/exposure/` and `etl/load_exposure.py`
- **Visualisation:** Power BI Desktop — see `dax/measures.dax` (21 measures)
- **Data quality:** Refer to `docs/data_quality.md`

---

## 4. Findings

### BQ1 — Casualty trend over time

- **Question:** How do casualties and serious/fatal outcomes vary month-by-month across 2021–2025?
- **Method:** `sql/queries/BQ1_casualty_trend.sql` — groups `fact_casualty` by month via `dim_date`, with month-over-month change via `LAG()`
- **Finding:**
  - Total casualties (5 years): **652,821**
  - Total serious/fatal (5 years): **137,044** (21.0%)
  - Monthly casualties range from **6,513** (February 2021, during COVID restrictions) to **12,556** (November 2021); pooled over five years, June is the busiest month (59,281) and February the quietest (44,193)
  - Serious/fatal share by individual month ranges from 17.9% to 24.0%; pooled by month-of-year it is stable (19.9%–22.3%, peaking in August)
  - 60 rows returned (5 years × 12 months)
- **Interpretation:** Casualty volumes show a clear seasonal pattern — February is consistently the lowest month, and late spring to autumn (May–November) the busiest. The serious/fatal share is relatively stable across months, with a slight peak in summer (June–August). The month-over-month change column reveals recurring seasonal dips in February.
- **Evidence:** Power BI report page 1 (Trend & KPIs) — monthly line chart with serious/fatal share overlay

### BQ2 — Highest-risk districts / road classes

- **Question:** Which districts have the highest rate of serious/fatal casualties over 2021–2025?
- **Method:** `sql/queries/BQ2_top_districts.sql` — groups by ONS district code, orders by serious/fatal per accident
- **Finding:**
  - **370 districts** with non-null district attribution (369 after the ≥50-accident reliability floor)
  - Top district (**S12000034**, Scotland): **702** accidents, **568** serious/fatal (**0.809** serious/fatal per accident)
  - Second (**S12000020**, Scotland): **198** accidents, **148** serious/fatal (**0.747**)
  - Third (**S12000026**, Scotland): **464** accidents, **327** serious/fatal (**0.705**)
  - Fourth (**S12000017**, Scotland): **1,190** accidents, **833** serious/fatal (**0.700**)
  - Fifth (**S12000035**, Scotland): **455** accidents, **302** serious/fatal (**0.664**)
  - Range: **0.809** (top) to **0.123** (bottom, E09000010; the Heathrow pseudo-code `EHEATHROW` is lower still at 0.109) — a **~6.6x** difference
  - Note: the metric is serious/fatal *casualties* per accident, so it can exceed 1 and partly reflects how many people each collision involves
- **Interpretation:** There is significant variation in serious/fatal rates across districts. The top 5 districts are all in Scotland, suggesting that rural road networks with higher speed limits and fewer traffic calming measures may be a contributing factor. The ~6x difference between the top and bottom districts suggests that local factors (road design, traffic volume, enforcement) are playing a significant role. The 5-year aggregation provides more stable rates than single-year figures.
- **Evidence:** Power BI report page 2 (Districts & Risk) — bar chart of top 20 districts by serious/fatal rate

### BQ3 — Weather / lighting / road-surface effects

- **Question:** How do weather conditions affect the severity of casualties?
- **Method:** `sql/queries/BQ3_conditions.sql` — groups by weather condition, calculates serious/fatal percentage
- **Finding:**
  - **Weather — Fine + high winds:** 5,786 casualties, 1,466 serious/fatal (**25.3%**)
  - **Weather — Fog or mist:** 2,874 casualties, 695 serious/fatal (**24.2%**)
  - **Weather — Raining + high winds:** 6,871 casualties, 1,563 serious/fatal (**22.7%**)
  - **Weather — Fine no high winds:** 526,489 casualties, 112,661 serious/fatal (**21.4%**)
  - **Weather — Raining no high winds:** 72,689 casualties, 14,971 serious/fatal (**20.6%**)
  - **Weather — Snowing no high winds:** 2,352 casualties, 451 serious/fatal (**19.2%**)
  - **Weather — Other:** 19,525 casualties, 3,428 serious/fatal (**17.6%**)
  - **Lighting — Darkness, no lights:** 40,476 casualties, 11,806 serious/fatal (**29.2%**)
  - **Lighting — Darkness, lights unlit:** 4,772 casualties, 1,217 serious/fatal (**25.5%**)
  - **Lighting — Darkness, lights lit:** 133,173 casualties, 29,178 serious/fatal (**21.9%**)
  - **Lighting — Daylight:** 464,154 casualties, 92,972 serious/fatal (**20.0%**)
  - **Lighting — Darkness, lighting unknown:** 10,198 casualties, 1,859 serious/fatal (**18.2%**)
  - **Road surface — Flood over 3cm deep:** 1,103 casualties, 251 serious/fatal (**22.8%**)
  - **Road surface — Wet or damp:** 158,102 casualties, 34,414 serious/fatal (**21.8%**)
  - **Road surface — Dry:** 472,355 casualties, 99,487 serious/fatal (**21.1%**)
  - **Road surface — Frost or ice:** 8,528 casualties, 1,673 serious/fatal (**19.6%**)
  - **Road surface — Snow:** 1,696 casualties, 328 serious/fatal (**19.3%**)
- **Interpretation:** Weather has little effect on severity. Fog (24.2%) and high winds (22.7–25.3%) are somewhat above fine conditions (21.4%), but these are small groups; ordinary rain (20.6%), snow (19.2%), frost/ice (19.6%) and snow-covered roads (19.3%) are all *below* the fine/dry rate, consistent with drivers slowing down in bad conditions. Lighting matters far more: darkness with no street lights is the single highest-risk condition at 29.2%, nearly 1.5x the daylight rate (20.0%). Flooded roads (22.8%) are slightly higher risk than dry (21.1%), but on very small numbers.
- **Correction (2026-10-12):** an earlier version of this section used a wrong code table, which labelled rain as "Fine with precipitation" (and omitted it), fog as "Rain", and high winds as "Fog". The conclusion that adverse weather drives severity did not survive the fix.
- **Evidence:** Power BI report page 3 (Conditions & VRU) — bar chart of weather conditions by serious/fatal rate

### BQ4 — Age & sex profile

- **Question:** What is the age and sex profile of casualties, and how does it compare to the driver population?
- **Method:** `sql/queries/BQ4_age_sex_profile.sql` — maps both casualty and driver ages onto a common grid whose edges match the DfT driver bands (0-15, 16-25, 26-35, 36-45, 46+, Unknown), splits by sex, and compares casualty vs driver distributions
- **Finding:**
  - **46+ age band:** Largest casualty and driver age band — **35.1%** of female casualties (87,318) and **30.5%** of male casualties (121,387); also **36.7%** of female drivers (87,759) and **35.2%** of male drivers (202,576).
  - **26-35 age band:** **19.2%** of female casualties (47,823) and **21.1%** of male casualties (83,863); **22.9%** of female drivers (54,814) and **21.9%** of male drivers (125,918).
  - **16-25 age band:** **19.1%** of female casualties (47,337) and **22.7%** of male casualties (90,321), but only **16.2%** of female drivers (38,783) and **18.6%** of male drivers (106,963).
  - **0-15 age band:** **9.3%** of female and **8.5%** of male casualties (23,232 and 33,999), almost all as pedestrians, cyclists or passengers.
  - **Unknown sex:** **6,433** casualties (1.0% of all) and **122,370** drivers; **142,240** drivers have no age band. The largest unknown group is "Unknown age + Unknown sex" (105,447 drivers) — a significant data-quality gap.
- **Interpretation:** Older people (46+) are the largest casualty and driver age band. Young people (16-25) are *over*-represented among casualties relative to their share of drivers in collisions (22.7% vs 18.6% for males), consistent with the known higher risk of young road users. Casualties include passengers and pedestrians, so this is a comparison of populations, not a per-driver injury rate. The high "Unknown" sex/age category for drivers is a significant data-quality issue that should be addressed in future extracts.
- **Correction (2026-10-12):** an earlier version used a grid whose bands did not line up (casualties 18-24 vs drivers 16-25), which reversed the young-driver conclusion. Age 0 (under one year old) was also wrongly treated as unknown; it is now kept (929 casualties).
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
- **Method:** `sql/queries/BQ6_geo_clusters.sql` — groups each collision's own coordinates (`fact_accident.lat/long`) into 0.1° grid cells, identifies top 25 cells by serious/fatal count
- **Finding:**
  - **Rank 1:** Grid cell (51.5, -0.1) — 20,950 casualties, 3,819 serious/fatal (mainly E09000028, Southwark)
  - **Rank 2:** Grid cell (51.5, -0.2) — 14,865 casualties, 2,553 serious/fatal (mainly E09000033, Westminster)
  - **Rank 3:** Grid cell (51.5, 0.0) — 11,108 casualties, 1,575 serious/fatal (mainly E09000030, Tower Hamlets)
  - **Rank 4:** Grid cell (51.6, -0.1) — 10,954 casualties, 1,352 serious/fatal (mainly E09000014, Haringey)
  - **Rank 5:** Grid cell (51.4, -0.1) — 8,442 casualties, 1,226 serious/fatal (mainly E09000008, Croydon)
  - **Rank 6:** Grid cell (52.5, -1.9) — 7,631 casualties, 1,119 serious/fatal (mainly E08000025, Birmingham), the top cell outside London
  - **Top 5 cells** are all in London, accounting for **10,525 serious/fatal** casualties combined
- **Correction (2026-10-12):** an earlier version gridded `dim_location` coordinates, which hold only one representative point per district/road-class group, not each collision's location. The ETL now stores per-collision coordinates on `fact_accident`.
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
  - **Motorcyclists (all classes, incl. unknown cc):** a further **19.7%** (27,031); e-scooter, e-motorcycle and mobility-scooter users add **2.1%** (2,817), bringing the total for vulnerable road users and riders to **~57.2%** (78,443)
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
- **Interpretation:** Total casualty volumes are broadly stable (128k–135k per year), but the serious/fatal share is rising steadily — from 19.4% in 2021 to 22.9% in 2025. Part of any rise in recorded severity comes from police forces moving to injury-based reporting (CRASH), so the same check was run on DfT's adjusted severity (`casualty_adjusted_severity_serious` + fatal): the share still rises, from 20.6% (2021) to 23.4% (2025). Fatalities themselves fell from 1,711 (2022) to 1,538 (2025), so the rise is in serious injuries.
- **Evidence:** Power BI report page 1 (Trend & KPIs) — annual bar chart with YoY change and 12-month moving average

### BQ10 — Seasonality index

- **Question:** Which months are over- or under-represented in serious/fatal casualties relative to the annual average?
- **Method:** `sql/queries/BQ10_seasonality.sql` — calculates a seasonality index (month S/F ÷ monthly average S/F × 100) for each month, pooled across the five years
- **Finding:**
  - **February:** lowest month — 8,857 serious/fatal, seasonality index **77.6** (22.4% below average)
  - **July:** highest month — 12,678 serious/fatal, seasonality index **111.0**
  - **June:** second-highest — 12,662 serious/fatal, index **110.9**; August 108.2
  - **January:** 9,940 serious/fatal, index **87.0**
  - **December:** 11,057 serious/fatal, index **96.8**
- **Correction (2026-10-12):** an earlier version of the query indexed *all* casualties (Feb 81.2, Jun 109.0) while the report described serious/fatal. The query now returns both (`seasonality_index` on S/F, `total_casualty_index` on all).
- **Interpretation:** There is a clear seasonal pattern: winter months (January–March) are under-represented in serious/fatal casualties, while summer months (May–September, peaking June–July) are over-represented. This is consistent with the BQ1 finding that February is the lowest month. The seasonality index provides a normalised measure that can be used to adjust for seasonal variation in predictive models.
- **Evidence:** Power BI report page 1 (Trend & KPIs) — seasonality index bar chart

### BQ11 — Inflection points & anomalies

- **Question:** Are there months where serious/fatal casualties deviate significantly from the trailing 12-month average?
- **Method:** `sql/queries/BQ11_inflection_points.sql` — calculates the trailing 12-month moving average and flags months where the actual S/F count deviates by more than ±10%
- **Finding:**
  - **Recurring February dips:** 2022 (−14.1%), 2023 (−16.9%), 2024 (−16.0%), 2025 (−15.4%) — February is consistently 14–17% below the trailing 12-month average, every year
  - **Summer spikes are not consistent:** flagged months are July 2022 (+12.6%), June and July 2023 (+15.7%, +12.5%), June 2024 (+11.4%) and May 2025 (+11.5%); June 2022 (+3.6%), July 2024 (+3.9%) and June/July 2025 (+9.9%, +8.2%) stay under the threshold
  - **Other flagged months:** March 2023 (−13.8%), April 2023 (−10.3%), May 2023 (+11.2%), March 2024 (−10.5%) — 13 flagged months in total
- **Interpretation:** The February dip is the only anomaly that recurs every year. Summer months usually run above average, but by how much varies year to year, so a summer peak should be expected without assuming a fixed size. Seasonal factors (daylight hours, leisure travel, more cyclists and motorcyclists in summer) are the likely drivers.
- **Evidence:** Power BI report page 1 (Trend & KPIs) — inflection point scatter plot with trailing 12-month average

### BQ12 — Serious/fatal rate per 100M vehicle-km by road class

- **Question:** How does the serious/fatal rate per unit of traffic exposure vary by road class?
- **Method:** `sql/queries/BQ12_sf_per_100m_km_by_road_class.sql` — maps each S/F casualty to TRA0202's road classes (first road class + urban/rural), joins `exposure_vehicle_km` (TRA0202 road-class km), and divides each class's casualties by that class's traffic
- **Finding:**
  - **Minor Roads (Urban):** highest rate — **9.11** S/F per 100M km (2025)
  - **Urban 'A' Roads:** **8.71** per 100M km
  - **Minor Roads (Rural):** **6.82** per 100M km
  - **All Roads:** **5.31** per 100M km
  - **Rural 'A' Roads:** **3.63** per 100M km
  - **Motorway (incl. A(M)):** lowest — **0.77** per 100M km
  - 30 rows returned (5 years × 6 road classes)
- **Correction (2026-10-12):** an earlier version divided the *national* S/F total by each road class's traffic, so the class with the least traffic (motorways) looked most dangerous. That ranking was an artefact.
- **Interpretation:** Per kilometre driven, motorways are by far the safest roads (about 12x safer than minor urban roads), matching DfT's own published finding: they separate traffic, have no at-grade junctions, and no pedestrians or cyclists. Urban roads carry the highest risk per km, where vehicles mix with pedestrians and cyclists at junctions. The All Roads rate (5.31) is the most appropriate for cross-year comparison as it captures the full traffic mix.
- **Evidence:** Power BI report page 5 (Exposure & Rates) — bar chart of S/F rate by road class

### BQ13 — Serious/fatal rate per 100K licensed vehicles (national)

- **Question:** How does the serious/fatal rate per licensed vehicle change over time?
- **Method:** `sql/queries/BQ13_sf_per_100k_vehicles.sql` — joins national S/F counts with `exposure_licensed_vehicles` (VEH0101 Great Britain total, matching STATS19's coverage), calculates S/F per 100K vehicles
- **Finding:**
  - **2021:** 63.8 per 100K vehicles
  - **2022:** 69.8 per 100K vehicles
  - **2023:** 69.3 per 100K vehicles
  - **2024:** 68.5 per 100K vehicles
  - **2025:** **71.5** per 100K vehicles (highest)
- **Correction (2026-10-12):** an earlier version used the UK fleet (which includes Northern Ireland) against GB-only casualties, understating every year; its 2022–2024 values also did not match the data.
  - 5 rows returned (one per year)
- **Interpretation:** The serious/fatal rate per 100K licensed vehicles rose from 63.8 (2021) to 71.5 (2025), a **12.1% increase** over five years — mostly a jump in 2022 (as traffic recovered after COVID restrictions) and in 2025, with a slight dip in between. The rise in serious/fatal casualties is not simply driven by growth in the vehicle fleet; part of it may reflect changes in injury recording (see BQ9).
- **Evidence:** Power BI report page 5 (Exposure & Rates) — line chart of S/F per 100K vehicles

### BQ14 — Serious/fatal rate per 100M vehicle-km by local authority

- **Question:** Which local authorities have the highest serious/fatal rate per unit of traffic exposure?
- **Method:** `sql/queries/BQ14_sf_per_100m_km_by_district.sql` — joins `fact_casualty` (S/F by district) with `exposure_vehicle_km` (TRA8904 LA-level km), calculates S/F per 100M vehicle-km
- **Finding:**
  - **186 local authorities** with both casualty and exposure data
  - Top districts are predominantly **Inner London boroughs** (E09 prefix), with rates of **17–45** per 100M km
  - 186 rows returned
- **Interpretation:** Inner London boroughs dominate the top of the exposure-adjusted ranking, reflecting the combination of high casualty counts and relatively moderate traffic volumes (due to congestion and lower average speeds). This contrasts with the BQ2 ranking (S/F per accident), which was dominated by Scottish districts — the exposure adjustment reveals a different risk profile. London's high per-km rates suggest that urban density, mixed traffic, and VRU exposure are key drivers of serious harm per unit of traffic.
- **Evidence:** Power BI report page 5 (Exposure & Rates) — bar chart of top 20 LAs by S/F per 100M km

---

## 5. Insights & Recommendations

| # | Insight (evidence) | Recommendation | Priority |
|---|--------------------|----------------|----------|
| 1 | **Vulnerable road users account for ~57.2% of serious/fatal casualties** — car occupants are the largest single category (37.7%), but VRUs (pedestrians 21.2% + cyclists 14.2%) plus motorcyclists (19.7%) and e-scooter/e-motorcycle users (2.1%) together make up the majority (BQ7 narrow = 35.5%) | Prioritise pedestrian and cyclist safety interventions: protected crossings, cycle lanes, speed limits in high-VRU areas, and enforcement of driver behaviour near VRUs. Also develop motorcycle-specific interventions: rider training, protective equipment, and road design that reduces conflict points | **High** |
| 2 | **Top 5 districts by serious/fatal rate** are ~6x higher than the bottom district (0.809 vs ~0.13 per accident) (BQ2) | Conduct targeted audits of the top 10% of districts, focusing on road design, speed limits, and enforcement. Allocate resources proportionally to risk | **High** |
| 3 | **Weekends and small hours (0–5am)** have the highest serious/fatal rates (23.1% on Sundays and 27.9% at 3am) (BQ8) | Increase lighting, speed enforcement, and driver alertness campaigns on weekends and in the small hours. Consider temporary speed limits in high-risk areas | **Medium** |
| 4 | **Darkness without street lights** has a 29.2% serious/fatal rate vs 20.0% in daylight, while weather barely moves severity (rain 20.6% vs fine 21.4%) (BQ3) | Prioritise street lighting on unlit roads with high casualty counts over weather-specific measures | **Medium** |
| 5 | **Serious/fatal share is rising** — from 19.4% in 2021 to 22.9% in 2025 (20.6% → 23.4% on DfT's adjusted severity), with a +6.0% YoY jump in 2025 (BQ9) | Monitor the trend on adjusted severity so changes in injury recording don't mask or exaggerate it. Investigate which road-user groups drive the rise | **High** |
| 6 | **Per-vehicle risk is rising** — S/F per 100K licensed vehicles (GB) increased 12.1% from 63.8 (2021) to 71.5 (2025) (BQ13) | The rise in serious/fatal casualties is not simply a function of fleet growth. Prioritise speed management and VRU protection, and track the rate on adjusted severity | **High** |
| 7 | **Urban roads have the highest S/F rate per 100M km** (minor urban 9.11, urban 'A' 8.71); motorways the lowest (0.77) (BQ12) | Focus traffic calming, 20mph zones, and junction and crossing design on urban roads; motorways are not a priority on this measure | **Medium** |
| 8 | **Inner London boroughs have the highest exposure-adjusted S/F rates** (17–45 per 100M km) (BQ14) | London's high per-km rates reflect urban density and VRU exposure. Prioritise protected intersections, cycle infrastructure, and speed limits in Inner London | **High** |

---

## 6. Limitations

- **District attribution:** The 2025 `local_authority_district` field is 100% `-1` (unknown). District attribution therefore uses `local_authority_ons_district` (ONS codes), which resolved `dim_location` from 396 → 2,492 rows. This is a data-quality issue that should be addressed in future extracts.
- **Field sparsity:** Some fields (e.g., weather, lighting) have a non-trivial proportion of "Unknown" values, which limits the precision of the analysis.
- **Exposure data coverage:** TRA8904 covers 186 of 370 districts (England and Wales only; Scotland is included at national level but not at LA level). The raw traffic counts file covers 214 LAs (England/Wales). BQ14 rates are therefore not available for Scottish districts.
- **Miles vs km:** RAS0201 published rates use **miles** (per billion vehicle miles), while our exposure tables use **kilometres**. A conversion factor of 1.609344 km/mile is needed when comparing. DAX measures `DfT Published KSI Rate` and `DfT Published Fatal Rate` use the DfT's mile-based rates directly.
- **Proxy rates:** BQ12–BQ14 use vehicle-km as the exposure denominator. This is a proxy for true exposure (which would account for time spent on road, speed, and VRU presence). Pedestrian and cyclist exposure is not directly captured in the vehicle-km denominator.
- **VEH0101 quarterly data:** Vehicle licensing data is quarterly; the ETL uses Q4 (year-end) snapshots as the annual vehicle population estimate.
- **No causal inference:** The analysis is descriptive, not causal. Correlations (e.g., between weather and severity) do not imply causation.
- **Severity recording:** Police forces using injury-based reporting (CRASH) record more injuries as serious than older systems did. DfT publishes adjusted severity to correct for this; the headline counts here are unadjusted, and BQ9 cross-checks the trend on adjusted severity.
- **Code tables:** STATS19 fields are coded integers. A wrong code table (weather, lighting, road surface, road class) produced mislabelled results in an earlier version; `tests/test_cleaning.py` now pins the corrected tables.

---

## 7. Conclusion

This project has successfully transformed raw DfT road-safety data into a governed SQL data warehouse and an interactive Power BI report that answers 14 business questions. The analysis covers **652,821 casualties** across **370 districts** over five years (2021–2025), with **137,044 serious or fatal** outcomes (21.0%). Phase B adds exposure-adjusted rates using DfT road traffic estimates, vehicle licensing data, and published casualty rates, revealing that per-vehicle risk is rising 12% over five years, that urban roads carry the highest serious/fatal rate per km driven (motorways the lowest), and that Inner London boroughs have the highest exposure-adjusted serious/fatal rates.

The most important finding is that **vulnerable road users collectively account for ~57.2% of all serious/fatal casualties** — car occupants are the largest single category (37.7%), but VRUs (pedestrians 21.2% + cyclists 14.2%) plus motorcyclists (19.7%) and e-scooter/e-motorcycle users (2.1%) together make up the majority. The serious/fatal share is also rising steadily, from 19.4% in 2021 to 22.9% in 2025. The top 5 districts by serious/fatal rate are ~6x higher than the bottom district, suggesting that targeted interventions in high-risk areas could have a significant impact.

**Next steps:**
1. ~~Incorporate exposure data (traffic volume, population) to adjust serious/fatal rates~~ — **DONE (Phase B)**
2. Extend the analysis to include IMD (Index of Multiple Deprivation) data to explore inequality in road-safety outcomes (Phase C)
3. Develop predictive models to identify high-risk locations and time periods (Phase D)
4. Conduct a cost-benefit analysis of the recommended interventions using RAS4001 cost data (Phase F)

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
  6. Run the exposure ETL (Phase B): `python etl/load_exposure.py --data-dir data/exposure --db-url postgresql://postgres:postgres@localhost:5432/road_safety`
  7. Verify: `psql road_safety -c "SELECT COUNT(*) AS accidents FROM fact_accident;"`
  8. Power BI: Follow `docs/power_bi_guide.md`
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
  5. Exposure & Rates (BQ12, BQ13, BQ14)
- **E. Row-count reconciliation** — from the data-quality log
