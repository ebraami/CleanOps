# Field Cleaning-Team Mobile Architecture & Geolocation (Flutter)
### CleanStreet AI — Field Mobile Application Design

**Scope:** Architecture for the Cleaning-Team Field Mobile Application in Flutter — task execution state machine, geofencing verification, offline photo proof collection, and telemetry/GPS tracking sync.

**Dependencies:** T_85ab37 (Authentication & RBAC Specification) for team-member identity/role. API Protection and Rate Limiting Requirements is a related security dependency for token validation and secret-handling patterns; this document remains a standalone field-mobile architecture specification.

---

## 0. Source and Gap Note

The proposal specifies Flutter as the proposed mobile technology (Section 14) and the **operations dashboard** side of cleaning-team management — assignment, status updates, completion recording (Section 10) — backed by the `ASSIGNMENTS` and `CLEANING_TEAMS` tables (Section 15.2). It treats cleaning-team location as a data point to capture "where available" (Section 13) and explicitly deprioritizes route optimization as a later-phase feature (Section 19, Risks — "Routing").

**The proposal does not define a dedicated field-worker mobile application.** Everything in this document — the task execution state machine, the geofence algorithm, the offline queueing design, and the telemetry sync mechanism — is a proposed architecture built to extend the existing data model, not an elaboration of something the proposal already specifies. Where a design choice here implies a schema change (new tables/fields), that is flagged explicitly in Section 7.

---

## 1. App Overview

The Field Mobile Application is used by individual cleaning-team members to receive, execute, and close out assigned reports. It consumes the same signed-token authentication defined in the API Protection and Rate Limiting Requirements, with a team-member role claim distinct from citizen and operator *(proposed — pending T_85ab37 confirming whether this is a third `USERS.role` value or a separate team-member identity linked to `CLEANING_TEAMS`)*.

The app is designed **offline-first**: core field actions such as photo capture and telemetry collection must be able to continue locally when connectivity is unavailable, since field work routinely happens in basements, alleys, or areas with poor signal. Local status changes may be queued for synchronization, but the **backend remains authoritative for the final server-side assignment state** — a locally recorded action is not treated as officially complete until it has synced and, where applicable, been reviewed.

---

## 2. Task Execution State Machine

Each assignment (`ASSIGNMENTS` row) moves through a defined sequence of states on the field app, each gated by a specific condition:

```
Assigned → En Route → Arrived (geofence verified) → Cleaning In Progress → Completion Evidence Captured → Submitted for Review
```

| State | Entry Condition | Available Actions |
|---|---|---|
| **Assigned** | Operator assigns the report to a team (existing `ASSIGNMENTS.assigned_at`) | View task details, start navigation |
| **En Route** | Team member taps "Start Navigation" / "Heading to Site" | View live distance-to-site, cancel/reassign request |
| **Arrived** | Geofence check passes (Section 3) | Start Cleaning |
| **Cleaning In Progress** | Team member taps "Start Cleaning" (only enabled once Arrived) | Capture completion evidence, pause/report issue |
| **Completion Evidence Captured** | At least one completion photo is captured (Section 4) | Submit for review |
| **Submitted for Review** | Team member taps "Submit" | None (read-only; awaits operator review per Figure 7 "Review Completion" step) |

**Design rule:** a team member cannot skip from Assigned directly to Cleaning In Progress — the geofence check is a hard gate, not a soft confirmation, since its entire purpose is verifying physical presence before work is logged as started. "Submitted for Review" is a terminal state for the field app; the actual Resolved/Take-Further-Action decision remains the operator's, per the existing branch in the operator workflow (Figure 7) — the field app does not close its own task.

If an operator takes further action after review (e.g., the cleaning wasn't done properly), the assignment can be reopened and the state machine restarts from **Assigned** for the same or a reassigned team — consistent with the "Take Further Action" loop already shown in Figure 7.

---

## 3. Geofencing Verification

**Purpose:** prevent a team member from marking cleaning as started (or completed) without being physically at the reported location — directly supporting the proposal's "AI assists, operator decides" trust model by ensuring the *operational* record is equally trustworthy, not just the AI layer.

### 3.1 Algorithm

```
distance = haversine(device_lat, device_lng, report_lat, report_lng)

if distance <= (geofence_radius + device_gps_accuracy):
    geofence_check = PASS
else:
    geofence_check = FAIL, show distance_to_site = distance - geofence_radius
```

- **Haversine distance** is used between the device's current coordinates and the report's stored `latitude`/`longitude` (`REPORTS` table).
- **`geofence_radius`**: proposed default **50 meters**, configurable per report category or area (e.g., a large lot might warrant a wider radius than a single sidewalk location) — *(proposed default, not specified in the proposal)*.
- **`device_gps_accuracy`**: the accuracy radius reported by the device's location API is added to the allowed radius, so a device reporting ±20m accuracy isn't unfairly blocked for being technically 10m outside a strict 50m circle. This avoids false negatives caused by normal GPS imprecision rather than the team member actually being far away.
- The check is re-evaluated continuously (or on a short polling interval, e.g., every 5 seconds) while the team member is on the "Arrived" gate screen, so the "Start Cleaning" button enables automatically the moment the condition is met, without requiring a manual retry tap.

### 3.2 Failure Handling
- If the geofence check fails, the app shows the team member their current distance from the site and does not allow "Start Cleaning."
- **Proposed override path:** if a team member believes they are legitimately on-site but failing the check (e.g., GPS drift near tall buildings), they can submit a manual override request with a reason, which is logged and requires operator approval before the state can advance — this avoids a hard operational dead-end from a GPS edge case while still keeping an audit trail, rather than letting the team silently bypass the check.
- **Out of scope for this architecture:** detection of spoofed/mocked GPS locations is not addressed here. This remains a follow-on security consideration — the geofence check verifies the device's *reported* coordinates against the report location; it does not prove those coordinates are genuine.

---

## 4. Offline Photo Proof Collection

Completion evidence (photos, and optionally short video per Figure 7's "Photo/Video" label) must be capturable and stored even without connectivity, since field conditions cannot guarantee signal at the moment of capture.

**Requirements:**
- Captured photos are written to local device storage immediately upon capture, tagged with `report_id`, `assignment_id`, a locally-generated unique id, `captured_at` (device timestamp), and device GPS coordinates at time of capture.
- A **local upload queue** (proposed: SQLite or an equivalent embedded store) tracks each pending item's upload status: `pending`, `uploading`, `uploaded`, `failed`.
- The team member is **not blocked** from completing local evidence capture while an upload is pending — the UI shows a clear "syncing" indicator. However, a task must **not** be represented as server-resolved merely because evidence is stored locally; final server-side completion remains dependent on successful evidence synchronization and operator review (Section 2's state machine still requires "Submitted for Review" to mean something an operator can actually review).
- When connectivity is available, the app uploads queued items automatically using the proposed retry/backoff pattern already used for AI-service recovery (1 → 5 → 15 minutes, then every 15 minutes) as a starting point. This reuse is an implementation choice, not a hard requirement, and can be adjusted independently after field testing — photo uploads have a different size/cost profile than the AI-analysis retry queue.
- Each uploaded item carries its locally-generated unique id as an idempotency key, so a retried upload after a partial failure does not create a duplicate `IMAGES` row.
- Once uploaded, the image is stored via the existing `IMAGES` table with `image_type = "completion_evidence"` (already established in the Citizen Functions requirements), linked to the correct `report_id`.
- If a device is lost or the app is uninstalled before sync completes, locally-queued-but-unsynced evidence is lost — this is a known limitation of local-first capture, not solved by this architecture, and is noted here rather than silently assumed away.

---

## 5. Telemetry and GPS Tracking Sync

**Purpose:** provide optional, assignment-scoped location telemetry for task-progress visibility and future routing/analytics use, populating the "cleaning-team location" data point the proposal lists as a future input (Section 13). This is a proposed extension: the proposal identifies cleaning-team location as a possible data point but does not define guaranteed real-time worker tracking, and this design does not claim to provide it — see Section 5.3.

### 5.1 Tracking Window
GPS tracking is active **only while a team member has an active assignment** (En Route through Cleaning In Progress) — not as continuous, all-day background tracking of the team member's device. This is a direct application of the proposal's data-minimization principle (Section 17): location data should be collected only for what it's needed for, not indefinitely.

### 5.2 Sync Behavior
- While tracking is active, the device records a location ping on a defined interval (proposed: every 30–60 seconds, balancing live-tracking usefulness against battery drain).
- Each ping is written locally first (`assignment_id`, `latitude`, `longitude`, `accuracy`, `captured_at`), then synced to the backend in batches rather than one network call per ping, to reduce both battery and network overhead.
- If connectivity drops, pings continue to accumulate locally and are sent as a batch once connectivity resumes — the `captured_at` timestamp (not the sync time) is what's used for any later route reconstruction, so a sync delay does not distort the team's actual movement history.
- Tracking stops automatically when the assignment reaches "Submitted for Review" or is cancelled/reassigned.

### 5.3 Use and Retention
- When connectivity is available, recently synced pings may be exposed to the operator dashboard for task-progress visibility. This should be treated as **best-effort telemetry, not guaranteed real-time worker tracking** — given the offline-buffering behavior in Section 5.2, a team working through a signal-poor area will show gaps or delayed catch-up in the dashboard, which is expected behavior, not a fault.
- Raw location pings are retained only long enough to support active monitoring and short-term performance analysis, then purged or aggregated (e.g., into a total-distance or time-on-site summary) per a defined retention period — consistent with the proposal's data minimization and retention policy (Section 17). The specific retention window is a proposed operational parameter, not specified by the proposal.

---

## 6. Screens (Task Execution Flow)

| Screen | Purpose |
|---|---|
| **My Assigned Tasks** | List of reports assigned to the team member/team, sorted by priority/assignment time |
| **Task Detail** | Shows the citizen's submitted photo, category, description, and location (map view) |
| **Navigate / En Route** | Optional map/directions view while traveling to the site; starts telemetry tracking |
| **Arrival Check** | Shows live geofence status and distance-to-site; gates the "Start Cleaning" action |
| **Cleaning In Progress** | Active-task screen; access to capture completion evidence |
| **Capture Completion Evidence** | Camera capture flow; shows local upload-queue status for captured items |
| **Submit Completion** | Final review of captured evidence before submitting the task for operator review |

---

## 7. Proposed Data Model Extensions

The existing schema (Section 15.2) does not have fields for several states and events this architecture introduces. The following are proposed additions, not currently part of the data model:

| Table | Proposed New Field(s) | Purpose |
|---|---|---|
| `ASSIGNMENTS` | `started_at` (cleaning start, post-geofence-pass), `arrived_at` (geofence-pass timestamp) | Distinguish "assigned," "arrived," and "work started" as separate timestamps, beyond the existing `assigned_at`/`completed_at` |
| `IMAGES` | `upload_status` (`pending`/`uploaded`/`failed`), `local_id` (idempotency key) | Support the offline upload queue (Section 4) and prevent duplicate uploads |
| New table: `TEAM_LOCATION_PINGS` | `id`, `assignment_id` (FK), `team_id` (FK), `latitude`, `longitude`, `accuracy`, `captured_at`, `synced_at` | Store telemetry pings (Section 5), separate from the `REPORTS` table since this is a high-frequency, short-retention data stream rather than part of the report's permanent record |

---

## 8. Security Considerations

- Field-app authentication reuses the signed token validation defined in the API Protection and Rate Limiting Requirements, with role/claim verification confirming the caller is an authorized team member for the specific assignment being acted on (a team member cannot submit evidence for a report not assigned to their team).
- Any third-party mapping/navigation API key embedded in the field app (e.g., Google Maps) is a client-restricted key (domain/app-restricted, minimal scope), never the backend service-role key defined in that same specification — the two must never be the same credential.
- Location and photo data transmitted from the field app follow the same secure-transport and access-control requirements as the rest of the system (Section 17): HTTPS only, and completion-evidence images accessible only to the report's owner and authorized operators, not publicly.

---

## 9. Acceptance Conditions

| ID | Requirement | Acceptance Condition |
|---|---|---|
| AC-01 | State machine enforcement | A team member cannot advance to "Cleaning In Progress" without first passing the "Arrived" geofence check. |
| AC-02 | Geofence calculation | The geofence check correctly computes Haversine distance and accounts for device-reported GPS accuracy in its pass/fail decision. |
| AC-03 | Geofence override audit | A manual override request is logged with a reason and requires operator approval before the state advances. |
| AC-04 | Offline photo capture | A completion photo can be captured and stored locally with no network connection present. |
| AC-05 | Upload queue reliability | A queued photo automatically uploads once connectivity returns, without requiring the team member to manually retry. |
| AC-06 | No duplicate uploads | A retried upload after a partial failure does not create a duplicate `IMAGES` record, verified via the idempotency key. |
| AC-07 | Non-blocking offline UX | A team member can continue local evidence capture while uploads are pending; the UI clearly shows pending synchronization, and the server does not mark the task resolved until required evidence is synchronized and reviewed. |
| AC-08 | Telemetry window | Assignment-scoped GPS telemetry is active only during the defined active-task window, not continuous all-day tracking; any live visibility in the dashboard is best-effort, not guaranteed real-time fleet tracking. |
| AC-09 | Telemetry offline buffering | Location pings captured offline are queued locally and synced with their original capture timestamps once connectivity resumes. |
| AC-10 | Credential separation | The field app's mapping API key is verified as a distinct, client-restricted credential, never the backend service-role key. |

---

## Delivered Means

A cleaning-team mobile architecture design document covering: task execution screens (My Tasks, Task Detail, Navigate, Arrival Check, Cleaning In Progress, Capture Evidence, Submit), a defined task execution state machine with a hard geofence gate before cleaning starts and the backend remaining authoritative for final assignment state, a geofence radius check algorithm (Haversine distance plus device-accuracy tolerance, with a logged manual override path), assignment-scoped background GPS telemetry with offline buffering and best-effort (not guaranteed real-time) synchronization, and offline completion-evidence photo queueing with idempotent retry-based upload that does not mark a task server-resolved until evidence is synced and reviewed.

---

## Source Note

The proposal establishes: Flutter as the proposed mobile technology (Section 14), the operations dashboard's assignment/status/completion-recording responsibilities (Section 10), the `ASSIGNMENTS`/`CLEANING_TEAMS`/`IMAGES` schema (Section 15.2), the operator workflow's "Receive Completion Evidence" and "Review Completion" steps (Figure 7), cleaning-team location as a future data input (Section 13), and data minimization/retention as a general security principle (Section 17).

The proposal does **not** define: a dedicated field-worker mobile application, a task execution state machine, a geofencing mechanism or radius value, an offline photo-queueing design, or a telemetry sync mechanism or cadence. All of these — along with the proposed schema extensions in Section 7 — are proposed implementation requirements for this task, built to extend rather than contradict the existing architecture. This document also depends on T_85ab37 (team-member role/identity) and should be reconciled against it once available.

*End of section.*
