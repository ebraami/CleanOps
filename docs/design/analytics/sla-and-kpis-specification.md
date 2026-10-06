# CleanOps — SLA & KPI Specification

> **Project:** CleanOps — An AI-Powered Application for Waste Reporting & Smart Cleaning Management  
> **Role:** Data Analysis  
> **Document Type:** Analytics / KPI / Mathematical Specification  
> **Target Path:** `docs/design/analytics/sla-and-kpis-specification.md`  
> **Status:** Proposed implementation contract  
> **Version:** 1.0  
> **Last Updated:** 2026-10-06

---

## 1. Purpose

This document defines the mathematical and analytical contract for three dashboard capabilities in CleanOps:

1. **SLA breach flags** based on report creation time and the report's priority tier.
2. **Area Litter Burden** scores with deterministic time decay.
3. **Municipal dashboard aggregation queries** for SLA, operational, and area-level KPIs.

The goal is to ensure that the same business definition is used by the analytics pipeline, scheduled rollups, and dashboard APIs.

The specification is intentionally separated from the transactional workflow:

```text
Operational Database
        |
        | reports + lifecycle history + location + priority
        v
Analytical Fact Layer
        |
        +--------------------+
        |                    |
        v                    v
   SLA/KPI Models      Spatial Burden Models
        |                    |
        +---------+----------+
                  |
                  v
          Dashboard Rollups
                  |
                  v
        Municipal Dashboard
```

---

## 2. Design Principles

### 2.1 Source of truth

The operational database remains authoritative for:

- report creation/submission;
- report priority;
- report location/area;
- lifecycle state history;
- resolution timestamp.

Analytics only derives values from these records.

### 2.2 Deterministic formulas

Every dashboard value must be reproducible from source records and the configuration version used to calculate it.

### 2.3 Configuration over hard-coding

SLA targets, severity weights, priority weights, decay half-life, and other policy parameters must be stored in versioned configuration rather than hard-coded independently in dashboard endpoints.

### 2.4 Final breach vs. current overdue

These are different metrics and must never be silently combined.

- **Final SLA breach:** a completed/resolved report finished after its SLA deadline.
- **Currently overdue:** an unresolved report whose SLA deadline has already passed.

### 2.5 Rework does not create a new incident

A returned-for-rework report keeps the same `report_id`.

Therefore:

- SLA performance remains associated with the original report.
- Area burden must not count each rework cycle as a new litter incident.
- Rework is an operational event, not a new report.

---

# 3. Canonical Analytical Inputs

The analytics layer should expose a normalized report-level analytical fact with at least the following logical fields:

| Field | Meaning |
|---|---|
| `report_id` | Unique report identifier |
| `submitted_at` | Report creation/submission timestamp |
| `priority_tier` | Approved operational priority classification |
| `severity_score` | Normalized severity value |
| `category` | Waste/problem category |
| `area_id` | Administrative area/district identifier |
| `spatial_cell_id` | Map aggregation cell |
| `resolved_at` | Timestamp of successful resolution; nullable |
| `final_status` | Final/current lifecycle state |
| `is_duplicate` | Duplicate classification, if available |
| `quality_valid` | Whether required analytical inputs passed validation |

Lifecycle timestamps are reconstructed from durable lifecycle/history records rather than application logs.

Canonical timestamps include:

- `submitted_at`
- `review_started_at`
- `assigned_at`
- `work_started_at`
- `completed_at`
- `evidence_submitted_at`
- `resolved_at`

---

# 4. SLA Specification

## 4.1 SLA clock start

For this task, the SLA clock is defined from **report creation/submission time** because the requirement explicitly evaluates SLA against creation time and priority tier.

```text
sla_clock_start_at = submitted_at
```

Therefore:

```text
sla_elapsed_time(t)
    = t - submitted_at
```

For a completed report:

```text
sla_elapsed_time_final
    = resolved_at - submitted_at
```

> If the approved operational policy later changes the SLA clock to another lifecycle event, only `sla_clock_start_at` changes. The remaining formulas remain unchanged.

---

## 4.2 Priority-based SLA target

Each priority tier maps to one approved SLA target.

```text
SLA_TARGET(priority_tier)
    → target duration
```

Example logical configuration:

| Priority Tier | SLA Target | Meaning |
|---|---:|---|
| `CRITICAL` | Configured | Highest urgency |
| `HIGH` | Configured | High urgency |
| `MEDIUM` | Configured | Standard urgency |
| `LOW` | Configured | Lower urgency |

The exact durations are **business-policy configuration**, not invented by the analytics layer.

Recommended configuration fields:

```text
priority_tier
sla_target_minutes
effective_from
effective_to
configuration_version
```

A report must use the configuration version effective at its SLA clock start.

---

## 4.3 SLA due timestamp

For report `i`:

```text
sla_due_at_i
    = submitted_at_i
      + SLA_TARGET(priority_tier_i)
```

In minutes:

```text
sla_due_at_i
    = submitted_at_i
      + interval(SLA_TARGET(priority_tier_i))
```

This creates one deterministic deadline for every SLA-eligible report.

---

## 4.4 SLA eligibility

A report is SLA-eligible when:

```text
submitted_at IS NOT NULL
AND priority_tier IS NOT NULL
AND SLA_TARGET(priority_tier) IS NOT NULL
AND quality_valid = TRUE
```

Formally:

```text
eligible_i =
    1, if all required SLA inputs are valid
    0, otherwise
```

Invalid or missing inputs must not be silently assigned an arbitrary SLA target.

They should instead be counted in a data-quality metric.

---

# 5. SLA Breach Flags

## 5.1 Final SLA breach

For a report that has been resolved:

```text
final_sla_breach_i =
    1, if resolved_at_i > sla_due_at_i
    0, otherwise
```

Equivalent mathematical form:

```text
final_sla_breach_i
    = I(resolved_at_i > sla_due_at_i)
```

where `I(condition)` returns `1` when the condition is true and `0` otherwise.

### Boundary condition

If:

```text
resolved_at = sla_due_at
```

the report is **not breached**.

Therefore:

```text
resolved_at <= sla_due_at
    → SLA met

resolved_at > sla_due_at
    → SLA breached
```

---

## 5.2 Current overdue flag

An unresolved report can already be late even though its final SLA outcome does not yet exist.

For the current time `t_now`:

```text
current_overdue_i =
    1, if resolved_at_i IS NULL
       AND t_now > sla_due_at_i
    0, otherwise
```

This metric answers:

> "How many currently open reports have already exceeded their SLA deadline?"

It must not be treated as the final SLA breach metric.

---

## 5.3 SLA status classification

The dashboard may expose one normalized status:

```text
if not SLA eligible:
    NOT_ELIGIBLE

else if resolved_at IS NOT NULL AND resolved_at > sla_due_at:
    BREACHED

else if resolved_at IS NULL AND current_time > sla_due_at:
    OVERDUE

else if resolved_at IS NOT NULL:
    MET

else:
    WITHIN_SLA
```

Resulting states:

| SLA Status | Definition |
|---|---|
| `NOT_ELIGIBLE` | Missing/invalid SLA inputs |
| `MET` | Resolved on or before deadline |
| `BREACHED` | Resolved after deadline |
| `OVERDUE` | Still unresolved and deadline has passed |
| `WITHIN_SLA` | Still unresolved and deadline has not passed |

---

# 6. SLA Metrics for Municipal Dashboards

## 6.1 SLA-eligible reports

```text
eligible_reports
    = COUNT(reports where eligible_i = 1)
```

---

## 6.2 Final SLA breaches

```text
final_breaches
    = COUNT(
        reports where
        eligible_i = 1
        AND resolved_at IS NOT NULL
        AND resolved_at > sla_due_at
      )
```

---

## 6.3 Final SLA breach rate

The denominator is the number of **resolved SLA-eligible reports**, because an unresolved report does not yet have a final SLA outcome.

```text
final_sla_breach_rate
    = final_breaches
      / resolved_eligible_reports
```

Where:

```text
resolved_eligible_reports
    = COUNT(
        reports where
        eligible_i = 1
        AND resolved_at IS NOT NULL
      )
```

If the denominator is zero:

```text
final_sla_breach_rate = NULL
```

The dashboard should display this as `N/A`, not `0%`, because no final outcomes exist.

---

## 6.4 Current overdue count

```text
current_overdue_count
    = COUNT(
        reports where
        eligible_i = 1
        AND resolved_at IS NULL
        AND current_time > sla_due_at
      )
```

---

## 6.5 SLA compliance rate

```text
sla_compliance_rate
    = 1 - final_sla_breach_rate
```

or:

```text
sla_compliance_rate
    = sla_met_reports
      / resolved_eligible_reports
```

where:

```text
sla_met_reports
    = COUNT(
        reports where
        eligible_i = 1
        AND resolved_at IS NOT NULL
        AND resolved_at <= sla_due_at
      )
```

---

## 6.6 Average SLA lateness

For breached resolved reports:

```text
sla_lateness_i
    = resolved_at_i - sla_due_at_i
```

Average lateness:

```text
average_sla_lateness
    = SUM(sla_lateness_i for breached reports)
      / COUNT(breached reports)
```

Only breached reports are included.

If there are no breached reports:

```text
average_sla_lateness = NULL
```

---

## 6.7 Maximum SLA lateness

```text
max_sla_lateness
    = MAX(resolved_at - sla_due_at)
```

calculated over final breached reports only.

This is useful for identifying severe service delays.

---

# 7. Area Litter Burden

## 7.1 Purpose

**Area Litter Burden** represents the current analytical pressure caused by waste-related reports in an area.

It should answer:

> "How much active and recently resolved litter-related burden is associated with this area right now?"

The metric is not simply a report count.

It combines:

1. report severity;
2. report priority;
3. current unresolved status;
4. decay of resolved incidents over time.

This prevents an old resolved incident from contributing the same burden as a current unresolved high-severity incident.

---

# 8. Burden Weight

For report `i`, define a base impact weight:

```text
W_i
    = SeverityWeight(severity_i)
      × PriorityWeight(priority_i)
```

Where both mappings come from versioned configuration.

Example logical configuration:

| Dimension | Example configuration concept |
|---|---|
| Severity | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` → configured numeric weight |
| Priority | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` → configured numeric multiplier |

The analytics layer must not assume that the textual priority label itself is numeric.

For example, the implementation may use:

```text
severity_weight("LOW")      → configured value
severity_weight("MEDIUM")   → configured value
severity_weight("HIGH")     → configured value
severity_weight("CRITICAL") → configured value
```

The same principle applies to priority.

---

# 9. Burden Decay Formula

## 9.1 Why decay is applied

Once a litter incident is resolved, its contribution should gradually decrease because it no longer represents active litter requiring immediate intervention.

However, it should not disappear immediately from historical burden analysis.

Therefore, a resolved report contributes a decaying value.

---

## 9.2 Half-life model

Use an exponential half-life model.

Let:

- `t` = evaluation timestamp;
- `r_i` = report resolution timestamp;
- `H` = configured burden decay half-life in days.

The decay factor is:

```text
D_i(t)
    = exp(
        -ln(2) × max(0, t - r_i) / H
      )
```

For a resolved report:

```text
t = r_i
    → D_i(t) = 1
```

After one half-life:

```text
t = r_i + H
    → D_i(t) = 0.5
```

After two half-lives:

```text
t = r_i + 2H
    → D_i(t) = 0.25
```

After three half-lives:

```text
t = r_i + 3H
    → D_i(t) = 0.125
```

This makes the decay behavior deterministic and easy to tune.

---

# 10. Report-Level Burden Contribution

## 10.1 Unresolved report

An unresolved report represents active burden:

```text
burden_contribution_i(t)
    = W_i
```

No decay is applied while the report remains unresolved.

---

## 10.2 Resolved report

For a resolved report:

```text
burden_contribution_i(t)
    = W_i × D_i(t)
```

Therefore:

```text
burden_contribution_i(t)
    = W_i × exp(
        -ln(2) × max(0, t - resolved_at_i) / H
      )
```

---

## 10.3 Unified formula

The complete report contribution can be written as:

```text
C_i(t) =
    W_i,                                  if resolved_at_i IS NULL

    W_i × exp(
        -ln(2) × max(0, t - resolved_at_i) / H
    ),                                    otherwise
```

---

# 11. Area Litter Burden Formula

For area `a` at evaluation time `t`:

```text
AreaLitterBurden(a,t)
    = Σ C_i(t)
```

for all eligible litter-related reports belonging to area `a`.

Expanded:

```text
AreaLitterBurden(a,t)
    =
    Σ unresolved reports
        [SeverityWeight_i × PriorityWeight_i]

    +

    Σ resolved reports
        [
          SeverityWeight_i
          × PriorityWeight_i
          × exp(
              -ln(2)
              × age_since_resolution_i
              / H
            )
        ]
```

Only reports passing the analytical eligibility rules are included.

---

# 12. Burden Eligibility Rules

A report contributes to Area Litter Burden only when:

```text
quality_valid = TRUE
AND duplicate_flag = FALSE
AND category is eligible for litter-burden analysis
AND valid area/location exists
```

Important:

- Duplicate reports must not inflate area burden.
- Rework events must not create additional burden contributions.
- Invalid locations must not be assigned to an arbitrary area.
- Missing severity/priority weights must result in a data-quality exception rather than an invented value.

---

# 13. Optional Normalized Burden Score

Raw burden values are useful for ranking areas, but they can be difficult to compare if area sizes or report volumes differ.

A normalized score can therefore be calculated separately.

## 13.1 Burden per area

```text
burden_per_km2(a,t)
    = AreaLitterBurden(a,t)
      / area_size_km2(a)
```

This should only be used when a reliable administrative area size is available.

---

## 13.2 Relative burden index

For dashboard ranking:

```text
relative_burden_index(a,t)
    = AreaLitterBurden(a,t)
      / MAX(
          AreaLitterBurden(all areas,t)
        )
```

This produces a value in:

```text
0 ≤ relative_burden_index ≤ 1
```

provided all burden values are non-negative.

A display percentage can be:

```text
relative_burden_percent
    = 100 × relative_burden_index
```

The raw burden should still be retained because normalization depends on the comparison population.

---

# 14. Municipal Dashboard KPI Model

The dashboard should expose metrics at consistent grains.

## 14.1 City-level KPIs

Recommended city-level measures:

- total reports;
- open reports;
- resolved reports;
- current overdue reports;
- final SLA breaches;
- final SLA breach rate;
- SLA compliance rate;
- average turnaround;
- median turnaround;
- P95 turnaround;
- total Area Litter Burden;
- number of high-burden areas.

---

## 14.2 Area-level KPIs

For each municipality/district/area:

- report count;
- open report count;
- resolved report count;
- current overdue count;
- final SLA breach count;
- final SLA breach rate;
- average turnaround;
- average severity;
- total severity load;
- Area Litter Burden;
- burden per km² where supported;
- recurrence count/rate where supported.

---

## 14.3 Time dimensions

All dashboard aggregates should support a reporting period:

```text
day
week
month
custom date range
```

The aggregation grain must be explicit.

For example:

```text
date + area_id
```

is different from:

```text
month + area_id
```

and must not be mixed implicitly.

---

# 15. Analytical SQL Contract

The SQL examples below use PostgreSQL-style syntax because it provides clear interval, date, CTE, and aggregation semantics.

The physical table names may be adapted to the final database schema.

The logical contract must remain unchanged.

---

# 16. SQL Model — SLA Analytical Fact

## 16.1 Purpose

Create one analytical record per report containing:

- SLA target;
- SLA deadline;
- final breach flag;
- current overdue flag;
- SLA status.

```sql
WITH report_sla AS (
    SELECT
        r.report_id,
        r.submitted_at,
        r.priority_tier,
        r.resolved_at,
        r.area_id,
        r.severity_score,
        r.category,
        r.is_duplicate,
        c.sla_target_minutes,
        c.configuration_version,

        CASE
            WHEN r.submitted_at IS NOT NULL
             AND r.priority_tier IS NOT NULL
             AND c.sla_target_minutes IS NOT NULL
             AND COALESCE(r.is_duplicate, FALSE) = FALSE
            THEN TRUE
            ELSE FALSE
        END AS sla_eligible

    FROM reports r

    LEFT JOIN sla_policy_config c
        ON c.priority_tier = r.priority_tier
       AND r.submitted_at >= c.effective_from
       AND (
            c.effective_to IS NULL
            OR r.submitted_at < c.effective_to
       )
),

sla_fact AS (
    SELECT
        *,
        CASE
            WHEN sla_eligible
            THEN submitted_at
                 + (sla_target_minutes * INTERVAL '1 minute')
            ELSE NULL
        END AS sla_due_at
    FROM report_sla
)

SELECT
    *,
    CASE
        WHEN sla_eligible
         AND resolved_at IS NOT NULL
         AND resolved_at > sla_due_at
        THEN TRUE
        ELSE FALSE
    END AS final_sla_breached,

    CASE
        WHEN sla_eligible
         AND resolved_at IS NULL
         AND CURRENT_TIMESTAMP > sla_due_at
        THEN TRUE
        ELSE FALSE
    END AS current_overdue,

    CASE
        WHEN NOT sla_eligible THEN 'NOT_ELIGIBLE'

        WHEN resolved_at IS NOT NULL
         AND resolved_at > sla_due_at
        THEN 'BREACHED'

        WHEN resolved_at IS NULL
         AND CURRENT_TIMESTAMP > sla_due_at
        THEN 'OVERDUE'

        WHEN resolved_at IS NOT NULL
        THEN 'MET'

        ELSE 'WITHIN_SLA'
    END AS sla_status

FROM sla_fact;
```

### Important implementation rule

The policy join must select the configuration that was effective when the report was created.

This prevents a later SLA policy change from silently changing historical results.

---

# 17. SQL Model — Municipal SLA KPI Rollup

Once the report-level SLA fact exists, the dashboard rollup should consume it directly.

```sql
SELECT
    DATE(submitted_at) AS report_date,
    area_id,

    COUNT(*) AS reports_submitted,

    COUNT(*) FILTER (
        WHERE sla_eligible
    ) AS sla_eligible_reports,

    COUNT(*) FILTER (
        WHERE sla_eligible
          AND resolved_at IS NOT NULL
    ) AS resolved_eligible_reports,

    COUNT(*) FILTER (
        WHERE final_sla_breached
    ) AS final_sla_breaches,

    COUNT(*) FILTER (
        WHERE current_overdue
    ) AS current_overdue_count,

    CASE
        WHEN COUNT(*) FILTER (
            WHERE sla_eligible
              AND resolved_at IS NOT NULL
        ) > 0
        THEN
            COUNT(*) FILTER (
                WHERE final_sla_breached
            )::DECIMAL
            /
            COUNT(*) FILTER (
                WHERE sla_eligible
                  AND resolved_at IS NOT NULL
            )
        ELSE NULL
    END AS final_sla_breach_rate,

    CASE
        WHEN COUNT(*) FILTER (
            WHERE sla_eligible
              AND resolved_at IS NOT NULL
        ) > 0
        THEN
            COUNT(*) FILTER (
                WHERE sla_eligible
                  AND resolved_at IS NOT NULL
                  AND final_sla_breached = FALSE
            )::DECIMAL
            /
            COUNT(*) FILTER (
                WHERE sla_eligible
                  AND resolved_at IS NOT NULL
            )
        ELSE NULL
    END AS sla_compliance_rate

FROM analytics_report_sla

GROUP BY
    DATE(submitted_at),
    area_id;
```

This is the preferred production pattern because the dashboard does not need to reconstruct SLA rules on every request.

---

# 18. SQL Model — Area Litter Burden

## 18.1 Purpose

Calculate the contribution of each report before aggregating by area.

```sql
WITH report_burden AS (
    SELECT
        r.report_id,
        r.area_id,
        r.category,
        r.severity_score,
        r.priority_tier,
        r.submitted_at,
        r.resolved_at,

        sw.weight AS severity_weight,
        pw.weight AS priority_weight,

        (
            sw.weight * pw.weight
        ) AS base_burden_weight

    FROM reports r

    JOIN severity_weight_config sw
        ON sw.severity_value = r.severity_score

    JOIN priority_weight_config pw
        ON pw.priority_tier = r.priority_tier

    WHERE COALESCE(r.is_duplicate, FALSE) = FALSE
      AND r.quality_valid = TRUE
      AND r.area_id IS NOT NULL
      AND r.category IN (
          SELECT category
          FROM litter_burden_categories
          WHERE enabled = TRUE
      )
),

contributions AS (
    SELECT
        rb.*,

        CASE
            WHEN rb.resolved_at IS NULL THEN
                rb.base_burden_weight

            ELSE
                rb.base_burden_weight
                * EXP(
                    -LN(2)
                    * EXTRACT(
                        EPOCH FROM (
                            CURRENT_TIMESTAMP - rb.resolved_at
                        )
                    )
                    / (
                        cfg.decay_half_life_days * 86400
                    )
                )
        END AS burden_contribution

    FROM report_burden rb

    CROSS JOIN (
        SELECT
            CAST(value AS DECIMAL) AS decay_half_life_days
        FROM analytics_config
        WHERE key = 'area_litter_burden_half_life_days'
    ) cfg
)

SELECT
    area_id,
    SUM(burden_contribution) AS area_litter_burden,
    COUNT(*) AS contributing_reports

FROM contributions

GROUP BY area_id;
```

---

# 19. SQL Model — Area Burden With Explicit Evaluation Time

For historical dashboard analysis, the evaluation timestamp should be explicit instead of relying on `CURRENT_TIMESTAMP`.

```sql
WITH report_burden AS (
    SELECT
        r.report_id,
        r.area_id,
        sw.weight * pw.weight AS base_burden_weight,
        r.resolved_at

    FROM reports r

    JOIN severity_weight_config sw
        ON sw.severity_value = r.severity_score

    JOIN priority_weight_config pw
        ON pw.priority_tier = r.priority_tier

    WHERE COALESCE(r.is_duplicate, FALSE) = FALSE
      AND r.quality_valid = TRUE
      AND r.area_id IS NOT NULL
),

contributions AS (
    SELECT
        rb.area_id,

        CASE
            WHEN rb.resolved_at IS NULL
              OR rb.resolved_at > :as_of_timestamp
            THEN rb.base_burden_weight

            ELSE
                rb.base_burden_weight
                * EXP(
                    -LN(2)
                    * EXTRACT(
                        EPOCH FROM (
                            :as_of_timestamp - rb.resolved_at
                        )
                    )
                    / (:half_life_days * 86400)
                )
        END AS burden_contribution

    FROM report_burden rb
)

SELECT
    area_id,
    SUM(burden_contribution) AS area_litter_burden

FROM contributions

GROUP BY area_id;
```

The explicit `as_of_timestamp` makes the metric reproducible and suitable for backfills and historical reporting.

---

# 20. SQL Model — Municipal Dashboard Summary

A municipal dashboard can consume a prepared area-level rollup:

```sql
SELECT
    area_id,
    report_date,

    reports_submitted,
    reports_resolved,
    open_reports,

    current_overdue_count,
    final_sla_breaches,
    final_sla_breach_rate,
    sla_compliance_rate,

    average_turnaround_minutes,
    median_turnaround_minutes,
    p95_turnaround_minutes,

    area_litter_burden,
    burden_per_km2

FROM municipal_area_kpi_daily

WHERE report_date BETWEEN :start_date AND :end_date

ORDER BY
    area_litter_burden DESC,
    final_sla_breach_rate DESC;
```

This allows the dashboard to identify areas with:

1. high current litter burden;
2. high SLA pressure;
3. poor service compliance.

---

# 21. Recommended Analytical Rollup Grains

The following logical grains should be maintained separately.

| Rollup | Grain | Main Use |
|---|---|---|
| `analytics_report_sla` | One row/report | SLA facts |
| `municipal_kpi_daily` | Date + area | KPI dashboard |
| `area_litter_burden` | Evaluation time + area | Burden map/ranking |
| `area_category_kpi_daily` | Date + area + category | Category filtering |
| `municipal_kpi_monthly` | Month + area | Historical trends |
| `spatial_burden_rollup` | Time bucket + spatial cell | Map/heat map |

The dashboard should query the smallest rollup capable of answering the requested view.

---

# 22. Data Quality Rules

Before publishing SLA or burden metrics, validate:

## 22.1 Required identifiers

- `report_id` exists.
- `report_id` is unique at report-fact grain.
- lifecycle events reference an existing report.

## 22.2 Timestamp consistency

When both timestamps exist:

```text
submitted_at <= assigned_at
assigned_at <= work_started_at
work_started_at <= completed_at
completed_at <= evidence_submitted_at
evidence_submitted_at <= resolved_at
```

Invalid sequences should be flagged rather than silently corrected.

## 22.3 SLA integrity

For SLA-eligible reports:

```text
sla_target_minutes > 0
sla_due_at IS NOT NULL
```

Also:

```text
final_sla_breached = TRUE
    only when resolved_at > sla_due_at
```

## 22.4 Burden integrity

- severity weight must exist;
- priority weight must exist;
- area must be valid;
- duplicate reports must be excluded;
- burden contribution must be non-negative;
- decay factor must satisfy:

```text
0 < D_i(t) <= 1
```

for resolved reports evaluated at or after resolution.

---

# 23. Edge Cases

## 23.1 Report resolved exactly at SLA deadline

```text
resolved_at = sla_due_at
```

Result:

```text
final_sla_breached = FALSE
sla_status = MET
```

---

## 23.2 Report still open after SLA deadline

Result:

```text
current_overdue = TRUE
final_sla_breached = FALSE
sla_status = OVERDUE
```

It becomes a final breach only after resolution if:

```text
resolved_at > sla_due_at
```

---

## 23.3 Missing priority

The report is:

```text
sla_eligible = FALSE
```

It must not be assigned an arbitrary priority or SLA duration by analytics.

---

## 23.4 Duplicate report

A report classified as a duplicate must not increase Area Litter Burden.

It may still be retained for operational/audit analysis.

---

## 23.5 Returned for rework

A rework cycle does not create a new burden contribution.

The report keeps the same `report_id`.

For SLA:

```text
original submitted_at
        |
        +--------------------+
                             |
                        final resolved_at
```

For burden:

```text
one report
    → one burden contribution
```

---

## 23.6 Corrected location

If a report's location/area is corrected:

1. remove its old contribution from the old area/cell;
2. assign it to the corrected area/cell;
3. recompute affected rollup buckets.

The correction must be idempotent.

---

# 24. Versioning

Because formula changes can change historical dashboard values, every analytical result should be traceable to:

```text
formula_version
configuration_version
aggregation_version
job_run_id
calculated_at
```

Recommended example:

```text
formula_version       = 1.0
configuration_version = 1
aggregation_version   = 1.0
```

If the decay half-life or SLA policy changes, historical results must not silently appear to have been calculated using the new configuration.

A rebuild/backfill should explicitly record the new version.

---

# 25. Incremental Processing

The analytics pipeline should process new or changed reports incrementally.

Conceptually:

```text
New / Changed Reports
        |
        v
Validate + Normalize
        |
        v
Recalculate Affected Report Facts
        |
        +-------------------+
        |                   |
        v                   v
   SLA Rollups        Burden Rollups
        |                   |
        +---------+---------+
                  |
                  v
        Dashboard Data Layer
```

Reprocessing the same input window must not double-count reports.

Use deterministic aggregation keys such as:

```text
report_date
+
area_id
+
category
+
metric_dimension
```

and use upsert/rebuild semantics for affected buckets.

---

# 26. Performance Requirements for the Analytics Layer

Dashboard endpoints should prefer pre-calculated rollups.

Recommended pattern:

```text
Dashboard request
      ↓
Dashboard KPI/API layer
      ↓
Pre-calculated analytical rollup
      ↓
Response
```

Avoid:

```text
Dashboard request
      ↓
Full lifecycle-history scan
      ↓
Full report aggregation
      ↓
Spatial calculation
      ↓
Response
```

The second pattern creates unnecessary database load and makes dashboard latency dependent on historical data volume.

---

# 27. Metric Naming Contract

Use consistent names across SQL, analytics jobs, APIs, and dashboard documentation.

Recommended names:

```text
sla_eligible
sla_due_at
final_sla_breached
current_overdue
sla_status
final_sla_breach_rate
sla_compliance_rate
average_sla_lateness_minutes

area_litter_burden
burden_contribution
burden_decay_factor
burden_per_km2
relative_burden_index
```

Avoid multiple names for the same business definition.

For example, do not use:

```text
sla_failed
sla_breach
late_sla
over_sla
```

interchangeably when they mean the same final breach flag.

Use:

```text
final_sla_breached
```

as the canonical field.

---

# 28. Acceptance Criteria

This deliverable is complete when all of the following are satisfied:

- [x] SLA clock start is explicitly defined.
- [x] SLA targets are mapped to priority tiers.
- [x] SLA due timestamp has a deterministic formula.
- [x] Final SLA breach has a deterministic formula.
- [x] Current overdue status is separated from final breach.
- [x] SLA breach rate has an explicit denominator.
- [x] Exact equality with the SLA deadline is treated as compliant.
- [x] Missing SLA configuration is treated as a data-quality/eligibility issue.
- [x] Area Litter Burden is mathematically defined.
- [x] Severity and priority are incorporated through configurable weights.
- [x] Resolved reports use exponential half-life decay.
- [x] Unresolved reports retain active burden.
- [x] Duplicate reports are excluded from burden.
- [x] Rework cycles do not create additional incidents.
- [x] Historical evaluation uses an explicit `as_of_timestamp`.
- [x] Area-level aggregation is defined.
- [x] Municipal dashboard aggregation is defined.
- [x] PostgreSQL-style analytical SQL models are provided.
- [x] Data-quality rules are specified.
- [x] Edge cases are specified.
- [x] Formula/configuration versioning is specified.
- [x] Incremental/idempotent processing is specified.
- [x] Dashboard queries are designed to consume analytical rollups rather than repeatedly scanning raw lifecycle history.

---

# 29. Final Mathematical Contract

The core formulas of this specification are summarized below.

## SLA

```text
sla_due_at
    = submitted_at
      + SLA_TARGET(priority_tier)
```

```text
final_sla_breached
    = I(
        resolved_at > sla_due_at
      )
```

for resolved reports.

```text
current_overdue
    = I(
        resolved_at IS NULL
        AND current_time > sla_due_at
      )
```

## SLA breach rate

```text
final_sla_breach_rate
    = final_sla_breaches
      / resolved_eligible_reports
```

## Burden weight

```text
W_i
    = SeverityWeight_i
      × PriorityWeight_i
```

## Resolved-report decay

```text
D_i(t)
    = exp(
        -ln(2)
        × max(0, t - resolved_at_i)
        / H
      )
```

## Report burden contribution

```text
C_i(t) =
    W_i,                    if unresolved

    W_i × D_i(t),            if resolved
```

## Area Litter Burden

```text
AreaLitterBurden(a,t)
    = Σ C_i(t)
```

## Normalized burden

```text
burden_per_km2
    = AreaLitterBurden
      / area_size_km2
```

---

# 30. Decision Boundaries

The following are intentionally **configuration/architecture inputs**, not invented analytics facts:

1. exact SLA duration for each priority tier;
2. exact severity-to-weight mapping;
3. exact priority-to-weight mapping;
4. Area Litter Burden decay half-life;
5. final administrative-area geometry source;
6. final spatial indexing technology;
7. final physical table/view names;
8. final scheduler/worker implementation.

These values must be approved by the relevant business/system requirements and stored as versioned configuration.

The analytics contract in this document remains stable if those values change.

---

# 31. Consistency With CleanOps Analytics Architecture

This specification follows the established CleanOps analytics principles:

```text
Operational Source of Truth
          ↓
Lifecycle / Analytical Facts
          ↓
Deterministic KPI + Spatial Transformations
          ↓
Pre-calculated Rollups
          ↓
Dashboard Data Layer
          ↓
Municipal Dashboard / Map
```

In particular:

- lifecycle history remains the source for durable analytical timestamps;
- one `report_id` represents one operational report even across rework cycles;
- SLA results are derived from report creation time and versioned priority policy;
- area burden is derived analytically from report evidence and operational state;
- duplicate incidents are not allowed to inflate burden;
- dashboard queries should consume prepared analytical datasets;
- all formula and configuration changes remain auditable.

---

## Document Ownership

**Owner:** Data Analysis  
**Project:** CleanOps  
**Deliverable:** SLA Countdown Rules, Area Litter Burden Decay Formulas, and Analytical SQL Models  
**Target Repository Path:** `docs/design/analytics/sla-and-kpis-specification.md`
