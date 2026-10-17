# PostGIS Spatial Modeling & Indexing Strategy

| | |
|---|---|
| **Project** | CleanOps / CleanStreet AI: Smart Citizen-Requested Street Cleaning and Waste Management Platform |
| **Task** | PostGIS Spatial Modeling & Indexing Strategy |
| **Package** | P02 — Design & Preparation → Database ERD, PostGIS Schemas & API Contracts |
| **Owner** | George Mohsen (per task card) |
| **Date** | 17 October 2026 |
| **Status** | Draft for Team Leader review |
| **Source of truth** | *CleanStreet AI Proposal (Updated)*: Section 13 (repeated reports → priority/hotspot detection), Section 15.1 (PostGIS rationale), Section 15.3 (spatial indexing requirement), Section 16.2 (operator "Check Hotspot / Repeated Reports" step) |
| **Builds on (must not contradict)** | `erd-and-data-model.md` Section 6.5 and `schema_draft.sql` (already-approved `reports.location geography(Point, 4326)` generated column and `idx_reports_location` GIST index) |

---

## 1. Purpose & Scope

This document specifies **how** the spatial column already defined in the approved schema is queried: the bounding-box pattern used for map/viewport reads, the proximity pattern used for duplicate-report and hotspot detection, and the indexing strategy that keeps both fast as report volume grows.

**In scope:** the `geography(Point, 4326)` column's exact semantics, the GIST indexing strategy, and reference query definitions for (a) nearby-report / duplicate lookups and (b) map bounding-box reads.

**Out of scope:** re-deriving the column or table design (already decided in `erd-and-data-model.md` and implemented in `schema_draft.sql` — this document only specifies how it is *used*), the priority-scoring formula itself (Proposal Section 11, a separate design surface), and the PL/pgSQL RPC wiring and API routes that will eventually call these queries (`Backend_Serverless_Architecture_and_API_Gateway_Design.md`, pattern P2 — the query definitions here are what that RPC layer will call, not a redefinition of it).

---

## 2. Conformance — this is a continuation, not a new design

Nothing here is a new spatial design. It is the specification layer the task card asks for, sitting directly on top of what the already-approved documents already built:

| Already approved (do not redefine) | Where |
|---|---|
| `reports.latitude`, `reports.longitude` — the citizen-supplied coordinates (`double precision`, validated to valid lat/lng ranges) | `schema_draft.sql`, `reports` table; `erd-and-data-model.md` Section 4 |
| `reports.location geography(Point, 4326) generated always as (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography) stored` | `schema_draft.sql`; rationale in `erd-and-data-model.md` Section 6.5 |
| `idx_reports_location` — `GIST` index on `reports.location` | `schema_draft.sql`, satisfying Proposal Section 15.3's "spatial index on latitude/longitude in REPORTS (via PostGIS)" |
| PostGIS extension enabled (`create extension if not exists postgis;`) | `schema_draft.sql` |

This document adds the query-level specification that makes that column and index actually usable: what "nearby" means, what a bounding-box read looks like, and how the GIST index is expected to serve both.

---

## 3. Spatial Column Specification

### 3.1 Type choice: `geography`, not `geometry`

| Property | `geography(Point, 4326)` (used here) | `geometry(Point, 4326)` (not used) |
|---|---|---|
| Distance unit in `ST_DWithin` / `ST_Distance` | **Meters**, calculated on the spheroid | Degrees of latitude/longitude (unless manually reprojected to a planar CRS) |
| Accuracy over the pilot's geographic extent | Correct regardless of the city/region the pilot runs in | Requires picking and maintaining a locally accurate projected SRID |
| Why this matters for CleanOps | Duplicate-detection and "reports within N meters" queries (Section 5 below) need a real distance unit the team can reason about directly (e.g. "50 meters"), not degrees | Would require an extra reprojection step the proposal does not call for |

`geography` is the right choice for a project whose risk register (Proposal Section 19) already flags "real municipal systems may not expose usable APIs" and keeps the MVP self-contained — a geography column needs no locally-chosen projection to give correct meter-based distances anywhere the pilot runs.

### 3.2 SRID: 4326 (WGS 84)

4326 is the standard GPS coordinate system (what a phone's GPS and the citizen app's `latitude`/`longitude` already produce) and the SRID already used in `schema_draft.sql`. No other SRID is introduced.

### 3.3 Why the column is *generated*, not written directly

`location` is never set by the application — it is computed automatically from `latitude`/`longitude` on every insert/update (`GENERATED ALWAYS AS ... STORED`). This means:

- The citizen app, the backend, and any future AI write-back only ever need to read/write `latitude`/`longitude` (plain numbers), exactly as Figure 5 of the proposal names them — nothing in the already-approved API design needs to change to populate `location`.
- `location` cannot drift out of sync with `latitude`/`longitude`, because PostgreSQL recomputes it from them on every write; there is no code path that can update one and forget the other.

---

## 4. GIST Indexing Strategy

### 4.1 Why GIST, not B-tree or SP-GiST

| Index type | Supports PostGIS spatial operators (`ST_DWithin`, `&&`, `ST_Contains`, …)? | Chosen? |
|---|---|---|
| B-tree | No — B-tree only orders scalar values; it cannot index a 2D point for "nearby" or "within box" queries | No |
| **GIST** | **Yes** — the standard PostGIS index type, built for exactly this: bounding-box pruning before an exact distance check | **Yes — already implemented as `idx_reports_location`** |
| SP-GiST | Yes, but tuned for different data distributions (e.g. very skewed point clusters); GIST is PostGIS's documented default and is sufficient at the pilot's scale (Proposal Section 14.2: a single-area pilot) | No — not justified at this scale |

### 4.2 How the index is actually used by a query

A GIST index on a geography column stores each point's bounding box in a tree structure. When a query runs `ST_DWithin(location, :point, :radius_meters)`, PostgreSQL's planner uses the GIST index to **first discard rows whose bounding box cannot possibly be within range** (a cheap index scan), and only then runs the exact spheroidal distance calculation on the much smaller remaining set. Without the index, every query would have to compute an exact distance against **every** row in `REPORTS` — acceptable at a few hundred rows, not at pilot scale once historical reports accumulate (Proposal Section 14.2 already budgets for growing monthly volume).

### 4.3 Maintenance

No additional maintenance step is required beyond ordinary PostgreSQL autovacuum. The index is created once (already present in `schema_draft.sql`) and updates automatically whenever `location` changes, because `location` itself only ever changes as a side effect of a `latitude`/`longitude` write.

---

## 5. Proximity Query: Nearby / Duplicate Reports

### 5.1 Purpose

Proposal Section 13 lists "repeated reports" as internal data used for "priority and hotspot detection," and Section 11's priority factors include "repeat occurrence." This query answers one question: **given a new report's location, which existing reports are close enough to plausibly be the same incident?**

### 5.2 Reference definition

```sql
-- PROPOSED reference query. Not yet wired into a PL/pgSQL RPC function —
-- that wiring belongs to the API Gateway document's pattern P2 when this
-- becomes part of create_report()'s duplicate-check step.
--
-- Finds existing reports within :radius_meters of a candidate point,
-- optionally narrowed to the same category and a recent time window.
select
    r.id,
    r.category_id,
    r.current_status,
    r.created_at,
    ST_Distance(r.location, ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography) as distance_meters
from public.reports r
where
    ST_DWithin(
        r.location,
        ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography,
        :radius_meters
    )
    and (:category_id is null or r.category_id = :category_id)
    and r.created_at >= now() - (:lookback_interval)
order by distance_meters asc;
```

**Why `ST_DWithin` and not `ST_Distance(...) < :radius_meters`:** `ST_DWithin` is what allows the GIST index to prune candidates before the exact distance calculation runs (Section 4.2). `ST_Distance(...) <` alone forces PostgreSQL to compute an exact distance for every row first, defeating the index.

### 5.3 Parameters — proposed defaults, open for Team Leader confirmation

| Parameter | Proposed default | Status |
|---|---|---|
| `radius_meters` | `50` meters | **Proposed.** No distance threshold is specified anywhere in the proposal. 50 m is a reasonable starting point for "same stretch of street," but this is a product/operations decision, not a technical one — see Open Question Q1 |
| `lookback_interval` | `72 hours` | **Proposed**, same reasoning as above — see Q1 |
| `category_id` filter | Applied when the new report's citizen-selected category is known | Matches Figure 5's `reports.category_id`; narrows false positives (e.g. a pothole report should not flag an unrelated litter report at the same corner) |

Both values are ordinary query parameters, not hard-coded constants, so they can be tuned (or made configurable per category) without a schema change once the pilot provides real data — consistent with how the API Gateway document already treats its own provisional values (rate-limit thresholds) as "data, not code" (that document, Section 7.6.3).

### 5.4 Relationship to hotspot detection

Proposal Section 16.2 names "Check hotspot / repeated reports" as an explicit operator-workflow step (Figure 7). The query in 5.2, run without a tight radius/category filter and aggregated by proximity instead of returning individual matches, is the same building block a hotspot view would use: a location with an unusually high count of `ST_DWithin` matches over a time window **is** a hotspot. This document treats hotspot detection as "the same proximity primitive, aggregated," rather than introducing a second, different spatial mechanism — one spatial query strategy serves both documented use cases (duplicate detection and hotspot detection), which keeps the design minimal, as the proposal's own feasibility assessment calls for (Section 18: "a focused minimum viable product").

A full clustering algorithm (e.g. `ST_ClusterDBSCAN`) is **not** specified here as a committed design — see Open Question Q2. `ST_ClusterDBSCAN` operates on `geometry`, not `geography`, and its `eps` parameter is in the column's native units (degrees, for SRID 4326) rather than meters, which means an accurate meter-based epsilon requires either reprojecting to a locally accurate planar SRID or approximating degrees-to-meters for the pilot's latitude. Given the proposal's assumption of "a single-area pilot deployment" (Section 14.2), a degree-based approximation is likely acceptable at MVP scale, but committing to the exact clustering function is better decided once the analytics/hotspot feature itself is scoped, not implied here as a side effect of the indexing task.

---

## 6. Bounding-Box Query: Map / Viewport Reads

### 6.1 Purpose

The operator dashboard's map view (Proposal Figure 7: "Review Requests on Map") needs to load only the reports visible in the operator's current map viewport, not the entire `REPORTS` table. This is a different access pattern from Section 5's point-radius search: it is a **rectangle**, defined by the map's visible bounds, not a radius around one point.

### 6.2 Reference definition

```sql
-- PROPOSED reference query for a map-viewport read.
-- :min_lng, :min_lat, :max_lng, :max_lat come from the client's current
-- map bounds (the SPA/dashboard already has these from the map library).
select
    r.id,
    r.latitude,
    r.longitude,
    r.category_id,
    r.priority_score,
    r.current_status
from public.reports r
where
    r.location && ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326)::geography
    and r.current_status = any(:status_filter)   -- e.g. {'NEW','ANALYZED','ASSIGNED'}
order by r.priority_score desc nulls last;
```

**Why `&&` (bounding-box overlap) instead of `ST_Contains` / `ST_Within`:** for a map viewport read, the goal is a fast, index-only pre-filter — `&&` is the operator the GIST index answers most cheaply, since it compares bounding boxes directly rather than computing exact geometric containment. For point data (every `REPORTS` row is a single point, never a polygon), a bounding-box overlap against an envelope is exactly equivalent to "the point is inside this rectangle," so no accuracy is lost by using the cheaper operator.

### 6.3 Relationship to the already-approved API design

This read matches `GET /v1/operator/map/reports`, already named in the Gateway document's route catalogue (Section 5.7) under the `heavy` rate-limit policy. This document does not add a new endpoint — it specifies the query that endpoint's handler is expected to run, filling in a detail that document deliberately left to "that domain's architecture document" (its Section 5.7 closing note).

---

## 7. Combined Indexing Behaviour

Both query patterns (Sections 5 and 6) are served by the **same single GIST index**, `idx_reports_location` — no second spatial index is introduced:

| Query pattern | Operator used | Served by `idx_reports_location`? |
|---|---|---|
| Nearby / duplicate search (point + radius) | `ST_DWithin` | Yes — bounding-box pre-filter, then exact spheroidal distance |
| Map viewport read (rectangle) | `&&` with `ST_MakeEnvelope` | Yes — direct bounding-box overlap, PostGIS's cheapest spatial test |

This is a deliberate minimalism: one spatial column, one spatial index, two query shapes built on top of it. No partial index, no second geometry column, and no separate hotspot table are introduced, consistent with the "do not over-engineer the MVP" discipline already applied in the Data Flow & Storage Architecture document.

---

## 8. Open Questions for Team Leader Review

| # | Question | Default if no decision |
|---|---|---|
| **Q1** | Are `radius_meters = 50` and `lookback_interval = 72 hours` (Section 5.3) reasonable starting thresholds for duplicate/repeat-report detection, or does the team have pilot-specific values in mind (e.g. based on the actual pilot area's street layout)? | The proposed defaults in Section 5.3, implemented as tunable query parameters, not constants |
| **Q2** | Should hotspot detection use a formal clustering function (`ST_ClusterDBSCAN`, with its geometry/degree caveats noted in Section 5.4), or is "count of nearby reports via `ST_DWithin`, aggregated" (the same primitive as duplicate detection) sufficient for the MVP's hotspot view? | Section 5.4's shared-primitive approach; no clustering function committed yet |
| **Q3** | Does `GET /v1/operator/map/reports` (Section 6.3) need server-side clustering/simplification for very dense viewports (many reports in a small area), or is a direct per-point result acceptable at the pilot's expected volume (Proposal Section 14.2: ≈570,000 monthly invocations across a small pilot, not a dense-marker problem yet)? | No clustering/simplification; direct point results, revisited if the pilot shows a need |

---

## 9. Acceptance Criteria

- [x] Specifies the spatial column already defined in `schema_draft.sql` (`geography(Point, 4326)`) without redefining or contradicting it.
- [x] Specifies the GIST index already defined in `schema_draft.sql` (`idx_reports_location`) and explains how it serves both query patterns below, without introducing a second spatial index.
- [x] Defines a bounding-box query for map/viewport reads (Section 6), matching the `GET /v1/operator/map/reports` route already named in the approved API Gateway document.
- [x] Defines a proximity ("nearby reports") query for duplicate/repeat-report detection (Section 5), traceable to Proposal Section 13's "repeated reports" and Section 11's "repeat occurrence" priority factor.
- [x] Every numeric threshold (radius, time window) is explicitly labeled proposed, not asserted as an agreed project fact.
- [x] No contradiction introduced with `erd-and-data-model.md`, `schema_draft.sql`, or `Backend_Serverless_Architecture_and_API_Gateway_Design.md` — cross-references are explicit rather than re-derived from scratch.
- [ ] Team Leader has answered Q1–Q3.
