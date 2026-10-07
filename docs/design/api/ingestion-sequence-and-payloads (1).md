# CleanStreet AI — Citizen Ingestion Sequence & API Payload Contracts

## 1. Purpose

This document defines the formal API ingestion flow for CleanStreet AI when a citizen submits a street-waste report.

The design follows the project proposal:

- Citizens submit a photo, GPS location, category, and optional description.
- PostgreSQL + PostGIS stores structured report data and spatial information.
- Firebase Storage or Amazon S3 stores uploaded images; PostgreSQL stores the resulting `storage_url`.
- The AI layer analyses the stored image and writes analysis results, including category/priority information, back into the report record.
- The operations dashboard consumes prioritised reports and supports assignment and status updates.
- AI assists decision-making; the final operational decision remains with a human operator.

---

## 2. Main Participants

| Participant | Responsibility |
|---|---|
| Citizen App | Collects report details and submits the request |
| Edge Gateway | API entry point; authenticates/authorises requests, validates the request, and routes it to backend services |
| Report Service | Creates and updates report records |
| Object Storage | Stores citizen images and later completion evidence |
| PostgreSQL + PostGIS | Stores users, reports, locations, image metadata/URLs, status history, assignments, and AI results |
| AI Service | Reads the stored image, performs waste detection/classification, and produces analysis used for prioritisation |
| Operations Dashboard | Allows operators to review, prioritise, assign, monitor, and resolve requests |
| Cleaning Team | Executes the cleaning request and uploads completion evidence |

---

## 3. High-Level Sequence

```
mermaid
sequenceDiagram
    autonumber

    actor Citizen
    participant App as Citizen App
    participant Gateway as Edge Gateway
    participant Report as Report Service
    participant Storage as Object Storage<br/>(S3 / Firebase Storage)
    participant DB as PostgreSQL + PostGIS
    participant AI as AI Service
    participant Ops as Operations Dashboard
    actor Team as Cleaning Team

    Citizen->>App: Enter report details\nphoto + GPS + category + description
    App->>Gateway: POST /api/v1/reports
    Gateway->>Gateway: Authenticate + validate request

    Gateway->>Report: Create report
    Report->>DB: INSERT report metadata
    DB-->>Report: report_id

    Report-->>Gateway: Upload instructions / report_id
    Gateway-->>App: 201 Created + report_id + upload target

    App->>Storage: Upload image
    Storage-->>App: storage_url / object key

    App->>Gateway: POST /api/v1/reports/{id}/images\nstorage reference
    Gateway->>Report: Register image
    Report->>DB: INSERT image metadata + storage_url
    DB-->>Report: image_id

    Report->>AI: Analyse report image
    AI->>Storage: Read image
    Storage-->>AI: Image
    AI->>AI: Detect + classify waste
    AI->>AI: Calculate severity / priority inputs
    AI->>DB: UPDATE report with analysis + priority
    DB-->>AI: Saved

    AI-->>Report: Analysis completed
    Report-->>Gateway: Report ready for review
    Gateway-->>App: Report status + priority

    Ops->>Gateway: GET /api/v1/reports?status=open
    Gateway->>Report: Fetch prioritised reports
    Report->>DB: Query reports by priority/location/status
    DB-->>Report: Ranked reports
    Report-->>Gateway: Ranked report list
    Gateway-->>Ops: Reports + AI analysis

    Ops->>Gateway: Assign report to cleaning team
    Gateway->>Report: POST /assignments
    Report->>DB: INSERT assignment + status history
    DB-->>Report: Assignment saved
    Report-->>Gateway: Assignment confirmed
    Gateway-->>Ops: 200 OK

    Team->>Gateway: Update progress / completion
    Gateway->>Report: Update status
    Report->>DB: UPDATE status + STATUS_HISTORY

    Team->>Storage: Upload completion evidence
    Storage-->>Team: storage_url
    Team->>Gateway: Register completion image
    Gateway->>Report: Save completion evidence
    Report->>DB: INSERT image metadata

    Report-->>Gateway: Report resolved
    Gateway-->>App: Status update + completion evidence
    App-->>Citizen: Show verified resolution
```

---

## 4. Citizen Report Ingestion Flow

### Step 1 — Submit report metadata

The citizen application sends the report information to the Edge Gateway.

**Endpoint**

`POST /api/v1/reports`

**Request**

```json
{
  "category_id": 3,
  "description": "Accumulated waste beside the sidewalk",
  "location": {
    "latitude": 29.3085,
    "longitude": 30.8428
  }
}
```

The gateway should authenticate the citizen and validate:

- authenticated user
- valid category
- valid latitude/longitude
- description length
- required fields

The server generates the `report_id` and timestamps.

---

## 5. Image Upload Contract

Images are kept outside PostgreSQL in Object Storage.

The database stores the image metadata and the storage URL/key.

### Option A — Direct upload

The backend can return an upload target:

`POST /api/v1/reports/{report_id}/upload-url`

Example response:

```json
{
  "report_id": "rep_01JABC123",
  "upload": {
    "method": "PUT",
    "object_key": "reports/rep_01JABC123/original/image_01.jpg",
    "storage_provider": "s3",
    "expires_at": "2026-10-06T18:00:00Z"
  }
}
```

The application then uploads the image directly to S3/Firebase Storage.

### Image registration

After successful upload:

`POST /api/v1/reports/{report_id}/images`

```json
{
  "image_type": "before",
  "storage_provider": "s3",
  "storage_key": "reports/rep_01JABC123/original/image_01.jpg",
  "storage_url": "https://storage.example/reports/rep_01JABC123/original/image_01.jpg"
}
```

The server must not trust a client-supplied URL blindly. It should validate that the object belongs to the expected report/user and that the object exists.

---

## 6. AI Analysis Contract

Once the image is available, the backend triggers the AI service.

**Endpoint**

`POST /internal/v1/ai/analyse-report`

```json
{
  "report_id": "rep_01JABC123",
  "image_id": "img_01JABC456",
  "image_url": "https://storage.example/reports/rep_01JABC123/original/image_01.jpg"
}
```

The AI pipeline follows the proposal's detect-then-classify design:

1. Waste detection.
2. Waste classification.
3. Severity calculation using configurable material weights.
4. Priority calculation using severity, report age, repeat occurrence, and location density.

Example response:

```json
{
  "report_id": "rep_01JABC123",
  "analysis": {
    "detected_objects": [
      {
        "label": "plastic",
        "confidence": 0.91,
        "count": 6
      },
      {
        "label": "glass",
        "confidence": 0.86,
        "count": 2
      }
    ],
    "severity_score": 0.72,
    "priority_score": 0.81,
    "classification": "mixed_waste"
  },
  "model_version": "waste-pipeline-v1",
  "analysed_at": "2026-10-06T17:30:00Z"
}
```

The AI result is written back into the report record so the report remains queryable together with its analysis.

---

## 7. Priority and Human Decision

The priority score is decision support, not an automatic final decision.

The proposal defines priority using:

- severity
- report age
- repeat occurrence
- location density
- image evidence

The operator reviews the result and can make the final operational decision.

A recommended report state sequence is:

```text
submitted
    ↓
processing
    ↓
analysed
    ↓
open
    ↓
assigned
    ↓
in_progress
    ↓
completed
    ↓
resolved
```

If the cleaning result is not satisfactory, the request can return to an active workflow instead of being closed permanently.

---

## 8. Operations API Contracts

### Get prioritised reports

`GET /api/v1/reports?status=open&sort=priority_desc`

Example response:

```json
{
  "items": [
    {
      "report_id": "rep_01JABC123",
      "category": {
        "id": 3,
        "name": "mixed_waste"
      },
      "location": {
        "latitude": 29.3085,
        "longitude": 30.8428
      },
      "priority_score": 0.81,
      "severity_score": 0.72,
      "current_status": "open",
      "repeat_count": 4,
      "created_at": "2026-10-06T17:20:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### Assign a report

`POST /api/v1/reports/{report_id}/assignments`

```json
{
  "team_id": "team_07"
}
```

Response:

```json
{
  "report_id": "rep_01JABC123",
  "team_id": "team_07",
  "status": "assigned",
  "assigned_at": "2026-10-06T18:10:00Z"
}
```

---

## 9. Status Update Contract

`PATCH /api/v1/reports/{report_id}/status`

```json
{
  "status": "in_progress",
  "note": "Cleaning team started work at the reported location."
}
```

Response:

```json
{
  "report_id": "rep_01JABC123",
  "previous_status": "assigned",
  "current_status": "in_progress",
  "changed_at": "2026-10-06T18:30:00Z"
}
```

Every important status change should create a `STATUS_HISTORY` record for audit and analytics.

---

## 10. Completion Evidence

The cleaning team uploads an after-cleaning image to Object Storage.

The image is then registered against the report:

`POST /api/v1/reports/{report_id}/images`

```json
{
  "image_type": "after",
  "storage_provider": "s3",
  "storage_key": "reports/rep_01JABC123/completion/image_01.jpg",
  "storage_url": "https://storage.example/reports/rep_01JABC123/completion/image_01.jpg"
}
```

The report can then be moved to `completed` and subsequently `resolved` after operator verification.

The citizen receives the final status and can view the completion evidence.

---

## 11. Standard Error Contract

All API errors should use a consistent structure.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The report location is required.",
    "details": [
      {
        "field": "location",
        "reason": "required"
      }
    ],
    "request_id": "req_01JXYZ789"
  }
}
```

Suggested error codes:

| HTTP | Code | Meaning |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Invalid request fields |
| 401 | `UNAUTHENTICATED` | Login/token required |
| 403 | `FORBIDDEN` | User does not have permission |
| 404 | `NOT_FOUND` | Report/resource does not exist |
| 409 | `CONFLICT` | Conflicting report/state operation |
| 413 | `FILE_TOO_LARGE` | Image exceeds upload limit |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | Unsupported image type |
| 422 | `UNPROCESSABLE_ENTITY` | Valid format but invalid business data |
| 500 | `INTERNAL_ERROR` | Unexpected server failure |
| 503 | `SERVICE_UNAVAILABLE` | Temporary dependency failure |

---

## 12. Core Database Mapping

The API contracts map to the proposal's main database tables.

| Table | API data |
|---|---|
| `USERS` | Citizen/operator identity and role |
| `CATEGORIES` | Waste/issue category |
| `REPORTS` | Report metadata, location, priority, status |
| `IMAGES` | Storage URL/key and image type |
| `STATUS_HISTORY` | Status transition audit log |
| `CLEANING_TEAMS` | Cleaning team information |
| `ASSIGNMENTS` | Report/team assignment and completion timestamps |

PostGIS is used for spatial queries such as nearby reports, duplicate/related-report detection, and hotspot analysis.

---

## 13. Security Requirements

The API should enforce:

1. Authentication for protected endpoints.
2. Role-based authorisation for citizen/operator/team actions.
3. HTTPS/TLS for API communication.
4. Server-side validation of all request data.
5. Controlled access to raw images.
6. Protection of location information.
7. Audit logging for important status changes.
8. Data minimisation and retention/deletion policies.
9. Validation of uploaded file type and size.
10. No direct exposure of private storage credentials.

Images may contain people, vehicles, or addresses; access to raw images should therefore be restricted to authorised users.

---

## 14. Idempotency and Reliability

For report creation and image registration, the API should support an idempotency mechanism to prevent duplicate submissions when a mobile client retries a request after a network interruption.

Recommended header:

`Idempotency-Key: <unique-client-generated-key>`

Example:

```http
POST /api/v1/reports
Authorization: Bearer <token>
Idempotency-Key: 5f6b2c1e-...
Content-Type: application/json
```

The backend should return the previously created result when the same idempotency key is safely retried.

---

## 15. End-to-End Contract Summary

```text
Citizen
   |
   | POST /reports
   v
Edge Gateway
   |
   +----> Report Service ----> PostgreSQL/PostGIS
   |
   +----> Object Storage (image)
   |
   +----> AI Service
              |
              +----> Object Storage (read image)
              |
              +----> PostgreSQL/PostGIS (analysis + priority)
   |
   v
Operations Dashboard
   |
   +----> Assignment
   +----> Status updates
   |
   v
Cleaning Team
   |
   +----> Completion image -> Object Storage
   +----> Completion status -> PostgreSQL
   |
   v
Citizen App
   |
   +----> Final status + completion evidence
```

---

## 16. Design Decisions

### Object Storage instead of database BLOBs

Images are stored in Firebase Storage or Amazon S3 because they are large objects. PostgreSQL stores metadata and the reference (`storage_url`) rather than the binary image itself.

### PostgreSQL + PostGIS

PostGIS provides spatial queries required for nearby-report searches, duplicate/related-report detection, and hotspot analysis.

### AI result stored with the report

The analysis and priority result are written back to the report record. This keeps incident information queryable in one place and supports later analytics and duplicate detection.

### Human-in-the-loop

AI produces analysis and decision-support scores. It does not automatically determine whether a citizen report is valid or replace the responsible operator's judgement.

### Separate detection and classification

The computer-vision pipeline uses a detect-then-classify approach because the selected datasets do not share the same class taxonomy.

---

## 17. Definition of Done

This task is complete when:

- [x] A formal UML Sequence Diagram is defined.
- [x] Citizen → Gateway → Storage → PostgreSQL ingestion flow is documented.
- [x] AI analysis flow is documented.
- [x] Operations/assignment flow is documented.
- [x] Completion evidence flow is documented.
- [x] Standard JSON request/response payloads are defined.
- [x] Standard error payload is defined.
- [x] Database table mapping is defined.
- [x] Authentication/authorisation and storage-security requirements are documented.
- [x] Status transitions and audit logging are documented.
- [x] Idempotency/retry behaviour is specified.

---

## Source Alignment

This design is based on the CleanStreet AI graduation-project proposal, especially the sections covering the proposed solution, technology/data architecture, system workflow, database entities, and security/privacy requirements.
