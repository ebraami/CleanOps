# Priority Scoring Requirements

**Project:** CleanStreet AI — Smart Citizen-Requested Street Cleaning and Waste Management Platform
**Task:** P01 — Project Foundation & Requirements / AI Requirements / Priority Scoring Requirements
**Owner:** Backend (Java / Spring Boot)
**Status:** To do → Draft for review
**Traceability:** Proposal Section 11 (AI and Intelligent Components — Tier 2), Section 15 (Data Architecture), Section 16.3 (AI-assisted decision support), Section 23 (Success Criteria)

---

## 1. Purpose

This document defines the **priority formula**, the **normalization method** applied to each input factor, and the **measurable consistency target** used to validate that the formula produces rankings a human operator would agree with. It is written so the formula can be implemented directly as a Spring Boot service (`PriorityScoringService`) against the `REPORTS` table defined in the data architecture.

Per the proposal's design principle ("AI assists, operator decides" — Section 16.3), the priority score is an **interpretable, rule-based formula**, not a learned/black-box model. Every input, weight, and output must be traceable and explainable to an operator.

---

## 2. Priority Formula

The overall priority score is a **weighted sum of four normalized factors**, each scaled to a common `[0, 1]` range before weighting so that no single factor dominates purely because it has a larger raw numeric range:

```
priority_score = (w_severity  × severity_norm)
                + (w_age       × age_norm)
                + (w_repeat    × repeat_norm)
                + (w_density   × density_norm)
```

Where:

| Symbol | Meaning | Source |
|---|---|---|
| `severity_norm` | Normalized severity of the report (waste type/amount) | AI service (Tier 1/2 output, Section 11) |
| `age_norm` | Normalized report age (time since submission) | `REPORTS.created_at` |
| `repeat_norm` | Normalized repeat-occurrence count for the location | Duplicate/related-report detection (Section 11, Tier 3) |
| `density_norm` | Normalized local report density (hotspot signal) | PostGIS spatial query (Section 15.3) |

**Constraint:** `w_severity + w_age + w_repeat + w_density = 1.0`, so `priority_score` always falls in `[0, 1]`.

**Default weights (initial, provisional — see Section 6):**

| Factor | Default Weight |
|---|---|
| Severity | 0.40 |
| Report age | 0.20 |
| Repeat occurrence | 0.20 |
| Location density | 0.20 |

These weights are explicitly **not hardcoded** — they live in a configurable table (Section 7) so they can be tuned during calibration without a code change or redeploy.

---

## 3. Factor Definitions and Normalization Method

Normalization uses **fixed min–max bounds** defined per factor (not recalculated per batch). Fixed bounds keep scores stable and comparable over time — a report's score does not silently shift just because a new, unrelated report was submitted elsewhere. All bounds are configurable, not hardcoded.

### 3.1 Severity (`severity_norm`)

- **Raw input:** `severity_score` — a weighted sum over detected waste by material type, produced by the AI service (Section 11, Tier 2).
- **Bounds:** `severity_min = 0`, `severity_max` = configurable ceiling (default `100`), representing the practical maximum a report is expected to reach given the material weight table.
- **Formula:**
  ```
  severity_norm = clamp(severity_score / severity_max, 0, 1)
  ```

### 3.2 Report Age (`age_norm`)

- **Raw input:** elapsed time since `REPORTS.created_at`, in hours, computed at scoring time (`now() - created_at`).
- **Bounds:** `age_max_hours` = configurable cap (default `336` hours / 14 days). Beyond this cap, additional age no longer increases urgency further — a report that old should already have been actioned.
- **Formula:**
  ```
  age_hours = hoursBetween(created_at, now())
  age_norm  = clamp(age_hours / age_max_hours, 0, 1)
  ```
- **Note:** because age changes continuously, this factor is recomputed at scoring/re-ranking time, not stored statically (see Section 8.3).

### 3.3 Repeat Occurrence (`repeat_norm`)

- **Raw input:** `repeat_count` — number of reports linked as duplicates/related to the same location, as surfaced (not auto-merged) by the duplicate-detection feature (Section 11, Tier 3).
- **Bounds:** `repeat_max` = configurable cap (default `10`). More than 10 linked reports is already an unambiguous hotspot and does not need to score higher still.
- **Formula:**
  ```
  repeat_norm = clamp(repeat_count / repeat_max, 0, 1)
  ```

### 3.4 Location Density (`density_norm`)

- **Raw input:** `nearby_report_count` — number of open reports within a defined radius of the report's coordinates, from the PostGIS spatial query / `ST_ClusterDBSCAN` hotspot logic (Section 15.3).
- **Bounds:** `density_radius_m` (default `150` meters) and `density_max` (default `20` nearby reports).
- **Formula:**
  ```
  density_norm = clamp(nearby_report_count / density_max, 0, 1)
  ```

### 3.5 Clamping

All four `*_norm` values are clamped to `[0, 1]` to guard against out-of-range inputs (e.g., a severity score that exceeds the configured ceiling, or a report older than the age cap).

---

## 4. Worked Example

| Factor | Raw value | Bound | Normalized |
|---|---|---|---|
| Severity | 60 | max 100 | 0.60 |
| Age | 72 hours | max 336 hours | 0.21 |
| Repeat count | 3 | max 10 | 0.30 |
| Nearby reports | 6 | max 20 | 0.30 |

```
priority_score = (0.40 × 0.60) + (0.20 × 0.21) + (0.20 × 0.30) + (0.20 × 0.30)
               = 0.24 + 0.042 + 0.06 + 0.06
               = 0.402
```

The dashboard displays this as a percentage (`40.2%`) or maps it into tiers (e.g., Low / Medium / High / Critical) for operator readability — tiering thresholds are a presentation-layer concern and out of scope for this document.

---

## 5. Consistency Target and Testing Method

**Target (per proposal Section 23):** the automated priority ranking must agree with an independent human-operator ranking on **at least 70%** of a sampled test set of reports.

### 5.1 How "agreement" is measured

Agreement is measured using **pairwise ranking concordance**, so the metric is well-defined and independent of how many reports are in the sample:

1. Draw a sample of **N reports** (recommended N ≥ 50) representative of the range of severity, age, repeat count, and density seen in the data.
2. An operator (or a small panel, with disagreements resolved by majority) manually ranks the sample from highest to lowest priority, using their normal judgment — with no visibility into the system's score, to avoid anchoring bias.
3. The system independently computes `priority_score` for the same N reports and derives its own ranking.
4. For every pair of reports `(A, B)` in the sample, the pair is **concordant** if both rankings agree on which of the two has higher priority (and **discordant** if they disagree; pairs tied by the operator are excluded from the denominator).
5. **Consistency % = concordant pairs / total comparable pairs × 100.**

This is equivalent to computing Kendall's Tau (rank correlation) and expressing it as a percentage of agreeing pairs, which is easier to explain to a non-technical reviewer than a correlation coefficient.

### 5.2 Pass criterion

The formula (and its weight configuration) is considered validated when **Consistency % ≥ 70%** on the test sample.

### 5.3 When to run this test

- Once against a synthetic/manually-labeled sample during backend development, to validate the implementation logic itself (does the code correctly compute what Section 2–3 specify).
- Again during the pilot (Section 18/23 of the proposal) against real operator rankings, to validate the **weights**, not just the code. If the pilot result falls below 70%, the weight table (Section 6) is retuned and the test re-run — the formula structure does not need to change, only the configured weights/bounds.

### 5.4 Backend responsibility

The backend exposes the raw inputs (`severity_score`, `created_at`, `repeat_count`, `nearby_report_count`) and the computed `priority_score` per report via an internal endpoint/export, so this comparison can be run reproducibly (e.g., as a CSV export or a test-support endpoint) without requiring direct database access.

---

## 6. Weight and Bound Configuration Table

To keep the formula auditable and tunable without redeploying code, weights and bounds are stored in a configuration table rather than as constants in code.

**Suggested schema — `PRIORITY_CONFIG`:**

| Column | Type | Description |
|---|---|---|
| `id` | PK | — |
| `factor_name` | varchar | `severity`, `age`, `repeat`, `density` |
| `weight` | numeric(4,3) | e.g. `0.400` |
| `min_bound` | numeric | e.g. `0` |
| `max_bound` | numeric | e.g. `100`, `336`, `10`, `20` |
| `updated_at` | timestamp | audit of last calibration change |
| `updated_by` | varchar | operator/admin who changed it |

**Validation rule:** on save, the sum of all `weight` rows must equal `1.0` (± small floating-point tolerance, e.g. `0.001`). The service layer should reject an update that breaks this invariant.

---

## 7. Spring Boot Implementation Notes

- **`PriorityConfig` entity** — maps to the `PRIORITY_CONFIG` table above; loaded once and cached, with a manual/admin-triggered refresh rather than re-querying per report scored.
- **`PriorityScoringService`** — pure computation service:
  - `double normalize(double raw, double min, double max)` — shared clamp/normalize helper used by all four factors.
  - `double computeScore(ReportScoringInput input, PriorityConfig config)` — applies Section 2's formula and returns the `[0,1]` score.
  - Stateless and unit-testable in isolation from the database (feed it plain input objects, assert expected output against the worked example in Section 4).
- **`REPORTS.priority_score`** — updated whenever: (a) the AI service writes a new `severity_score`, (b) the repeat/density signals change, or (c) a scheduled recalculation job runs to refresh `age_norm` for reports still open (age changes continuously even with no new events).
- **Recalculation trigger:** a lightweight scheduled job (e.g., every 15–30 minutes) re-scores all open reports so ranking stays current as reports age, rather than only scoring once at submission time.
- **Unit tests:** cover each normalization boundary (raw value at 0, at the cap, above the cap) and the end-to-end worked example in Section 4.
- **Consistency test harness:** a test-support endpoint or batch script that exports `(report_id, priority_score, rank)` for a given set of report IDs, to support the Section 5 validation process without manual DB queries.

---

## 8. Assumptions and Open Items

- `severity_max`, `age_max_hours`, `repeat_max`, `density_max`, and `density_radius_m` defaults above are **provisional starting points**, consistent with the proposal's statement that weights are "presented to the committee explicitly as provisional, pending calibration against pilot or operator feedback" (Section 11). They should be revisited once real pilot data is available.
- Repeat-occurrence and density inputs depend on the duplicate-detection and hotspot features (Section 11, Tier 3) being available; until those are implemented, the backend can default `repeat_count` and `nearby_report_count` to `0` so the formula degrades gracefully to severity- and age-only scoring.
- The 70% consistency target and its pass/fail interpretation should be confirmed with the team lead/supervisor before the pilot test is run, since it is the single measurable success criterion tied to this task's "Delivered means."

---

## 9. Deliverable Checklist (maps to task's "Delivered means")

- [x] Priority formula defined (Section 2)
- [x] Normalization method defined per factor (Section 3)
- [x] Measurable consistency target stated: ≥70% agreement with human-operator ranking (Section 5.2)
- [x] How the target will be tested: pairwise ranking concordance methodology (Section 5.1–5.3)
