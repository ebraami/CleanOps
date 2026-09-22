**Duplicate / Related Report Detection Requirements**

**Objective**

Design a duplicate and related-report detection mechanism that identifies potentially duplicated incident reports using:

1. Classification embeddings
2. Spatial proximity filtering (PostGIS)
3. Temporal proximity filtering
4. Embedding similarity comparison

Detected matches will be surfaced as recommendations to operators and **will never be auto-merged**.

**Business Requirements**

**Duplicate Report**

Two reports are considered potential duplicates when:

- They describe the same incident/event.
- They are reported within a close geographic area.
- They are reported within a reasonable time window.
- Their semantic content is highly similar according to embedding similarity.

**Examples**

Duplicate:

- "Car accident on Main Street."
- "Vehicle collision on Main St causing traffic."

Related but not duplicate:

- "Traffic congestion on Main Street."
- "Car accident on Main Street."

Not duplicate:

- Similar text but different locations.
- Similar location but significantly different incident types.

**Detection Pipeline**

**Step 1: Classification Embedding Generation**

**Input**

New incident report:

JSON

{

"report\_id": 1001,

"title": "Car accident near City Mall",

"description": "Two vehicles collided near the main entrance.",

"location": "(lat,lng)",

"created\_at": "2026-09-23T12:30:00Z"

}

Show more lines

**Process**

Generate a vector embedding from:

- Incident title
- Description
- Classification metadata (if available)

Example:

Plain Text

Embedding Vector

\[0.123, 0.941, ...\]

Show more lines

**Output**

Plain Text

incident\_embedding

Show more lines

Stored with the report for later comparison.

**Step 2: Spatial Pre-Filtering (PostGIS)**

To avoid comparing against the entire dataset.

**Query Logic**

Retrieve reports within a configurable radius.

Example:

SQL

SELECT id

FROM incidents

WHERE ST\_DWithin(

location,

:incoming\_location,

500

);

Show more lines

**Configuration**

| **Parameter** | **Default** |
| --- | --- |
| Search Radius | 500 meters |

**Purpose**

Reduce the candidate set to geographically relevant incidents.

**Step 3: Temporal Pre-Filtering**

Filter candidate incidents based on creation time.

**Query Logic**

SQL

SELECT \*

FROM incidents

WHERE created\_at >=

:incoming\_time - INTERVAL '24 HOURS'

Show more lines

**Configuration**

| **Parameter** | **Default** |
| --- | --- |
| Time Window | 24 Hours |

**Purpose**

Prevent matching incidents that occurred days or weeks apart.

**Step 4: Candidate Set Creation**

Intersection of:

Plain Text

Spatial Matches

+

Temporal Matches

Show more lines

Result:

Plain Text

Candidate Reports

Show more lines

Only candidate reports proceed to semantic comparison.

**Step 5: Embedding Similarity Comparison**

Calculate cosine similarity between:

Plain Text

Incoming Report Embedding

Show more lines

and

Plain Text

Candidate Report Embeddings

Show more lines

**Formula**

Plain Text

Cosine Similarity

\=

(A · B)

/

(|A| × |B|)

Show more lines

**Output**

Plain Text

Similarity Score

0.00 → 1.00

Show more lines

**Match Classification Rules**

| **Similarity Score** | **Classification** |
| --- | --- |
| ≥ 0.90 | Strong Duplicate |
| 0.80 - 0.89 | Probable Duplicate |
| 0.70 - 0.79 | Related Report |
| < 0.70 | No Match |

**Recommendation Workflow**

**System Behavior**

When a new report is submitted:

1. Generate embedding.
2. Apply spatial filter.
3. Apply temporal filter.
4. Compare semantic similarity.
5. Rank candidates by similarity score.
6. Present recommendations to operator.

Example:

Plain Text

Possible Duplicate Reports

#8891

Similarity: 94%

#8743

Similarity: 88%

#8530

Similarity: 76%

Show more lines

**Manual Review Requirement**

The system must:

✅ Suggest duplicates

✅ Display similarity score

✅ Display matched report details

✅ Allow operator review

The system must NOT:

❌ Auto-merge reports

❌ Auto-close reports

❌ Auto-delete records

Final decision remains with the user/operator.

**Inputs**

| **Input** | **Description** |
| --- | --- |
| Title | Incident title |
| Description | Incident description |
| Latitude | Incident latitude |
| Longitude | Incident longitude |
| Created At | Report creation timestamp |
| Embedding | Generated classification embedding |

**Outputs**

| **Output** | **Description** |
| --- | --- |
| Candidate Report ID | Potential duplicate |
| Similarity Score | Semantic similarity |
| Match Type | Duplicate / Related |
| Rank | Match priority |
| Recommendation List | Reports surfaced to operator |

**Precision Target**

**Minimum Acceptance Target**

Plain Text

Precision ≥ 70%

Show more lines

Meaning:

At least 70% of reports flagged as duplicates should be confirmed by reviewers as true duplicates.

**Formula**

Plain Text

Precision

\=

True Positives

/

(True Positives + False Positives)

Show more lines

**Example**

Plain Text

100 Suggested Duplicates

75 Confirmed Duplicates

25 False Positives

Show more lines

Precision:

Plain Text

75 / 100 = 75%

Show more lines

Result:

✅ Meets requirement (>70%)

**Testing Strategy**

**Test Dataset**

Use historical incidents that have already been manually reviewed and classified.

Dataset should include:

- Known duplicates
- Related reports
- Non-duplicates

**Evaluation Process**

1. Run duplicate detection on historical data.
2. Compare system predictions with reviewer decisions.
3. Measure:
    - Precision
    - Recall
    - False Positive Rate

**Acceptance Criteria**

| **Metric** | **Target** |
| --- | --- |
| Precision | ≥ 70% |
| Spatial Search Success | 100% |
| Similarity Ranking Accuracy | Verified during UAT |
| Auto Merge Actions | 0 |
| Recommendation Availability | 100% |

**Final Solution Summary**

The duplicate-detection mechanism uses a **multi-stage filtering approach**:

1. Generate classification embeddings for every report.
2. Use PostGIS spatial filtering to find nearby incidents.
3. Apply time-window filtering to identify temporally relevant reports.
4. Compare embeddings using cosine similarity.
5. Rank matches by similarity score.
6. Surface results as operator recommendations only.
7. Maintain a minimum precision target of **70% confirmed duplicates** while ensuring no automatic merge actions are performed.
