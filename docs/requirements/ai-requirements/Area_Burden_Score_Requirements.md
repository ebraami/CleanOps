# Area Burden Score Requirements
### CleanStreet AI — Area-Level Litter Burden

**Scope:** Define the area-level burden score by aggregating the severity of open and resolved reports within each area, using decay weighting so that the score reflects **current rather than historical burden**.

---

## 1. Purpose and Source

The project proposal directly names the **Area Burden Score** feature:

> “Area burden score applies the same severity logic at the area level, aggregating open and resolved reports with a decay weighting so the score reflects current, rather than historical, burden.”

In Figure 2, the feature is classified as a **rule-based rollup**, with inputs described as **severity scores per area** and an implementation based on a **decay-weighted sum, with open reports weighted more than resolved reports**.

The proposal therefore establishes the core concept and two weighting principles:

- Report contributions should **decay over time**.
- **Open reports should contribute more than resolved reports**.

However, the proposal does **not** specify the exact mathematical formula, numerical status weights, decay function or parameter, or the exact mechanism for defining geographic areas. These values and mechanisms are therefore treated as **proposed implementation requirements**, not as already-approved proposal values.

---

# 2. Area Burden Formula

For a geographic area **A**:

\[
AreaBurden(A)=\sum_{r\in A}
[Severity(r)\times StatusWeight(r)\times DecayWeight(r)]
\]

Where:

- **Severity(r)** = the existing severity score assigned to report `r`.
- **StatusWeight(r)** = weighting based on whether the report is open or resolved.
- **DecayWeight(r)** = reduction in contribution as the report becomes older.
- **A** = the configured geographic area containing the report.

The score is intentionally **not bounded between 0 and 1**. It is an aggregate burden measure, so an area containing several active severe reports can naturally have a higher score than an area containing fewer or less severe reports.

---

# 3. Inputs

The calculation requires the following inputs:

| Input | Source / Purpose |
|---|---|
| **Report Location** | `REPORTS.latitude / longitude` — determines which area contains the report |
| **Severity Score** | Existing severity-assessment component — consumed as the report's severity value |
| **Current Status** | `REPORTS.current_status` — determines open/resolved weighting |
| **Created Timestamp** | Report record — used to calculate the age of an open report |
| **Resolved/Completion Timestamp** | `STATUS_HISTORY` — used to calculate the age of a resolved report |
| **Area Definition** | Configured geographic areas — determines report grouping |
| **Decay Parameter λ** | Configuration — controls how quickly historical influence decreases |

The architecture already supports location, status, timestamps, and spatial processing required for this calculation.

### Status Grouping

For the Area Burden Score, statuses are grouped as follows:

**Open:**
- Submitted
- Under Review
- Assigned
- In Progress

**Resolved:**
- Resolved

Every status before final resolution is treated as **Open**. Therefore, reports that are Assigned or In Progress still contribute as active unresolved burden.

---

# 4. Status Weighting

The proposed initial status weights are:

| Report Status | Status Weight |
|---|---:|
| Open | **1.0** |
| Resolved | **0.5** |

Therefore, assuming the same severity and age, an open report contributes twice as much as a resolved report.

These are **proposed calibration values** and may be adjusted after pilot testing and operational feedback.

This directly implements the proposal's requirement that open reports receive greater weight than resolved reports.

---

# 5. Decay Weighting

The proposed decay function is exponential:

\[
DecayWeight=e^{-\lambda d}
\]

Where:

- **λ** = configurable decay parameter.
- **d** = age of the report in days relative to its relevant reference timestamp.

### For Open Reports

The age is calculated from the report's creation time:

\[
d = CurrentTime - CreatedAt
\]

### For Resolved Reports

The age is calculated from the resolution/completion time:

\[
d = CurrentTime - ResolvedAt
\]

This means that once a report is resolved, its decay period starts from the time of resolution rather than continuing to age from its original creation date.

### Proposed Initial Decay Parameter

\[
\lambda=0.1
\]

The corresponding half-life is:

\[
t_{1/2}=\frac{\ln(2)}{0.1}\approx6.9\text{ days}
\]

Therefore, the contribution of a report decreases by approximately half every **6.9 days** under this initial configuration.

The value **λ = 0.1** is a **proposed initial calibration**, not a value specified by the project proposal. It should remain configurable and may be adjusted after pilot testing and operational evaluation.

---

# 6. Area Definition

The Area Burden Score requires a consistent definition of geographic areas.

The current data model contains report latitude and longitude, but a dedicated mechanism for defining named/stable areas is not explicitly specified in the proposal.

A proposed implementation can use predefined geographic areas such as:

- Service/working areas
- Administrative zones
- Fixed geographic grid cells

A report can be assigned to an area based on its stored coordinates, for example using a spatial containment rule such as:

```text
ST_Contains(area_geometry, report_location)
```

The area boundaries should remain stable so that burden values can be compared consistently over time.

A fixed geographic partition is preferable for this metric to a dynamically changing clustering method such as `ST_ClusterDBSCAN`, because dynamic clusters can change their boundaries and identities between calculations.

The exact area-partition mechanism remains an **implementation decision** rather than a requirement explicitly defined by the proposal.

---

# 7. Open vs. Resolved Reports

Both open and resolved reports contribute to the Area Burden Score.

### Open Reports

Open reports represent current unresolved burden:

\[
Weight=1.0
\]

They therefore receive the highest contribution for equivalent severity and age.

### Resolved Reports

Resolved reports still contribute because they represent recent activity in the area:

\[
Weight=0.5
\]

Their contribution then decays based on the time since resolution.

This allows the score to represent both:

- **Current unresolved burden**
- **Recent historical burden**

while preventing old resolved incidents from dominating the area score indefinitely.

---

# 8. Behavior Over Time

The Area Burden Score should behave as follows:

### New Severe Report

When a new severe report is created, the area's burden score increases according to its severity.

### Report Resolution

When a report changes from Open to Resolved:

- Its status weight changes from **1.0 → 0.5**.
- Its decay reference changes to the **resolution timestamp**.

Therefore, its contribution immediately becomes lower and subsequently decreases over time.

### Older Resolved Reports

As time passes, the contribution of resolved reports approaches zero:

\[
\lim_{d\rightarrow\infty}e^{-\lambda d}=0
\]

This prevents historical reports from maintaining a permanently high burden score.

### Quiet Area

If an area has no recent activity and no current unresolved reports, its burden score should gradually decrease toward zero.

### New Activity

A new report in the same area increases the score again, allowing the metric to respond to current conditions.

---

# 9. Relationship to Other Analytics

The Area Burden Score should remain distinct from other dashboard metrics.

| Metric | What It Measures |
|---|---|
| **Area Reporting Statistics** | Report counts/volumes |
| **Hotspot / Heatmap** | Geographic concentration/location of reports |
| **Area Resolution Rate** | Ratio of resolved reports over a defined period |
| **Resolution Performance** | Average/median time required to resolve reports |
| **Area Burden Score** | Severity + status + recency combined into a decay-weighted burden measure |

For example, hotspot analysis can identify **where reports are geographically concentrated**, while the Area Burden Score estimates **how much current burden exists in each defined area**.

The burden score is therefore a **rule-based rollup**, rather than a replacement for other operational analytics.

---

# 10. Worked Example

Consider three reports within the same area.

| Report | Severity | Status | Age | Status Weight | Decay | Contribution |
|---|---:|---|---:|---:|---:|---:|
| R1 | 0.80 | Open | 1 day | 1.0 | 0.905 | 0.72 |
| R2 | 0.60 | Open | 4 days | 1.0 | 0.670 | 0.40 |
| R3 | 0.90 | Resolved | 10 days | 0.5 | 0.368 | 0.17 |

Therefore:

\[
AreaBurden
=
(0.80\times1.0\times0.905)
+
(0.60\times1.0\times0.670)
+
(0.90\times0.5\times0.368)
\]

\[
AreaBurden\approx0.72+0.40+0.17
\]

\[
\boxed{AreaBurden\approx1.29}
\]

The calculation demonstrates that:

- Higher severity increases contribution.
- Open reports contribute more than resolved reports.
- Older reports contribute less.
- Resolved reports remain relevant for a limited period but gradually lose influence.

---

## Important Operational Limitation

An old high-severity **open** report also loses contribution because the decay function is applied to its age.

Consequently, a low Area Burden Score could represent either:

1. A genuinely quiet area, or
2. An area containing an unresolved report that has remained open for a long time.

Therefore, the Area Burden Score should **not be used as the sole indicator of operational urgency**.

A separate ageing/SLA alert can identify stalled reports. This is outside the scope of the Area Burden Score itself.

---

# 11. Recompute Cadence and Storage

The Area Burden Score should be recalculated using:

- **Scheduled recalculation:** hourly or daily.
- **Status-change recalculation:** immediately when a report changes status.

A daily scheduled recalculation is sufficient for normal decay progression, while immediate recalculation after status changes keeps the score responsive to operational events.

The calculated score can be stored per area, for example:

```text
AREAS.burden_score
AREAS.burden_updated_at
```

The following parameters should be stored in a configurable configuration table rather than hard-coded:

```text
decay_lambda
open_status_weight
resolved_status_weight
recompute_frequency
```

This allows the values to be adjusted without changing the calculation logic.

---

# 12. Configuration Summary

| Parameter | Proposed Initial Value | Configurable |
|---|---:|---|
| Open Status Weight | **1.0** | Yes |
| Resolved Status Weight | **0.5** | Yes |
| Decay Function | **Exponential** | Function can be revised if required |
| λ | **0.1** | Yes |
| Approx. Half-Life | **6.9 days** | Derived from λ |
| Recalculation | **Hourly/Daily + status change** | Yes |
| Area Assignment | **Configured geographic boundaries** | Yes |

These values are proposed implementation/calibration values and are not claimed to be explicitly specified by the project proposal.

---

# 13. Acceptance Conditions

### AC-01 — Formula
The Area Burden Score formula is documented and implemented as:

\[
AreaBurden(A)=\sum
[Severity(r)\times StatusWeight(r)\times DecayWeight(r)]
\]

### AC-02 — Geographic Grouping
Every report is aggregated into its configured geographic area.

### AC-03 — Existing Severity
The calculation uses the existing report severity score and does not create a second independent severity model.

### AC-04 — Open Weight
For otherwise identical reports, an open report contributes more than a resolved report.

### AC-05 — Resolved Inclusion
Resolved reports remain included in the score but receive a lower status weight.

### AC-06 — Age Decay
A report's contribution decreases as its reference age increases.

### AC-07 — Configuration
Decay and status-weight parameters can be configured without changing the core formula.

### AC-08 — Resolution Transition
When a report is resolved:

- Its status weight changes from Open to Resolved.
- Its decay reference changes from creation time to resolution time.

### AC-09 — Historical Burden Reduction
An old resolved-only area should have a lower burden contribution than a comparable area with recent active reports, assuming equivalent original severity.

### AC-10 — Explainability
The contribution of any individual report can be calculated and explained from its **severity, status, reference age, and active configuration parameters**.

### AC-11 — Reproducibility
Given the same report data and configuration parameters, the system produces the same Area Burden Score.

### AC-12 — Area Assignment
Each report included in the metric belongs to exactly one configured area under the selected spatial assignment rule.

### AC-13 — Dashboard Availability
The calculated Area Burden Score is available to the operations/dashboard layer without requiring a full live recalculation for every dashboard request.

---

# 14. Final Formula

The final proposed implementation is:

\[
\boxed{
AreaBurden(A)=
\sum_{r\in A}
[
Severity(r)
\times
StatusWeight(r)
\times
DecayWeight(r)
]
}
\]

Where:

\[
\boxed{
StatusWeight=
\begin{cases}
1.0 & \text{Open}\\
0.5 & \text{Resolved}
\end{cases}
}
\]

and:

\[
\boxed{
DecayWeight=e^{-\lambda d}
}
\]

with:

\[
\boxed{\lambda=0.1}
\]

giving an approximate half-life of:

\[
\boxed{6.9\text{ days}}
\]

and:

- **Open:** \(d\) is measured from `created_at`.
- **Resolved:** \(d\) is measured from the resolution/completion timestamp.

---

# 15. Delivered Means

Delivered means the project contains a documented Area Burden Score specification covering:

- The complete area-burden formula.
- Required inputs.
- Existing severity score as the severity input.
- Open/resolved status grouping.
- Open weight of **1.0** and resolved weight of **0.5**.
- Exponential decay function.
- Proposed \(\lambda=0.1\) and approximately **6.9-day half-life**.
- Different age reference for open and resolved reports.
- Proposed mechanism for assigning reports to stable geographic areas.
- Explanation of how the score differs from reporting statistics, hotspots, resolution rate, and resolution performance.
- Worked calculation example.
- Recalculation and storage approach.
- Configurable parameters.
- Acceptance conditions that make the calculation testable and reproducible.

---

# 16. Source and Implementation Boundary

The project proposal establishes the **Area Burden Score concept**, its classification as a **rule-based rollup**, the use of **severity scores per area**, decay to emphasize current rather than historical burden, and greater weighting for open reports than resolved reports.

The proposal also establishes that severity is based on the project's existing severity logic rather than requiring a separate severity model for this metric.

The proposal does **not** explicitly specify:

- The exact Area Burden Score equation.
- Open/resolved numerical weights.
- The exact decay function.
- The value of λ.
- The geographic area-boundary mechanism.
- The exact recomputation/storage implementation.

Therefore, the values **Open = 1.0, Resolved = 0.5, λ = 0.1, approximately 6.9-day half-life, and the proposed stable-area assignment mechanism** are documented here as **proposed implementation requirements/calibration choices**, not as values already approved by the proposal.
