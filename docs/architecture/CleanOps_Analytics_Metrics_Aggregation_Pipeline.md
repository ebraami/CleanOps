# CleanOps --- Analytics & Metrics Aggregation Pipeline Architecture

**Project:** CleanOps --- An AI-Powered Application for Waste Reporting
& Smart Cleaning Management\
**Role:** Data Analysis\
**Document Type:** Analytics, Metrics Aggregation & Dashboard Data
Architecture\
**Status:** Proposed implementation architecture\
**Owner:** Data Analysis\
**Last Updated:** 2026-10-04

------------------------------------------------------------------------

## 1. Purpose

This document defines the end-to-end architecture for the CleanOps
analytics and metrics aggregation pipeline.

The pipeline converts operational report data and lifecycle events into:

1.  operational KPIs;
2.  SLA monitoring metrics;
3.  recurrence and hotspot analytics;
4.  spatial heat-map aggregates;
5.  pre-calculated analytical rollups;
6.  dashboard-ready visualization feeds.

The design is intentionally separated from the transactional workflow.
Operational transactions remain the source of truth, while analytics
consumes stable report/lifecycle data and produces derived analytical
datasets optimized for read-heavy dashboard workloads.

------------------------------------------------------------------------

## 2. Scope

### In scope

-   KPI definitions and formulas;
-   lifecycle timestamp derivation;
-   SLA-breach calculation;
-   recurrence-rate calculation;
-   spatial density / heat-map aggregation;
-   scheduled analytical rollups;
-   dashboard-facing data feeds;
-   query-performance optimization;
-   incremental refresh and backfill strategy;
-   data-quality checks;
-   analytics observability;
-   consistency and acceptance criteria.

### Out of scope

-   AI/computer-vision model implementation;
-   citizen/mobile UI implementation;
-   operator UI design;
-   notification-provider implementation;
-   transactional report-state transition logic;
-   authentication and authorization implementation;
-   final choice of database/vendor unless separately approved by the
    project architecture.

------------------------------------------------------------------------

## 3. Architectural Principles

### 3.1 Transactional data is the source of truth

The operational database remains authoritative for reports, report
state, assignments, images, and lifecycle history.

Analytics must not modify transactional records.

### 3.2 Derived analytics are reproducible

Every KPI, aggregate, and heat-map value must be reproducible from
source records and documented transformation rules.

### 3.3 Do not calculate expensive analytics on every dashboard request

The dashboard should primarily read from pre-calculated analytical
datasets rather than repeatedly scanning raw report/history tables.

### 3.4 Incremental processing is preferred

Only new or changed records since the previous successful processing
point should normally be recalculated.

A full rebuild must remain possible for backfills, corrected source
data, formula changes, or recovery.

### 3.5 Historical values must remain auditable

Analytics should retain the source period, calculation
timestamp/version, and aggregation grain needed to explain how a
displayed value was produced.

### 3.6 KPI definitions must be centralized

The same KPI formula must not be implemented independently in multiple
dashboard endpoints.

------------------------------------------------------------------------

## 4. High-Level Architecture

``` text
                         CLEANOPS OPERATIONAL SYSTEM
                                      |
                                      v
                    +-------------------------------+
                    | Transactional Data Sources    |
                    |-------------------------------|
                    | REPORTS                       |
                    | STATUS_HISTORY / Audit Events |
                    | ASSIGNMENTS                   |
                    | Location / Category / Severity|
                    +-------------------------------+
                                      |
                                      v
                    +-------------------------------+
                    | Analytics Ingestion Layer     |
                    |-------------------------------|
                    | Change detection              |
                    | Incremental extraction        |
                    | Validation / normalization   |
                    | Processing watermark         |
                    +-------------------------------+
                                      |
                                      v
                    +-------------------------------+
                    | Analytics Transformation     |
                    |-------------------------------|
                    | Lifecycle timestamps         |
                    | KPI calculations             |
                    | SLA evaluation                |
                    | Recurrence detection          |
                    | Spatial aggregation          |
                    +-------------------------------+
                           /                 \
                          v                   v
             +---------------------+   +----------------------+
             | KPI / Rollup Store  |   | Spatial Aggregate    |
             |---------------------|   | Store                |
             | Daily KPIs          |   | Grid/cell metrics    |
             | Area KPIs           |   | Density              |
             | SLA metrics         |   | Severity              |
             | Trend metrics       |   | Recurrence            |
             +---------------------+   +----------------------+
                          \                   /
                           \                 /
                            v               v
                    +-------------------------------+
                    | Dashboard Data Access Layer   |
                    |-------------------------------|
                    | KPI endpoints                 |
                    | Trend endpoints               |
                    | Map/heat-map endpoints        |
                    | Filters / pagination          |
                    | Cache where appropriate       |
                    +-------------------------------+
                                      |
                                      v
                         Operations Dashboard / Maps
```

------------------------------------------------------------------------

## 5. Analytics Data Layers

The analytics pipeline should use logical layers even if the
implementation uses fewer physical tables.

  -----------------------------------------------------------------------
  Layer                   Purpose                 Example data
  ----------------------- ----------------------- -----------------------
  Source                  Operational source of   reports, status
                          truth                   history, assignments

  Clean/Conformed         Standardized analytical normalized timestamps,
                          input                   categories, locations

  Event/Lifecycle         Ordered lifecycle facts state transitions and
                                                  derived timestamps

  Fact                    Analysis-ready          one analytical record
                          report-level facts      per report

  Aggregate               Pre-calculated metrics  daily/area/category KPI
                                                  totals

  Spatial Aggregate       Map-ready spatial facts cell counts, weighted
                                                  severity, recurrence

  Dashboard Feed          Read-optimized output   current KPI cards,
                                                  trends, map cells
  -----------------------------------------------------------------------

The exact physical schema may vary, but the logical separation should
remain.

------------------------------------------------------------------------

# 6. Source Data Contract

The analytics pipeline relies on internally derived and operational data
produced by CleanOps.

The existing data-boundary work distinguishes citizen/external inputs
from internally derived platform data. For analytics, the important
distinction is that raw location/category/evidence enter the platform,
while severity, priority, hotspots, aggregates, trends, validation
results, and other analytical values are derived internally.

Relevant analytical inputs include:

-   `report_id`;
-   report submission timestamp;
-   report location;
-   report category/type;
-   AI/model-derived classification where available;
-   severity;
-   priority;
-   report lifecycle/status history;
-   assignment timestamps;
-   work-start timestamp;
-   work-completion timestamp;
-   evidence-submission timestamp;
-   resolution timestamp;
-   return-for-rework events;
-   validation/quality flags.

**Rule:** the analytics layer must not silently replace missing source
values with invented values. Missing or invalid fields are classified
and monitored as data-quality issues.

------------------------------------------------------------------------

# 7. Lifecycle-to-Analytics Mapping

CleanOps lifecycle history provides the event foundation for operational
KPIs.

The analytics layer should derive timestamps from the durable
lifecycle/history records rather than relying on application logs.

A report may progress through the following logical lifecycle:

``` text
SUBMITTED
    |
    v
UNDER_REVIEW
    |
    v
ASSIGNED
    |
    v
IN_PROGRESS
    |
    v
COMPLETED
    |
    v
EVIDENCE_SUBMITTED
    |
    v
UNDER_REVIEW
    |
    +--------------------+
    |                    |
    v                    v
RESOLVED          RETURNED_FOR_REWORK
                         |
                         v
                    IN_PROGRESS
                         |
                         v
                    COMPLETED
                         |
                         v
              EVIDENCE_SUBMITTED
                         |
                         v
                    UNDER_REVIEW
                         |
                    repeat decision
```

For analytics, each lifecycle event should provide:

-   `report_id`;
-   previous state;
-   new state;
-   event timestamp;
-   actor/source;
-   correlation/transition identity where available.

This allows the pipeline to reconstruct the required business timestamps
without adding one database column for every KPI.

------------------------------------------------------------------------

# 8. Canonical Analytical Timestamps

The analytics model should expose a normalized timestamp set:

  Analytical timestamp       Derived from
  -------------------------- -------------------------------------
  `submitted_at`             report submission
  `review_started_at`        first transition into review
  `assigned_at`              transition into assigned
  `work_started_at`          transition into in-progress
  `completed_at`             cleaning completion
  `evidence_submitted_at`    completion-evidence submission
  `resolved_at`              successful transition into resolved
  `returned_for_rework_at`   each return-for-rework event

For repeated rework cycles, the pipeline must preserve event history
rather than overwriting earlier events.

------------------------------------------------------------------------

# 9. Operational KPI Definitions

## 9.1 Clean-up Turnaround Time

### Primary definition

Clean-up turnaround time measures the elapsed service time from
assignment of a cleaning request until the request is successfully
resolved.

``` text
cleanup_turnaround_time
    = resolved_at - assigned_at
```

For reports that are not resolved, the value is not treated as a
completed turnaround time.

### Average turnaround

``` text
average_cleanup_turnaround
    = SUM(cleanup_turnaround_time for resolved reports)
      / COUNT(resolved reports)
```

### Median / percentile turnaround

The dashboard should also support P50, P95, and P99 where operationally
useful, because averages can hide long-running reports.

### Active cleaning duration

To avoid confusing operational turnaround with actual work duration:

``` text
active_cleaning_duration
    = completed_at - work_started_at
```

These are separate metrics.

-   **Turnaround time:** service elapsed time from assignment to
    resolution.
-   **Active cleaning duration:** time spent in the active cleaning
    stage.

------------------------------------------------------------------------

# 10. SLA Breach Metrics

## 10.1 SLA Due Time

Each report must have an applicable SLA target based on the approved
business SLA policy.

The target may depend on factors such as priority/category.

Conceptually:

``` text
sla_due_at
    = sla_clock_start_at + applicable_sla_target
```

For this analytics document, the SLA clock starts at `assigned_at`,
unless the approved operational policy defines another start event.

The exact SLA duration values are configuration/business-policy data,
not hard-coded into the analytics SQL.

## 10.2 SLA Breach Flag

For a resolved report:

``` text
sla_breached
    = 1, if resolved_at > sla_due_at
    = 0, otherwise
```

For an unresolved report:

``` text
sla_breached_as_of_now
    = 1, if current_time > sla_due_at
    = 0, otherwise
```

Unresolved reports must not be counted as completed SLA breaches until
the reporting definition explicitly distinguishes **currently overdue**
from **final breached**.

## 10.3 SLA Breach Rate

``` text
sla_breach_rate
    = breached_eligible_reports / eligible_reports
```

Where:

-   `eligible_reports` = reports with a valid SLA target and a valid SLA
    clock start;
-   `breached_eligible_reports` = eligible reports whose final
    resolution exceeded the applicable SLA.

The dashboard should expose both:

-   current overdue count;
-   final SLA breach rate.

These are different operational concepts.

------------------------------------------------------------------------

# 11. Recurrence Metrics

Recurrence measures whether the same type of waste problem reappears in
the same or nearby area after a previous incident has been resolved.

A recurrence definition must be deterministic.

## 11.1 Recurrence Matching Rule

A report can be classified as a recurrence when all required conditions
are satisfied:

1.  it belongs to the same analytical issue category;
2.  its location falls within the configured recurrence spatial
    radius/cell;
3.  a previous comparable report was resolved before the new report;
4.  the new report occurs within the configured recurrence window after
    the previous resolution.

Conceptually:

``` text
is_recurrence(report)
    = same_category
      AND within_spatial_threshold
      AND previous_report_resolved
      AND new_report_time <= previous_resolution_time + recurrence_window
```

The spatial threshold and recurrence window are configurable parameters
and must be versioned with the analytical job.

## 11.2 Recurrence Rate

``` text
recurrence_rate
    = recurrent_reports / eligible_reports
```

The denominator must use the same eligibility rules for every reporting
period.

## 11.3 Recurrence Count

``` text
recurrence_count
    = COUNT(reports classified as recurrent)
```

## 11.4 Important distinction

Recurrence is not the same as duplicate reporting.

-   **Duplicate:** multiple reports likely refer to the same original
    incident.
-   **Recurrence:** a new incident/problem appears again after a
    previous incident was resolved.

The analytics layer must not mix these concepts.

------------------------------------------------------------------------

# 12. Spatial Heat-Map Aggregation

## 12.1 Goal

The map should not scan every historical report whenever the user pans,
zooms, or changes a layer.

Instead, reports are transformed into spatial cells and pre-aggregated.

The implementation should use a consistent spatial indexing strategy
(for example, a grid/geohash/H3-style cell system) selected by the
project architecture. The logical contract below is independent of the
specific technology.

## 12.2 Spatial Grain

Each report is assigned to:

``` text
spatial_cell_id
```

using its normalized latitude/longitude.

The spatial cell resolution should be selected according to map zoom
level.

A single high-resolution dataset should not be forced to serve every
zoom level if doing so creates unnecessary query cost.

## 12.3 Basic Density Metric

For cell `c` during time window `T`:

``` text
density(c,T)
    = number_of_eligible_reports_in_cell_c_during_T
```

## 12.4 Density per Area

If cell area is available:

``` text
density_per_area(c,T)
    = report_count(c,T) / cell_area(c)
```

This prevents comparisons between cells of different physical areas.

## 12.5 Severity-Weighted Density

A useful analytical layer can provide a severity-weighted score:

``` text
severity_weighted_density(c,T)
    = SUM(severity_score_i) / eligible_report_count(c,T)
```

An alternative total-impact measure is:

``` text
severity_weighted_load(c,T)
    = SUM(severity_score_i)
```

The dashboard must label these metrics clearly because an average
severity and a total severity load answer different questions.

## 12.6 Priority-Weighted Heat Map

If priority is represented numerically:

``` text
priority_weighted_load(c,T)
    = SUM(priority_weight_i)
```

The numeric mapping must come from the approved priority model;
analytics must not invent a mapping.

------------------------------------------------------------------------

# 13. Spatial Heat-Map Dimensions

The spatial aggregate should support filtering by:

-   time window;
-   issue category;
-   severity;
-   priority;
-   lifecycle/resolution state where meaningful;
-   recurrence flag;
-   administrative area if available;
-   spatial resolution / zoom level.

The aggregate should retain enough dimensions to avoid rebuilding the
entire map dataset for every filter.

However, high-cardinality dimensions should not be materialized blindly.
Frequently used dashboard filters should be prioritized based on actual
query patterns.

------------------------------------------------------------------------

# 14. Analytical Rollups

Pre-calculated rollups are the primary performance mechanism for
dashboard analytics.

## 14.1 Report-Level Analytical Fact

Logical grain:

``` text
one row = one report
```

Contains normalized:

-   lifecycle timestamps;
-   final status;
-   category;
-   severity;
-   priority;
-   location/cell;
-   SLA values;
-   recurrence classification;
-   quality flags.

This table is the foundation for higher-level aggregates.

## 14.2 Daily KPI Rollup

Logical grain:

``` text
date + optional operational dimensions
```

Recommended measures:

-   reports submitted;
-   reports assigned;
-   reports started;
-   reports completed;
-   reports resolved;
-   reports returned for rework;
-   average turnaround;
-   median turnaround;
-   P95 turnaround;
-   SLA-eligible reports;
-   SLA breaches;
-   SLA breach rate;
-   recurrence count;
-   recurrence rate.

## 14.3 Spatial Rollup

Logical grain:

``` text
time_bucket + spatial_cell + selected dimensions
```

Recommended measures:

-   report count;
-   unresolved report count;
-   resolved report count;
-   average severity;
-   total severity load;
-   recurrence count;
-   average turnaround where relevant.

## 14.4 Trend Rollup

Logical grain:

``` text
time_bucket + metric + dimension
```

Used for dashboard trend charts without scanning raw history.

------------------------------------------------------------------------

# 15. Aggregation Schedule

The schedule is designed around dashboard freshness versus computation
cost.

  ------------------------------------------------------------------------
  Pipeline                                   Refresh Purpose
  --------------------- ---------------------------- ---------------------
  Lifecycle/KPI                      Every 5 minutes Current operational
  incremental update                                 KPI freshness

  Spatial heat-map                  Every 15 minutes Map density/hotspot
  aggregate                                          freshness

  Daily KPI rollup        Every hour for the current Fast trend and KPI
                           day; final reconciliation queries
                                     after day close 

  Historical                                   Daily Detect late/corrected
  reconciliation                                     source data

  Full rebuild                             On demand Formula/version
                                                     changes or recovery
  ------------------------------------------------------------------------

### Why incremental schedules are used

A dashboard should not trigger a full historical aggregation every time
it loads.

Instead:

``` text
new/changed source records
        ↓
incremental processing
        ↓
affected KPI buckets / spatial cells
        ↓
upsert aggregate values
        ↓
dashboard reads aggregate
```

The exact scheduler/worker technology is intentionally
implementation-neutral.

------------------------------------------------------------------------

# 16. Incremental Processing and Watermarks

Each pipeline run should maintain a durable processing watermark.

Example:

``` text
last_successful_processed_at
```

A run processes records newer than the previous watermark plus a small
overlap/reconciliation window when required for late-arriving events.

A safer logical model is:

``` text
processing_window_start
processing_window_end
job_run_id
formula_version
status
```

### Idempotency

Re-running the same processing window must not double-count reports.

Use deterministic aggregation keys such as:

``` text
date + category + spatial_cell + metric_dimension
```

and upsert/rebuild affected buckets rather than blindly inserting
duplicates.

------------------------------------------------------------------------

# 17. Late-Arriving and Corrected Data

Analytics must handle source changes after an earlier rollup has already
been produced.

Examples:

-   a report receives a late lifecycle event;
-   a location is corrected;
-   a category is corrected;
-   a severity score is updated;
-   an operator resolves a report after the previous rollup;
-   a report is returned for rework.

The pipeline should:

1.  detect the changed report/event;
2.  identify all affected analytical periods/cells;
3.  recompute those affected aggregates;
4.  replace the previous aggregate values atomically;
5.  record the job/version used.

This is safer than adding adjustment rows indefinitely.

------------------------------------------------------------------------

# 18. Dashboard Data Feed Architecture

The dashboard should consume purpose-built analytical endpoints/views.

Example logical feeds:

``` text
GET /analytics/kpis/summary
GET /analytics/kpis/trends
GET /analytics/kpis/sla
GET /analytics/kpis/recurrence
GET /analytics/map/heatmap
```

These are logical examples; final API naming belongs to the backend/API
contract.

### Summary feed

Designed for KPI cards:

``` text
total_reports
open_reports
resolved_reports
average_turnaround
sla_breach_rate
recurrence_rate
```

### Trend feed

Designed for charts:

``` text
period
metric
value
optional_dimension
```

### Heat-map feed

Designed for map rendering:

``` text
spatial_cell_id
geometry/centroid
report_count
severity_metric
recurrence_count
time_bucket
```

The map endpoint should return only the spatial cells and metrics
required for the selected viewport/filter.

------------------------------------------------------------------------

# 19. Dashboard Query Performance Optimization

## 19.1 Query pre-aggregation

Prefer:

``` text
dashboard
   ↓
pre-calculated aggregate
   ↓
small result set
```

instead of:

``` text
dashboard
   ↓
raw reports + full status history
   ↓
joins
   ↓
grouping
   ↓
spatial calculation
   ↓
result
```

The second approach becomes increasingly expensive as historical data
grows.

## 19.2 Indexing Strategy

Indexes should support the actual filter and join patterns.

At minimum, the implementation should evaluate indexes around:

### Lifecycle/history

``` text
(report_id, event_timestamp)
(event_type/state, event_timestamp)
```

### Reports

``` text
(submission_timestamp)
(status, submission_timestamp)
(category, submission_timestamp)
(priority, submission_timestamp)
```

### Spatial analytics

``` text
(spatial_cell_id, time_bucket)
(spatial_cell_id, category, time_bucket)
```

The exact indexes must be validated with query plans rather than added
indiscriminately.

## 19.3 Spatial query optimization

For map queries:

1.  filter by viewport/time first where possible;
2.  use spatial cell keys for aggregation;
3.  avoid recalculating distance/density for every request;
4.  return only cells required for the current map resolution;
5.  precompute frequently requested heat-map metrics.

## 19.4 Pagination

Large report-level dashboard lists must be paginated.

Offset pagination may become expensive for deep pages; keyset/cursor
pagination should be preferred for large, frequently changing datasets
where supported.

## 19.5 Caching

Short-lived caching can be applied to:

-   dashboard summary KPIs;
-   trend results;
-   heat-map results for repeated filters/viewports.

Cache keys should include all parameters that affect the result, for
example:

``` text
metric + date_range + category + severity_filter
```

For heat maps:

``` text
spatial_resolution + viewport/cell set + date_range + filters
```

A cache must never return data for a different filter combination.

------------------------------------------------------------------------

# 20. Dashboard Performance Validation Targets

The analytics architecture should be validated against the project's
approved performance requirements. Where the current baseline is used,
the following targets are the validation criteria:

  Operation                                   Target
  -------------------------------------- -----------
  Dashboard initial/filter response        ≤ 3 s P95
  Map initial heat-map/render response     ≤ 4 s P95
  Dynamic spatial query/layer refresh      ≤ 2 s P95
  API error rate                             \< 0.1%

Performance testing should record:

-   P50;
-   P95;
-   P99;
-   request count;
-   concurrency;
-   error rate.

These targets are validation criteria for the analytical access layer,
not permission to hide slow queries behind arbitrary caching.

------------------------------------------------------------------------

# 21. KPI Query Examples

## 21.1 Turnaround

Logical calculation:

``` sql
SELECT
    AVG(resolved_at - assigned_at) AS avg_turnaround
FROM report_analytics_fact
WHERE resolved_at IS NOT NULL
  AND assigned_at IS NOT NULL
  AND resolved_at >= :from
  AND resolved_at < :to;
```

The exact SQL syntax depends on the selected database.

## 21.2 SLA breach rate

``` sql
SELECT
    SUM(CASE WHEN resolved_at > sla_due_at THEN 1 ELSE 0 END)
      * 1.0 / COUNT(*) AS sla_breach_rate
FROM report_analytics_fact
WHERE sla_due_at IS NOT NULL
  AND resolved_at IS NOT NULL
  AND resolved_at >= :from
  AND resolved_at < :to;
```

## 21.3 Spatial density

``` sql
SELECT
    spatial_cell_id,
    COUNT(*) AS report_count
FROM report_analytics_fact
WHERE submitted_at >= :from
  AND submitted_at < :to
GROUP BY spatial_cell_id;
```

These examples define the analytical intent. Production queries should
read from the appropriate rollup whenever the rollup can answer the
dashboard request.

------------------------------------------------------------------------

# 22. Data Quality Controls

Before an aggregate is published, the pipeline should validate:

### Required identifiers

-   `report_id` is present and unique at report-fact grain;
-   lifecycle events reference a valid report.

### Timestamp consistency

Examples:

``` text
submitted_at <= assigned_at
assigned_at <= work_started_at
work_started_at <= completed_at
completed_at <= evidence_submitted_at
evidence_submitted_at <= resolved_at
```

These comparisons apply only when the corresponding events exist.

### Location quality

-   latitude/longitude are within valid geographic ranges;
-   invalid locations are excluded from spatial aggregation and counted
    as quality failures;
-   corrected locations trigger re-aggregation of affected cells.

### KPI integrity

-   turnaround cannot be negative;
-   SLA due time must be derivable for SLA-eligible reports;
-   recurrence calculations must use a consistent configuration version;
-   aggregate counts must not double-count the same report.

------------------------------------------------------------------------

# 23. Handling Rework Correctly

A rejected completion submission does not create a new report.

Therefore, recurrence and operational KPI logic must not count each
rework cycle as a separate incident.

For turnaround:

``` text
assigned_at → final resolved_at
```

For rework analytics:

``` text
rework_count
    = number of RETURNED_FOR_REWORK events
```

For rework rate:

``` text
rework_rate
    = reports_with_at_least_one_rework
      / reports_entering_operator_review
```

This keeps the distinction between:

-   one operational report;
-   multiple lifecycle transitions;
-   multiple completion attempts.

------------------------------------------------------------------------

# 24. Analytical Versioning

Formula changes can alter historical results.

Therefore, the analytics pipeline should track:

``` text
formula_version
aggregation_version
job_run_id
calculated_at
```

Example:

``` text
KPI: SLA Breach Rate
Formula Version: 1.0
```

When a formula changes, the affected rollups can be rebuilt without
losing knowledge of how older values were produced.

------------------------------------------------------------------------

# 25. Failure and Recovery

If an analytics job fails:

1.  the previous successful aggregate remains available;
2.  the failed run is marked unsuccessful;
3.  the watermark is not advanced past unprocessed data;
4.  the job can safely retry;
5.  affected aggregates are recomputed idempotently;
6.  monitoring records the failure.

The dashboard should prefer the last known valid aggregate over exposing
partially calculated results.

------------------------------------------------------------------------

# 26. Observability

The analytics pipeline should emit operational metrics for:

``` text
analytics_job_runs_total
analytics_job_failures_total
analytics_job_duration_seconds
analytics_records_processed_total
analytics_records_failed_total
analytics_watermark_lag_seconds
analytics_rollup_refresh_lag_seconds
analytics_dashboard_query_duration_seconds
analytics_dashboard_query_errors_total
```

High-cardinality identifiers such as `report_id` should not be metric
labels.

Useful dimensions include:

-   job name;
-   pipeline stage;
-   result;
-   aggregate type.

------------------------------------------------------------------------

# 27. End-to-End Data Flow

``` text
REPORT / LIFECYCLE DATA
          |
          v
  Change Detection
          |
          v
 Validation + Normalization
          |
          v
 Lifecycle Event Ordering
          |
          v
 Report Analytics Fact
          |
    +-----+------------------+
    |                        |
    v                        v
 KPI Transformation    Spatial Transformation
    |                        |
    v                        v
 KPI Rollups            Spatial Rollups
    |                        |
    +-----------+------------+
                |
                v
       Dashboard Data Layer
                |
       +--------+---------+
       |                  |
       v                  v
   KPI Dashboard      Map / Heat Map
```

------------------------------------------------------------------------

# 28. Acceptance Criteria

This task is complete when:

-   [ ] The analytics architecture clearly separates transactional
    source data from derived analytics.
-   [ ] Lifecycle timestamps can be derived from durable
    lifecycle/history records.
-   [ ] Clean-up turnaround time has one explicit canonical formula.
-   [ ] SLA breach logic distinguishes final breaches from currently
    overdue reports.
-   [ ] SLA breach rate has an explicit denominator.
-   [ ] Recurrence is explicitly distinguished from duplicate reporting.
-   [ ] Recurrence rate has an explicit denominator.
-   [ ] Spatial aggregation has a defined logical grain.
-   [ ] Heat-map density formulas are documented.
-   [ ] Severity-weighted spatial metrics are documented separately from
    simple density.
-   [ ] Pre-calculated analytical rollups are defined.
-   [ ] Incremental processing and idempotency are defined.
-   [ ] Late-arriving/corrected data is handled.
-   [ ] Dashboard feeds are separated from raw transactional queries.
-   [ ] Query/index/cache optimization principles are documented.
-   [ ] Dashboard/map performance targets are testable.
-   [ ] Data-quality validation rules are documented.
-   [ ] Analytics failures can be retried without corrupting or
    double-counting aggregates.
-   [ ] Formula/aggregation versions are traceable.
-   [ ] The resulting design supports both KPI dashboards and spatial
    heat-map visualization.

------------------------------------------------------------------------

# 29. Final Architecture Summary

The CleanOps analytics architecture follows this principle:

``` text
Operational Source of Truth
          ↓
Lifecycle / Analytical Facts
          ↓
Incremental KPI + Spatial Transformations
          ↓
Pre-calculated Rollups
          ↓
Dashboard-Optimized Data Feeds
          ↓
Fast KPI Cards, Trends, and Heat Maps
```

The key design decision is to keep **business transactions and analytics
separate** while maintaining a reliable analytical connection through
lifecycle history, normalized report facts, deterministic KPI formulas,
and versioned aggregation jobs.

This provides:

-   consistent KPI definitions;
-   reproducible analytics;
-   scalable spatial aggregation;
-   predictable dashboard performance;
-   support for late/corrected data;
-   auditable analytical calculations;
-   reduced load on the transactional database.

------------------------------------------------------------------------

# 30. Implementation Notes / Decision Boundaries

The following items are deliberately treated as configurable
architecture inputs rather than invented project facts:

1.  the final database engine;
2.  the final spatial-index technology;
3.  exact SLA durations by priority/category;
4.  exact recurrence radius and recurrence time window;
5.  final dashboard API naming;
6.  final job scheduler/worker technology.

The analytics contract in this document remains valid regardless of
those implementation choices.

**Important:** These values should be configured centrally and
versioned. They should not be hard-coded separately inside dashboard
queries or individual analytical jobs.

------------------------------------------------------------------------

# 31. Consistency With Existing CleanOps Requirements

This document is designed to consume the existing CleanOps
lifecycle/history model and derived-data boundary.

In particular:

-   lifecycle history remains the basis for durable analytical
    timestamps;
-   rework cycles preserve the same `report_id`;
-   rejected completion evidence remains part of history rather than
    creating a new incident;
-   externally supplied location/category data is treated as source
    input;
-   hotspots, aggregates, trends, and similar analytical values are
    treated as internally derived data.

This keeps the analytics layer consistent with the existing CleanOps
requirements rather than introducing a parallel lifecycle or
duplicate-report model.
