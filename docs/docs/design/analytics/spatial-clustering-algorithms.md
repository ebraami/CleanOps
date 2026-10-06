# CleanOps — Spatial Clustering Algorithms

> **Analytics Design Document**  
> **Project:** CleanOps — An AI-Powered Application for Waste Reporting & Smart Cleaning Management  
> **Role:** Data Analysis  
> **Deliverable:** `docs/design/analytics/spatial-clustering-algorithms.md`  
> **Status:** Proposed / MVP Design  
> **Primary Technology:** PostgreSQL + PostGIS  
> **Clustering Algorithm:** DBSCAN via `ST_ClusterDBSCAN`

---

## 1. Executive Summary

CleanOps receives geolocated waste/litter reports from users. Individual reports are useful for investigation, but cleaning teams need higher-level spatial information such as:

- **Where are reports repeatedly concentrated?**
- **Which areas currently require cleaning?**
- **Which locations are persistent hotspots rather than isolated incidents?**
- **How should cleanup zones be prioritized?**

This document defines the analytics design for answering those questions using **PostGIS `ST_ClusterDBSCAN`**.

The solution separates three concepts:

1. **Spatial clustering** — groups nearby reports into dense spatial clusters.
2. **Temporal recurrence** — determines whether similar clusters repeatedly appear across independent time windows.
3. **Operational prioritization** — ranks current cleanup zones using recent volume, severity, recency, and historical recurrence.

This separation is intentional. DBSCAN is a spatial density algorithm; recurrence and operational priority are business/analytics layers built on top of the clustering results.

### Main outputs

```text
Raw Waste Reports
       |
       v
Data Validation
       |
       v
Spatial Normalization
       |
       +-------------------------+
       |                         |
       v                         v
Recent DBSCAN              Historical DBSCAN
       |                         |
       v                         v
Cleanup Zones           Cluster Instances
                                 |
                                 v
                       Cross-Window Matching
                                 |
                                 v
                       Recurring Hotspots
                                 |
                       +---------+---------+
                       |                   |
                       v                   v
                 Priority Score      Map / API Output
```

---

# 2. Business Objectives

The analytics component must support CleanOps in converting individual reports into actionable spatial intelligence.

## 2.1 Dynamic cleanup zones

Identify areas with a sufficiently high concentration of **recent** reports.

These zones answer:

> "Where should the cleaning operation focus now?"

## 2.2 Recurring litter hotspots

Identify locations that repeatedly become dense reporting areas across multiple historical time windows.

These hotspots answer:

> "Where does litter repeatedly occur?"

## 2.3 Explainable prioritization

Each cleanup zone should have an interpretable priority score rather than an opaque number.

The team should be able to explain a high-priority zone using measurable factors such as:

- recent report volume;
- severity;
- recency;
- historical recurrence.

---

# 3. Scope

## In Scope

- Input validation for geospatial reports.
- Metric spatial representation.
- PostGIS DBSCAN clustering.
- `eps` / radius configuration.
- `minpoints` density configuration.
- Dynamic 7-day cleanup clustering.
- Historical weekly clustering.
- Cross-window hotspot matching.
- Recurrence scoring.
- Cleanup-zone priority scoring.
- Cluster summary metrics.
- GeoJSON-ready output.
- Visualization specifications.
- SQL reference implementation.
- Parameter tuning methodology.
- Testing and acceptance criteria.
- Performance/indexing guidance.
- Reproducibility requirements.

## Out of Scope

This component does not:

- predict future litter locations by itself;
- perform image classification;
- determine the root cause of litter;
- permanently assign a report to a hotspot;
- replace human operational decisions;
- guarantee that every DBSCAN cluster represents a physically contaminated area;
- use cluster IDs as permanent business identities.

---

# 4. Analytical Concepts

## 4.1 Report

A single user-generated observation of waste/litter.

## 4.2 DBSCAN cluster

A spatially dense group of reports generated during one clustering run.

## 4.3 Noise report

A report that does not belong to a DBSCAN cluster under the selected parameters.

Noise is **not invalid data**.

It remains a valid CleanOps report and may become part of a cluster when additional reports arrive.

## 4.4 Cluster instance

A DBSCAN cluster belonging to a specific time window and parameter configuration.

A cluster instance is temporary/analytical.

## 4.5 Recurring hotspot

A stable business-level location formed by matching cluster instances across multiple time windows.

## 4.6 Dynamic cleanup zone

A recent cluster that represents current operational demand.

---

# 5. Why DBSCAN?

DBSCAN is appropriate for CleanOps because the number of waste hotspots is unknown in advance.

Compared with K-Means, DBSCAN:

| Requirement | K-Means | DBSCAN |
|---|---:|---:|
| Requires number of clusters in advance | Yes | No |
| Detects noise/outliers | No | Yes |
| Density-based | No | Yes |
| Suitable for irregular cluster shapes | Limited | Yes |
| Natural spatial radius parameter | No | Yes |

The two primary DBSCAN parameters are:

- `eps` — maximum neighborhood distance.
- `minpoints` — minimum density requirement.

---

# 6. Important Design Decision: Geometry Units

`ST_ClusterDBSCAN` works on PostGIS `geometry`.

The distance represented by `eps` depends on the geometry's coordinate system.

Therefore, CleanOps should perform clustering using a **metric projected CRS** appropriate for the deployment area.

## Recommended pattern

```text
GPS coordinates
     |
     | WGS84 / EPSG:4326
     v
PostGIS geometry(Point, 4326)
     |
     | ST_Transform(...)
     v
Metric projected geometry
     |
     v
ST_ClusterDBSCAN(... eps in meters ...)
```

For a deployment restricted to an appropriate UTM zone, a local UTM CRS can be used.

For example, if the entire deployment area is covered by UTM zone 36N:

```text
EPSG:32636
```

should be evaluated.

> The final CRS must be selected based on the actual CleanOps geographic coverage. Do not hard-code a UTM zone for worldwide deployment.

---

# 7. Input Data Contract

The analytics layer assumes a table similar to:

```sql
waste_reports
-------------
id                  BIGINT / UUID
reported_at         TIMESTAMPTZ
status              TEXT
latitude            DOUBLE PRECISION
longitude           DOUBLE PRECISION
geom                geometry(Point, 4326)
geom_metric         geometry(Point, <metric SRID>)
severity            INTEGER
waste_type          TEXT
reporter_id         BIGINT / UUID
is_resolved         BOOLEAN
```

The exact production schema may differ.

## Required fields

| Field | Required | Purpose |
|---|---:|---|
| `id` | Yes | Unique report identity |
| `reported_at` | Yes | Temporal analysis |
| `latitude` | Yes | Location |
| `longitude` | Yes | Location |
| metric geometry | Yes | DBSCAN distance calculations |
| `status` | Yes | Business filtering |

## Recommended fields

- `severity`
- `waste_type`
- `reporter_id`
- `is_resolved`
- GPS accuracy, if available

---

# 8. Data Quality Pipeline

Before clustering, reports must pass validation.

## 8.1 Required validation

Reject from the clustering input when:

```text
id IS NULL
reported_at IS NULL
latitude IS NULL
longitude IS NULL
geometry IS NULL
```

## 8.2 Coordinate validation

Valid ranges:

```text
latitude  ∈ [-90, 90]
longitude ∈ [-180, 180]
```

## 8.3 Geometry validation

Expected geometry:

```text
POINT
```

The raw report should never be deleted merely because it fails an analytical rule.

Instead:

```text
Raw data
   |
   +--> valid -> clustering
   |
   +--> invalid -> quality/error layer
```

This preserves auditability.

---

# 9. Status Filtering

Only reports representing active/relevant litter observations should normally participate in dynamic clustering.

Example:

```sql
status IN (
    'confirmed',
    'open',
    'in_progress'
)
```

The exact values must match the actual CleanOps status model.

### Historical analysis

Resolved reports can remain eligible for historical recurrence analysis because a resolved report still provides evidence that the location previously experienced litter.

### Current cleanup analysis

Resolved reports should normally not drive current cleanup priority unless the business rules explicitly require them.

---

# 10. Time-Window Strategy

A single all-time DBSCAN run is not recommended for operational decisions.

## 10.1 Dynamic window

Initial baseline:

```text
7 days
```

Purpose:

- current cleanup demand;
- recent activity;
- fast response.

## 10.2 Historical recurrence window

Initial baseline:

```text
30 days
```

split into:

```text
weekly windows
```

Example:

```text
Week 1 -> DBSCAN
Week 2 -> DBSCAN
Week 3 -> DBSCAN
Week 4 -> DBSCAN
```

This makes recurrence measurable.

---

# 11. DBSCAN Parameters

## 11.1 `eps`

Maximum neighborhood distance.

Example:

```text
eps = 100 meters
```

means reports can be considered neighbors when they are within the configured spatial distance.

## 11.2 `minpoints`

Minimum density requirement.

Example:

```text
minpoints = 4
```

means a sufficiently dense group requires at least four reports under DBSCAN's density rules.

## 11.3 Initial baseline

```yaml
eps_meters: 100
minpoints: 4
```

These are **starting values only**.

The final values must be selected from actual CleanOps data.

---

# 12. SQL — Valid Input Reports

Assuming `geom_metric` already exists:

```sql
WITH valid_reports AS (
    SELECT
        id AS report_id,
        reported_at,
        status,
        severity,
        waste_type,
        reporter_id,
        geom_metric AS geom
    FROM waste_reports
    WHERE reported_at >= :window_start
      AND reported_at <  :window_end
      AND status IN ('confirmed', 'open', 'in_progress')
      AND geom_metric IS NOT NULL
)
SELECT *
FROM valid_reports;
```

If the database does not yet store metric geometry:

```sql
SELECT
    id AS report_id,
    reported_at,
    severity,
    waste_type,
    ST_Transform(
        ST_SetSRID(
            ST_MakePoint(longitude, latitude),
            4326
        ),
        :projected_srid
    ) AS geom
FROM waste_reports
WHERE reported_at >= :window_start
  AND reported_at <  :window_end
  AND status IN ('confirmed', 'open', 'in_progress')
  AND latitude BETWEEN -90 AND 90
  AND longitude BETWEEN -180 AND 180;
```

---

# 13. SQL — Core PostGIS DBSCAN

```sql
WITH input_reports AS (
    SELECT
        id AS report_id,
        reported_at,
        severity,
        waste_type,
        geom_metric AS geom
    FROM waste_reports
    WHERE reported_at >= :window_start
      AND reported_at <  :window_end
      AND status IN ('confirmed', 'open', 'in_progress')
      AND geom_metric IS NOT NULL
),

clustered AS (
    SELECT
        report_id,
        reported_at,
        severity,
        waste_type,
        geom,

        ST_ClusterDBSCAN(
            geom,
            eps => :eps_meters,
            minpoints => :minpoints
        ) OVER (
            ORDER BY report_id
        ) AS cluster_id

    FROM input_reports
)

SELECT *
FROM clustered
ORDER BY cluster_id NULLS LAST, report_id;
```

## Determinism

The stable:

```sql
ORDER BY report_id
```

is intentional.

DBSCAN can have ambiguous border points when a point can be associated with multiple density-connected clusters. A stable ordering helps make repeated execution deterministic for the same input and parameters.

---

# 14. Noise Handling

DBSCAN returns:

```text
cluster_id = NULL
```

for noise.

Example:

```text
Report A -> cluster 0
Report B -> cluster 0
Report C -> NULL
Report D -> cluster 1
```

Report C should remain in the raw/reporting system.

It should simply not create a hotspot by itself.

---

# 15. SQL — Cluster Summary

```sql
WITH clustered AS (
    SELECT
        id AS report_id,
        reported_at,
        severity,
        waste_type,
        geom_metric AS geom,

        ST_ClusterDBSCAN(
            geom_metric,
            eps => :eps_meters,
            minpoints => :minpoints
        ) OVER (
            ORDER BY id
        ) AS cluster_id

    FROM waste_reports
    WHERE reported_at >= :window_start
      AND reported_at <  :window_end
      AND status IN ('confirmed', 'open', 'in_progress')
      AND geom_metric IS NOT NULL
),

cluster_summary AS (
    SELECT
        cluster_id,
        COUNT(*) AS report_count,
        AVG(severity) AS avg_severity,
        MAX(severity) AS max_severity,
        COUNT(DISTINCT reported_at::date) AS active_days,
        MIN(reported_at) AS first_report_at,
        MAX(reported_at) AS last_report_at,
        ST_Centroid(ST_Collect(geom)) AS center_geom,
        ST_ConvexHull(ST_Collect(geom)) AS hull_geom
    FROM clustered
    WHERE cluster_id IS NOT NULL
    GROUP BY cluster_id
)

SELECT *
FROM cluster_summary
ORDER BY report_count DESC;
```

---

# 16. Cluster Metrics

Each cluster should expose:

| Metric | Definition |
|---|---|
| `report_count` | Number of reports |
| `avg_severity` | Mean severity |
| `max_severity` | Highest severity |
| `active_days` | Distinct reporting days |
| `first_report_at` | Earliest report |
| `last_report_at` | Latest report |
| `center_geom` | Cluster center |
| `hull_geom` | Approximate footprint |
| `unique_reporters` | Distinct reporters, if available |

The cluster summary is the primary backend representation for dashboard analytics.

---

# 17. Cluster Geometry

## Center

```sql
ST_Centroid(ST_Collect(geom))
```

Use for:

- map markers;
- labels;
- API center point.

## Hull

```sql
ST_ConvexHull(ST_Collect(geom))
```

Use for:

- approximate visualization footprint.

### Important interpretation

The convex hull does **not** mean every location inside the polygon contains waste.

It is only a visual approximation of the spatial distribution of reports.

---

# 18. Recurring Hotspot Detection

A DBSCAN cluster exists only within the input window.

Therefore:

```text
Cluster ID ≠ Hotspot ID
```

A recurring hotspot must be created by matching cluster instances across time.

## Process

```text
Week 1
  -> Cluster A

Week 2
  -> Cluster B

Week 3
  -> Cluster C

Week 4
  -> Cluster D

A/B/C/D
  |
  v
Spatial matching
  |
  v
Hotspot H-0001
```

---

# 19. Cross-Window Matching

Use a separate matching radius.

Example:

```yaml
dbscan_eps_meters: 100
hotspot_match_radius_meters: 100
```

These parameters have different meanings:

| Parameter | Question |
|---|---|
| `eps` | Which reports form one cluster in this window? |
| `match_radius` | Which clusters from different windows represent the same hotspot? |

Example:

```sql
SELECT
    current.cluster_instance_id,
    previous.cluster_instance_id,
    ST_Distance(
        current.center_geom,
        previous.center_geom
    ) AS distance_m
FROM cluster_instances current
JOIN cluster_instances previous
    ON current.window_id <> previous.window_id
   AND ST_DWithin(
        current.center_geom,
        previous.center_geom,
        :match_radius_meters
   );
```

For production, matching should be limited to relevant windows rather than performing unrestricted all-to-all comparisons.

---

# 20. Recurrence Metrics

For each hotspot:

```text
recurrence_count
eligible_window_count
recurrence_rate
```

Formula:

```text
recurrence_rate =
    recurrence_count / eligible_window_count
```

Example:

```text
3 active windows
5 eligible windows

recurrence_rate = 3 / 5 = 0.60
```

---

# 21. Hotspot Classification

Initial product thresholds:

| Recurrence Rate | Classification |
|---:|---|
| `< 0.25` | Occasional |
| `0.25 – < 0.50` | Emerging |
| `0.50 – < 0.75` | Recurring |
| `>= 0.75` | Persistent |

These are **product-policy thresholds**, not universal scientific thresholds.

They should be adjusted after evaluating actual CleanOps behavior.

---

# 22. Dynamic Cleanup Zones

A dynamic cleanup zone should use recent reports only.

Initial baseline:

```yaml
window_days: 7
eps_meters: 100
minpoints: 4
```

A cluster becomes a candidate zone when:

```text
DBSCAN cluster exists
AND
report_count >= operational minimum
```

Optional additional rules:

```text
recent_report_count >= threshold
OR
avg_severity >= threshold
```

---

# 23. Priority Scoring

The priority score should remain explainable.

Recommended initial model:

```text
priority_score =
      0.40 * recent_volume_score
    + 0.25 * severity_score
    + 0.20 * recurrence_score
    + 0.15 * recency_score
```

All components must be normalized to:

```text
[0, 1]
```

## Components

### Recent volume

More reports in the current window → higher priority.

### Severity

Higher severity → higher priority.

### Recurrence

Locations repeatedly becoming hotspots → higher priority.

### Recency

Newer reports → higher priority.

---

# 24. Recency Function

Use exponential decay:

```text
recency_score = exp(-age_hours / half_life_hours)
```

Example with:

```text
half_life = 72 hours
```

| Age | Score |
|---:|---:|
| 0 h | 1.00 |
| 72 h | 0.50 |
| 144 h | 0.25 |

This avoids a hard cutoff where a report suddenly becomes worthless.

---

# 25. Normalization

For each score component:

```text
normalized_value =
    (value - min_value)
    /
    (max_value - min_value)
```

When:

```text
max_value = min_value
```

define the normalized value as a neutral value such as:

```text
0
```

or:

```text
0.5
```

The chosen convention must be consistent across the implementation.

For production, robust percentile normalization can be considered if extreme outliers distort min/max scaling.

---

# 26. Parameter Tuning

Parameter tuning is one of the main analytical responsibilities.

Do not select `eps` and `minpoints` solely by intuition.

## Candidate grid

```text
eps:
50m
75m
100m
150m
200m

minpoints:
3
4
5
6
8
```

Total:

```text
25 configurations
```

---

# 27. Tuning Evaluation Metrics

Evaluate every candidate using:

## 27.1 Number of clusters

```text
cluster_count
```

## 27.2 Noise ratio

```text
noise_ratio =
    noise_reports / total_reports
```

## 27.3 Cluster size

Track:

```text
minimum
median
mean
maximum
```

## 27.4 Spatial compactness

Calculate average distance of reports to cluster center.

Lower values generally indicate tighter clusters.

## 27.5 Temporal stability

Check whether similar physical areas continue to appear across adjacent windows.

## 27.6 Operational usefulness

Human/map validation remains necessary.

---

# 28. Automated Tuning SQL Skeleton

The following pattern can be used to compare candidate configurations.

```sql
WITH parameter_grid AS (
    SELECT *
    FROM (
        VALUES
            (50.0, 3),
            (50.0, 4),
            (75.0, 3),
            (75.0, 4),
            (100.0, 3),
            (100.0, 4),
            (100.0, 5),
            (150.0, 4),
            (150.0, 5),
            (200.0, 5)
    ) AS p(eps_meters, minpoints)
),

reports AS (
    SELECT
        id AS report_id,
        reported_at,
        severity,
        geom_metric AS geom
    FROM waste_reports
    WHERE reported_at >= :tuning_start
      AND reported_at <  :tuning_end
      AND status IN ('confirmed', 'open', 'in_progress')
      AND geom_metric IS NOT NULL
)

-- In production, execute one DBSCAN run per parameter combination
-- and persist the evaluation metrics into an analytics table.
SELECT
    eps_meters,
    minpoints
FROM parameter_grid
ORDER BY eps_meters, minpoints;
```

For the graduation project, it is better to persist tuning results in an evaluation table rather than hide the process inside one extremely complex query.

---

# 29. Recommended Tuning Table

Create:

```text
analytics.cluster_evaluation
```

Suggested schema:

```sql
CREATE TABLE analytics.cluster_evaluation (
    evaluation_id BIGSERIAL PRIMARY KEY,
    eps_meters NUMERIC NOT NULL,
    minpoints INTEGER NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    total_reports INTEGER NOT NULL,
    cluster_count INTEGER NOT NULL,
    noise_count INTEGER NOT NULL,
    noise_ratio NUMERIC NOT NULL,
    median_cluster_size NUMERIC,
    mean_cluster_size NUMERIC,
    max_cluster_size INTEGER,
    mean_compactness_m NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

This makes parameter selection reproducible.

---

# 30. Parameter Selection Procedure

Use this workflow:

```text
1. Select historical data
        |
2. Split into tuning and holdout periods
        |
3. Run candidate configurations
        |
4. Calculate objective metrics
        |
5. Inspect maps
        |
6. Select best operational configuration
        |
7. Validate on holdout period
        |
8. Freeze configuration
```

### Data split

Recommended:

```text
Historical period
├── Tuning period
└── Holdout period
```

Do not use the same period for both parameter selection and final validation.

---

# 31. What Makes a Good Configuration?

A good configuration should:

- identify meaningful dense areas;
- avoid one giant city-wide cluster;
- avoid excessive tiny clusters;
- maintain a reasonable noise ratio;
- produce compact clusters;
- remain reasonably stable across adjacent windows;
- create operationally useful cleanup zones;
- agree with human/map inspection.

There is no single mathematical metric that should decide the final configuration.

---

# 32. Example Interpretation

Suppose two configurations produce:

### Configuration A

```text
eps = 200m
minpoints = 3

clusters = 8
noise_ratio = 4%
```

### Configuration B

```text
eps = 75m
minpoints = 5

clusters = 31
noise_ratio = 62%
```

A is potentially too permissive.

B is potentially too strict.

The preferred configuration might be between them, but the final choice must be based on actual spatial maps and operational requirements.

---

# 33. Visualization Specification

CleanOps should expose three primary map layers.

## Layer A — Individual Reports

Display:

```text
location
timestamp
severity
waste_type
status
```

Purpose:

- detailed inspection;
- debugging;
- transparency.

## Layer B — Dynamic Cleanup Zones

Display:

```text
zone center
zone footprint
report count
average severity
latest report
priority score
```

## Layer C — Recurring Hotspots

Display:

```text
hotspot center
recurrence rate
active windows
average reports/window
last activity
classification
```

---

# 34. Visualization Encoding

| Data | Recommended Encoding |
|---|---|
| Report location | Point |
| Report severity | Marker intensity/size |
| Cluster volume | Zone size / marker size |
| Priority | Visual intensity / ranking |
| Recurrence | Hotspot category |
| Current status | Status indicator |
| Cluster footprint | Polygon/hull |
| Timestamp | Tooltip/details panel |

Do not depend on color alone.

Every visual encoding should have a textual/tooltip representation for accessibility and clarity.

---

# 35. Map Interaction

Clicking a cleanup zone should show:

```text
Zone ID
Report count
Average severity
Highest severity
Active days
First report
Latest report
Priority score
```

Clicking a recurring hotspot should show:

```text
Hotspot ID
Classification
Recurrence rate
Active windows
Average reports/window
Latest activity
Historical trend
```

---

# 36. Stable Business IDs

Never expose the DBSCAN cluster number as a permanent identity.

Bad:

```text
cluster_id = 0
```

Good:

```text
hotspot_id = H-000123
```

A DBSCAN cluster can change after new reports arrive.

A business hotspot identity should be maintained by the cross-window matching layer.

---

# 37. GeoJSON API Contract

Example:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "H-000123",
      "geometry": {
        "type": "Point",
        "coordinates": [30.123, 29.456]
      },
      "properties": {
        "entity_type": "recurring_hotspot",
        "report_count": 18,
        "recurrence_rate": 0.75,
        "active_windows": 3,
        "priority_score": 0.82,
        "classification": "Persistent"
      }
    }
  ]
}
```

For cleanup-zone polygons, return the cluster footprint in `geometry`.

---

# 38. Recommended Database Objects

## 38.1 Validated input view

```text
analytics.valid_waste_reports
```

Responsibilities:

- coordinate validation;
- status filtering;
- spatial normalization.

## 38.2 Cluster instances

```text
analytics.cluster_instances
```

Suggested columns:

```text
cluster_instance_id
window_start
window_end
eps_meters
minpoints
report_count
avg_severity
max_severity
active_days
center_geom
hull_geom
created_at
```

## 38.3 Recurring hotspots

```text
analytics.recurring_hotspots
```

Suggested columns:

```text
hotspot_id
center_geom
recurrence_count
eligible_window_count
recurrence_rate
avg_reports_per_window
last_active_at
classification
priority_score
updated_at
```

## 38.4 Evaluation table

```text
analytics.cluster_evaluation
```

Stores tuning experiments and evaluation metrics.

---

# 39. Spatial and Temporal Indexing

Recommended indexes:

```sql
CREATE INDEX IF NOT EXISTS idx_waste_reports_geom_metric
ON waste_reports
USING GIST (geom_metric);
```

```sql
CREATE INDEX IF NOT EXISTS idx_waste_reports_reported_at
ON waste_reports (reported_at);
```

Potential combined/filtering index:

```sql
CREATE INDEX IF NOT EXISTS idx_waste_reports_status_reported_at
ON waste_reports (status, reported_at);
```

The exact index strategy must be verified using real data volume and query plans.

---

# 40. Query Performance

## Filter first

Apply:

```text
time range
status
geometry availability
geographic scope
```

before clustering.

## Avoid all-history clustering

Do not run:

```text
all reports since project launch
```

for a question such as:

```text
what needs cleaning this week?
```

## Use `ST_DWithin`

For distance filtering:

```sql
ST_DWithin(...)
```

is preferred over manually comparing `ST_Distance(...)` in a filter.

## Verify with EXPLAIN

Production queries should be evaluated with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
...
```

on realistic data volumes.

---

# 41. Duplicate Reports

Multiple reports at the same location are not automatically duplicates.

Example:

```text
User A reports litter
User B reports litter
User C reports litter
```

These may be three independent observations of a real problem.

For the MVP:

> Keep all valid reports.

If duplicate submissions become a demonstrated problem, introduce a separate event-deduplication layer.

Do not silently delete raw reports.

---

# 42. Edge Cases

## Case 1 — Isolated report

```text
cluster_id = NULL
```

Keep the report.

Do not create a hotspot.

## Case 2 — Exactly minimum density

A cluster may form when the DBSCAN density condition is satisfied.

## Case 3 — Very large cluster

Investigate:

- `eps` too large;
- `minpoints` too low;
- genuinely dense area.

## Case 4 — Chain effect

DBSCAN can connect density-reachable points into a single cluster.

This is normal DBSCAN behavior.

If operational zones become too large:

- reduce `eps`;
- increase `minpoints`;
- review business zone-size constraints.

Do not silently change DBSCAN semantics.

## Case 5 — GPS noise

GPS uncertainty can separate reports from the same physical location.

Parameter tuning should consider realistic GPS accuracy.

---

# 43. Testing Strategy

The analytics implementation must include unit, integration, and analytical validation tests.

## 43.1 Unit tests

### TC-01 — Invalid latitude

Input:

```text
latitude = 100
```

Expected:

```text
excluded from clustering
```

### TC-02 — Invalid longitude

Input:

```text
longitude = -200
```

Expected:

```text
excluded from clustering
```

### TC-03 — Missing geometry

Expected:

```text
excluded from clustering
```

### TC-04 — Missing timestamp

Expected:

```text
excluded from clustering
```

---

# 44. DBSCAN Tests

## TC-05 — Isolated report

Given:

```text
one report
minpoints = 4
```

Expected:

```text
cluster_id = NULL
```

## TC-06 — Dense local group

Given:

```text
>= minpoints
```

reports sufficiently close together.

Expected:

```text
same cluster
```

## TC-07 — Distant groups

Given two dense groups separated beyond `eps`.

Expected:

```text
two different clusters
```

## TC-08 — Noise preservation

Noise reports must remain available in the report dataset.

---

# 45. Recurrence Tests

## TC-09 — No recurrence

A cluster appears in only one historical window.

Expected:

```text
recurrence_rate = 1 / N
```

## TC-10 — Persistent hotspot

A matching cluster appears in every eligible window.

Expected:

```text
recurrence_rate = 1.0
classification = Persistent
```

## TC-11 — Partial recurrence

A hotspot appears in 3 of 5 windows.

Expected:

```text
recurrence_rate = 0.60
classification = Recurring
```

under the baseline classification table.

---

# 46. Priority Score Tests

Verify:

```text
0 <= priority_score <= 1
```

for normalized inputs.

A zone with:

- more recent reports;
- higher severity;
- higher recurrence;
- newer activity

should generally receive a higher score than an otherwise comparable low-activity zone.

---

# 47. Visualization Tests

Verify:

- valid GeoJSON;
- correct SRID transformation to API output CRS;
- stable hotspot IDs;
- all required properties are present;
- polygons/points render correctly;
- tooltip fields match backend values;
- no reliance on color alone.

---

# 48. Reproducibility

Every clustering execution must record:

```text
algorithm
eps_meters
minpoints
window_start
window_end
projected_srid
input filter/version
execution timestamp
```

Example:

```json
{
  "algorithm": "DBSCAN",
  "eps_meters": 100,
  "minpoints": 4,
  "window_start": "2026-10-01T00:00:00Z",
  "window_end": "2026-10-08T00:00:00Z",
  "projected_srid": 32636
}
```

This allows the team to reproduce analytical results.

---

# 49. Data Lineage

The system should maintain this relationship:

```text
Raw Report
   |
   v
Validated Report
   |
   v
Cluster Instance
   |
   v
Hotspot Matching
   |
   v
Recurring Hotspot
   |
   v
Cleanup Priority
```

Every derived object should be traceable back to its underlying reports.

This is especially important when a cleaning team asks:

> "Why was this area classified as a hotspot?"

---

# 50. Recommended Configuration

Initial configuration:

```yaml
spatial_clustering:
  eps_meters: 100
  minpoints: 4

dynamic_cleanup:
  window_days: 7

recurring_hotspots:
  historical_window_days: 30
  bucket_days: 7
  match_radius_meters: 100
  minimum_recurrence_rate: 0.50

priority:
  recent_volume_weight: 0.40
  severity_weight: 0.25
  recurrence_weight: 0.20
  recency_weight: 0.15
```

These values are **MVP baselines**, not final scientifically validated parameters.

---

# 51. End-to-End Implementation Plan

## Phase 1 — Data Preparation

```text
1. Confirm production schema
2. Validate coordinates
3. Create spatial columns
4. Select appropriate metric CRS
5. Add indexes
```

## Phase 2 — DBSCAN MVP

```text
1. Implement 7-day filtering
2. Implement DBSCAN
3. Store cluster instances
4. Calculate cluster metrics
5. Generate GeoJSON
```

## Phase 3 — Historical Recurrence

```text
1. Generate weekly windows
2. Run DBSCAN per window
3. Store cluster instances
4. Match cluster centers
5. Build recurring hotspots
```

## Phase 4 — Prioritization

```text
1. Normalize metrics
2. Calculate priority score
3. Rank cleanup zones
```

## Phase 5 — Validation

```text
1. Tune eps/minpoints
2. Evaluate historical windows
3. Validate on holdout data
4. Inspect maps
5. Freeze baseline configuration
```

---

# 52. Monitoring Metrics

Once deployed, monitor:

```text
reports_processed
invalid_report_count
cluster_count
noise_ratio
median_cluster_size
max_cluster_size
average_cluster_compactness
recurring_hotspot_count
dynamic_cleanup_zone_count
priority_score_distribution
```

Sudden changes can indicate:

- GPS/data-quality problems;
- changes in user behavior;
- parameter problems;
- database/query issues;
- real changes in litter activity.

---

# 53. Model/Analytics Drift

The clustering system is unsupervised, but its behavior can still drift.

Monitor changes in:

- report volume;
- geographic coverage;
- reporting density;
- GPS quality;
- cluster-size distribution;
- noise ratio.

Example:

```text
Historical noise ratio: 18%
Current noise ratio:    71%
```

This should trigger investigation.

Do not automatically change `eps` without validating the reason for the change.

---

# 54. Security and Privacy Considerations

Location data may be sensitive.

The analytics layer should:

- expose only the minimum location precision required by the UI;
- avoid exposing reporter identity in public hotspot endpoints;
- apply existing CleanOps authorization rules;
- keep raw reporter identifiers out of map outputs unless explicitly required;
- retain auditability internally.

For public-facing maps, consider aggregating individual reports into zones/hotspots rather than exposing exact reporter locations.

---

# 55. Acceptance Criteria

The task is complete when all of the following are true:

### Data

- [ ] Invalid coordinates are excluded from clustering.
- [ ] Valid reports retain traceability to their original IDs.
- [ ] Metric geometry is used for distance calculations.
- [ ] Appropriate SRID is documented.

### DBSCAN

- [ ] `ST_ClusterDBSCAN` is implemented.
- [ ] `eps` is configurable.
- [ ] `minpoints` is configurable.
- [ ] DBSCAN ordering is deterministic.
- [ ] Noise reports are handled correctly.

### Dynamic Zones

- [ ] Recent reports can be clustered.
- [ ] Cluster metrics are calculated.
- [ ] Cleanup zones are map-ready.
- [ ] Priority score is explainable.

### Recurring Hotspots

- [ ] Historical windows are processed independently.
- [ ] Cluster instances are spatially matched.
- [ ] Recurrence rate is calculated.
- [ ] Stable hotspot IDs are generated.
- [ ] Hotspot classification is available.

### Tuning

- [ ] Candidate parameter grid is defined.
- [ ] Noise ratio is measured.
- [ ] Cluster size distribution is measured.
- [ ] Compactness is measured.
- [ ] Temporal stability is evaluated.
- [ ] Holdout validation is performed.

### Visualization

- [ ] Individual reports can be inspected.
- [ ] Cleanup zones can be visualized.
- [ ] Recurring hotspots can be visualized.
- [ ] Tooltips expose analytical metrics.
- [ ] Color is not the only information channel.

### Engineering

- [ ] Spatial index exists.
- [ ] Timestamp index exists.
- [ ] Query performance is checked.
- [ ] Analytical parameters are persisted.
- [ ] Results are reproducible.

---

# 56. Recommended MVP Output

The first production-quality MVP should produce:

```text
1. Dynamic Cleanup Zones
2. Recurring Litter Hotspots
3. Individual/Noise Reports
4. Cluster Metrics
5. Priority Scores
6. GeoJSON Map Output
7. Parameter Evaluation Results
```

The architecture should remain extensible so future versions can add more advanced spatial-temporal methods without rewriting the current data pipeline.

---

# 57. Future Enhancements

## Adaptive `eps`

Estimate a suitable radius from actual report distributions.

## Local density parameters

Different neighborhoods may have different natural reporting densities.

## Road-network constraints

Geographic distance does not always represent practical cleaning access.

A future version may use road/network distance where operationally necessary.

## Spatiotemporal clustering

If CleanOps later needs clustering based simultaneously on spatial and temporal proximity, evaluate a dedicated spatiotemporal method rather than manually mixing time and distance without a justified scale.

## Predictive hotspot forecasting

A future predictive model could estimate where reports are likely to appear next.

That would be a separate predictive analytics problem from the current DBSCAN task.

---

# 58. Final Architecture

```text
                         CLEANOPS REPORTING
                                |
                                v
                    +-----------------------+
                    | Raw Waste Reports     |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    | Data Quality Layer    |
                    | - coordinates         |
                    | - timestamp           |
                    | - status              |
                    | - geometry            |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    | Spatial Normalization |
                    | WGS84 -> Metric CRS   |
                    +-----------+-----------+
                                |
               +----------------+----------------+
               |                                 |
               v                                 v
     +----------------------+          +----------------------+
     | Recent 7-Day Data    |          | Historical Windows  |
     +----------+-----------+          +----------+-----------+
                |                                 |
                v                                 v
     +----------------------+          +----------------------+
     | ST_ClusterDBSCAN     |          | ST_ClusterDBSCAN     |
     +----------+-----------+          +----------+-----------+
                |                                 |
                v                                 v
     +----------------------+          +----------------------+
     | Cleanup Zones        |          | Cluster Instances    |
     +----------+-----------+          +----------+-----------+
                |                                 |
                |                                 v
                |                      +----------------------+
                |                      | Spatial Matching     |
                |                      +----------+-----------+
                |                                 |
                |                                 v
                |                      +----------------------+
                |                      | Recurring Hotspots   |
                |                      +----------+-----------+
                |                                 |
                +----------------+----------------+
                                 |
                                 v
                    +-----------------------------+
                    | Priority / Analytics Layer  |
                    +--------------+--------------+
                                   |
                    +--------------+--------------+
                    |                             |
                    v                             v
             Dashboard / Map                 Backend API
```

---

# 59. Key Design Principles

1. **Use DBSCAN for spatial density, not for recurrence itself.**
2. **Use metric geometry so `eps` has a meaningful unit.**
3. **Treat `eps` and `minpoints` as tunable configuration.**
4. **Use recent windows for operational cleanup zones.**
5. **Use independent historical windows for recurrence.**
6. **Never treat DBSCAN cluster IDs as permanent hotspot IDs.**
7. **Keep noise reports instead of deleting them.**
8. **Use explainable priority scoring.**
9. **Validate configurations on historical and holdout data.**
10. **Keep every derived result traceable to its source reports.**
11. **Design visualization around operational decisions, not only algorithm output.**
12. **Record parameters and execution metadata for reproducibility.**

---

# 60. Final Deliverable Summary

**GitHub path:**

```text
docs/design/analytics/spatial-clustering-algorithms.md
```

**Core technology:**

```text
PostgreSQL + PostGIS
```

**Core algorithm:**

```text
ST_ClusterDBSCAN
```

**Analytical layers:**

```text
Spatial Density
      +
Temporal Recurrence
      +
Operational Prioritization
```

**Primary outputs:**

```text
Dynamic Cleanup Zones
Recurring Litter Hotspots
Individual / Noise Reports
```

**Baseline configuration:**

```text
eps = 100 meters
minpoints = 4
dynamic window = 7 days
historical window = 30 days
historical bucket = 7 days
hotspot match radius = 100 meters
```

> **Important:** The baseline values above are starting points for experimentation. Final values must be selected through parameter tuning, map inspection, and holdout validation using real CleanOps data.

---

# 61. References

Official PostGIS documentation:

- `ST_ClusterDBSCAN`:  
  https://postgis.net/docs/ST_ClusterDBSCAN.html

- `ST_DWithin`:  
  https://postgis.net/docs/ST_DWithin.html

- PostGIS documentation:  
  https://postgis.net/documentation/



---

# 62. Production-Ready Tuning Implementation

The parameter-tuning section above describes the methodology. This section adds a concrete SQL implementation so the team can reproduce the comparison directly in PostgreSQL/PostGIS.

> **Performance note:** The query intentionally cross-joins the report set with the candidate parameter grid. Run it on a bounded tuning period or a representative sample, not on an unlimited production history.

## 62.1 Candidate parameter grid

```sql
WITH parameter_grid AS (
    SELECT *
    FROM (
        VALUES
            (50.0::double precision, 3),
            (50.0::double precision, 4),
            (50.0::double precision, 5),
            (75.0::double precision, 3),
            (75.0::double precision, 4),
            (75.0::double precision, 5),
            (100.0::double precision, 3),
            (100.0::double precision, 4),
            (100.0::double precision, 5),
            (100.0::double precision, 6),
            (150.0::double precision, 4),
            (150.0::double precision, 5),
            (150.0::double precision, 6),
            (200.0::double precision, 5),
            (200.0::double precision, 6),
            (200.0::double precision, 8)
    ) AS p(eps_meters, minpoints)
),

reports AS (
    SELECT
        id AS report_id,
        reported_at,
        severity,
        geom_metric AS geom
    FROM waste_reports
    WHERE reported_at >= :tuning_start
      AND reported_at <  :tuning_end
      AND status IN ('confirmed', 'open', 'in_progress')
      AND geom_metric IS NOT NULL
),

clustered AS (
    SELECT
        p.eps_meters,
        p.minpoints,
        r.report_id,
        r.reported_at,
        r.severity,
        r.geom,

        ST_ClusterDBSCAN(
            r.geom,
            eps => p.eps_meters,
            minpoints => p.minpoints
        ) OVER (
            PARTITION BY p.eps_meters, p.minpoints
            ORDER BY r.report_id
        ) AS cluster_id

    FROM reports r
    CROSS JOIN parameter_grid p
),

cluster_centers AS (
    SELECT
        eps_meters,
        minpoints,
        cluster_id,
        ST_Centroid(ST_Collect(geom)) AS center_geom,
        COUNT(*) AS cluster_size
    FROM clustered
    WHERE cluster_id IS NOT NULL
    GROUP BY
        eps_meters,
        minpoints,
        cluster_id
),

cluster_compactness AS (
    SELECT
        c.eps_meters,
        c.minpoints,
        c.cluster_id,
        c.cluster_size,
        AVG(
            ST_Distance(
                x.geom,
                c.center_geom
            )
        ) AS mean_distance_to_center_m
    FROM cluster_centers c
    JOIN clustered x
      ON x.eps_meters = c.eps_meters
     AND x.minpoints = c.minpoints
     AND x.cluster_id = c.cluster_id
    GROUP BY
        c.eps_meters,
        c.minpoints,
        c.cluster_id,
        c.cluster_size
),

configuration_metrics AS (
    SELECT
        eps_meters,
        minpoints,
        COUNT(*) AS cluster_count,
        SUM(cluster_size)::INTEGER AS clustered_report_count,
        MIN(cluster_size) AS min_cluster_size,
        PERCENTILE_CONT(0.5)
            WITHIN GROUP (ORDER BY cluster_size)
            AS median_cluster_size,
        AVG(cluster_size) AS mean_cluster_size,
        MAX(cluster_size) AS max_cluster_size,
        AVG(mean_distance_to_center_m)
            AS mean_compactness_m
    FROM cluster_compactness
    GROUP BY eps_meters, minpoints
),

total_reports AS (
    SELECT COUNT(*)::INTEGER AS total_report_count
    FROM reports
),

final_metrics AS (
    SELECT
        m.*,
        t.total_report_count,
        (
            1.0 -
            m.clustered_report_count::NUMERIC
            / NULLIF(t.total_report_count, 0)
        ) AS noise_ratio
    FROM configuration_metrics m
    CROSS JOIN total_reports t
)

SELECT
    eps_meters,
    minpoints,
    total_report_count,
    clustered_report_count,
    total_report_count - clustered_report_count AS noise_count,
    ROUND(noise_ratio, 4) AS noise_ratio,
    cluster_count,
    min_cluster_size,
    ROUND(median_cluster_size, 2) AS median_cluster_size,
    ROUND(mean_cluster_size, 2) AS mean_cluster_size,
    max_cluster_size,
    ROUND(mean_compactness_m, 2) AS mean_compactness_m
FROM final_metrics
ORDER BY
    eps_meters,
    minpoints;
```

### Interpretation

This produces one evaluation row per parameter configuration.

The output can be stored in:

```text
analytics.cluster_evaluation
```

and compared across historical windows.

### Important limitation

No single metric should automatically choose the winner.

The final configuration must satisfy both:

```text
quantitative metrics
+
map / domain validation
```

---

# 63. Production-Ready Hotspot Identity Matching

A major distinction must be maintained:

```text
DBSCAN cluster instance
        !=
persistent hotspot identity
```

The recommended matching process is deterministic and operates on **adjacent time windows**.

## 63.1 Required entities

Each historical cluster instance should have:

```text
cluster_instance_id
window_start
window_end
center_geom
report_count
avg_severity
```

Each recurring hotspot should have:

```text
hotspot_id
current_center_geom
last_window_start
recurrence_count
eligible_window_count
recurrence_rate
status
```

---

# 64. Hotspot Matching Rules

For each new time window:

### Rule 1 — Candidate generation

A current cluster can match a hotspot from the immediately previous eligible window when:

```text
ST_DWithin(
    current.center_geom,
    previous.center_geom,
    match_radius
)
```

### Rule 2 — Nearest candidate

When multiple previous hotspots are within the radius, rank them by:

```text
1. smallest center distance
2. highest previous recurrence count
3. stable hotspot_id
```

### Rule 3 — One current cluster gets one primary identity

Each current cluster receives at most one existing hotspot ID.

### Rule 4 — One previous hotspot cannot own two current clusters

If one previous hotspot is close to multiple current clusters:

- the nearest current cluster retains the existing hotspot ID;
- additional current clusters receive new hotspot IDs.

This prevents one hotspot ID from simultaneously representing two separate zones.

### Rule 5 — Merge

If multiple previous hotspots are close to one current cluster:

- retain the identity with the strongest continuity;
- mark the other previous hotspot identities as merged/inactive;
- preserve their historical records.

### Rule 6 — No candidate

If no previous hotspot is within the matching radius:

```text
create new hotspot_id
```

---

# 65. Deterministic Matching SQL

First generate candidate pairs:

```sql
SELECT
    current.cluster_instance_id,
    previous.hotspot_id,
    ST_Distance(
        current.center_geom,
        previous.center_geom
    ) AS distance_m
FROM analytics.cluster_instances current
JOIN analytics.recurring_hotspots previous
  ON previous.last_window_start = :previous_window_start
 AND ST_DWithin(
        current.center_geom,
        previous.current_center_geom,
        :match_radius_meters
    )
WHERE current.window_start = :current_window_start;
```

Rank candidates:

```sql
WITH candidate_pairs AS (
    SELECT
        current.cluster_instance_id,
        previous.hotspot_id,
        ST_Distance(
            current.center_geom,
            previous.current_center_geom
        ) AS distance_m,
        previous.recurrence_count
    FROM analytics.cluster_instances current
    JOIN analytics.recurring_hotspots previous
      ON previous.last_window_start = :previous_window_start
     AND ST_DWithin(
            current.center_geom,
            previous.current_center_geom,
            :match_radius_meters
        )
    WHERE current.window_start = :current_window_start
),

ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY cluster_instance_id
            ORDER BY
                distance_m ASC,
                recurrence_count DESC,
                hotspot_id ASC
        ) AS current_rank
    FROM candidate_pairs
)

SELECT *
FROM ranked
WHERE current_rank = 1;
```

This produces a deterministic **primary candidate** for each current cluster.

The one-to-one conflict resolution described in the previous section should then be applied in the persistence/transaction layer.

---

# 66. Hotspot Lifecycle States

A recurring hotspot should have a lifecycle.

Recommended states:

```text
NEW
ACTIVE
INACTIVE
MERGED
```

## NEW

A newly created hotspot with insufficient historical evidence.

## ACTIVE

The hotspot has a recent matching cluster.

## INACTIVE

The hotspot has not matched recent windows but is retained for historical analysis.

## MERGED

Its identity was absorbed into another hotspot because of a merge event.

Historical rows should never be deleted simply because the hotspot becomes inactive or merged.

---

# 67. Split and Merge Example

### Split

Previous window:

```text
Hotspot H-001
```

Current window:

```text
Cluster C-01
Cluster C-02
```

Both are close to H-001.

Resolution:

```text
C-01 -> H-001
C-02 -> H-NEW
```

assuming C-01 is the nearest/highest-ranked match.

### Merge

Previous window:

```text
H-001
H-002
```

Current window:

```text
C-01
```

If C-01 is within the match radius of both:

```text
C-01 -> retain strongest existing identity
other hotspot -> MERGED
```

This avoids creating unstable IDs.

---

# 68. Recurrence Calculation with Window Eligibility

A hotspot's recurrence rate must account for the number of windows in which it was eligible to exist.

Recommended formula:

```text
recurrence_rate =
    active_matching_windows
    /
    eligible_windows
```

Do not divide by the number of windows since the beginning of the entire project if the hotspot was created later.

Example:

```text
Hotspot created in Week 3
Eligible windows = Weeks 3–6 = 4
Active windows = 3

recurrence_rate = 3 / 4 = 0.75
```

This avoids unfairly penalizing newly discovered hotspots.

---

# 69. Recurrence Table Example

```text
Window | Cluster | Hotspot
-------+---------+---------
W1     | C12     | H001
W2     | C08     | H001
W3     | C14     | H001
W4     | --      | --
W5     | C21     | H001
```

For W1–W5:

```text
active windows = 4
eligible windows = 5
recurrence_rate = 0.80
```

Classification:

```text
Persistent
```

under the baseline thresholds.

---

# 70. Data Model for Traceability

To preserve analytical lineage, store a mapping table:

```text
analytics.cluster_hotspot_membership
```

Suggested columns:

```sql
CREATE TABLE analytics.cluster_hotspot_membership (
    cluster_instance_id BIGINT NOT NULL,
    hotspot_id TEXT NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    match_distance_m NUMERIC,
    match_method TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (cluster_instance_id)
);
```

Example `match_method` values:

```text
NEW
NEAREST_PREVIOUS
MERGED
```

This makes every hotspot decision auditable.

---

# 71. Hotspot Update Transaction

Hotspot matching and updates should be treated as one logical transaction:

```text
BEGIN

1. Insert current cluster instances
2. Generate candidate matches
3. Resolve one-to-one assignments
4. Update existing hotspots
5. Create new hotspots
6. Mark merged/inactive hotspots
7. Insert membership records

COMMIT
```

If any step fails:

```text
ROLLBACK
```

This prevents partially updated hotspot identities.

---

# 72. Actual Production Workflow

The final implementation should follow this sequence.

```text
                    RAW REPORTS
                         |
                         v
                +----------------+
                | Validation     |
                +-------+--------+
                        |
                        v
                +----------------+
                | Metric Geometry|
                +-------+--------+
                        |
             +----------+----------+
             |                     |
             v                     v
       Recent Window        Historical Windows
             |                     |
             v                     v
        ST_ClusterDBSCAN      ST_ClusterDBSCAN
             |                     |
             v                     v
       Cleanup Zones        Cluster Instances
             |                     |
             |                     v
             |               Candidate Matching
             |                     |
             |                     v
             |               Identity Resolution
             |                     |
             |                     v
             |               Hotspot Lifecycle
             |                     |
             +----------+----------+
                        |
                        v
                Priority Scoring
                        |
                        v
                API / GeoJSON
                        |
                        v
                  Dashboard
```

---

# 73. Final Review Checklist for Team Lead

Before opening the pull request, verify the following.

## Requirement coverage

- [x] PostGIS DBSCAN query definitions
- [x] Radius threshold tuning
- [x] Hotspot visualization specifications

## Data analysis

- [x] Data validation
- [x] Metric CRS
- [x] Time-window strategy
- [x] Noise handling
- [x] Cluster metrics
- [x] Recurrence metrics
- [x] Priority scoring
- [x] Parameter tuning
- [x] Holdout validation

## Spatial identity

- [x] Cluster instance vs hotspot separation
- [x] Cross-window matching
- [x] Deterministic matching
- [x] Split handling
- [x] Merge handling
- [x] Hotspot lifecycle
- [x] Traceability

## Engineering

- [x] SQL examples
- [x] Tuning SQL
- [x] Indexing
- [x] Performance notes
- [x] API contract
- [x] GeoJSON output
- [x] Testing
- [x] Reproducibility
- [x] Monitoring

## Visualization

- [x] Individual reports
- [x] Dynamic cleanup zones
- [x] Recurring hotspots
- [x] Map encodings
- [x] Tooltip/details specification

---

# 74. Final Recommendation

For the CleanOps graduation project, the recommended implementation boundary is:

```text
PostGIS DBSCAN
        |
        v
Cluster Instances
        |
        v
Spatial + Temporal Matching
        |
        v
Recurring Hotspots
        |
        v
Explainable Priority Score
        |
        v
Cleanup Dashboard
```

The most important implementation rule is:

> **Do not use DBSCAN cluster IDs as persistent hotspot IDs.**

DBSCAN determines spatial membership for a specific run. CleanOps must maintain hotspot identity separately across time.

The second most important rule is:

> **Do not claim the initial radius is optimal before tuning it against real project data.**

The documented baseline can be used to start development, while the tuning/evaluation pipeline provides the evidence for the final production configuration.

---

# 75. Definition of Done

The analytics deliverable is ready for implementation review when:

```text
[✓] SQL can generate spatial clusters
[✓] eps/minpoints are configurable
[✓] parameter candidates can be evaluated
[✓] cluster quality metrics are available
[✓] recent cleanup zones are defined
[✓] historical recurrence is defined
[✓] cluster-to-hotspot matching is deterministic
[✓] split/merge cases are defined
[✓] hotspot lifecycle is defined
[✓] priority score is explainable
[✓] map output is specified
[✓] GeoJSON contract is specified
[✓] test cases are defined
[✓] indexes/performance are addressed
[✓] reproducibility is addressed
[✓] data lineage is addressed
[✓] acceptance criteria are explicit
```

This document therefore covers the requested **PostGIS DBSCAN query definitions, radius threshold tuning, recurring hotspot generation, dynamic cleanup zones, and hotspot visualization specifications** required by the CleanOps analytics task.
