# Citizen Mobile App Client Architecture & UML Activity Diagram
### CleanStreet AI — Citizen Flutter Application

**Repository path:** `docs/design/mobile/citizen-app-architecture.md`

**UML Activity Diagram:** Section 7 — the rendered diagram is embedded in this file (7.0), with a step-by-step description (7.0), the PlantUML source (7.5) and GitHub-rendered Mermaid versions (7.1–7.4). This file is self-contained; no separate image files are needed.

**Scope:** Architecture of the Citizen Flutter application — client-side image compression pipeline, geolocation GPS fallback algorithm, offline report queueing (SQLite/Hive), and a formal UML Activity Diagram of the citizen report-creation sequence.

**Related documents:** Citizen Functions (functions 1–15), Availability & Reliability Requirements, API Protection and Rate Limiting Requirements, Field Cleaning-Team Mobile Architecture.

---

## 0. Source and Gap Note

The proposal establishes: Flutter as the proposed mobile technology (Section 14); the citizen report inputs — photo, GPS location, category, optional description (Sections 2, 6, 10); the citizen workflow (Section 16.1, Figure 6); the `REPORTS` and `IMAGES` tables (Section 15.2); Firebase Authentication and Firebase Cloud Messaging as candidate services (Section 13); and data minimization and image-privacy principles (Sections 17, 19).

The Figma material available is the System Workflow page: the **Citizen / User Workflow** (4.1, Figure 6 in the proposal), the Operator Workflow (4.2) and AI-Assisted Decision Support (4.3). This document follows the Citizen workflow's node names and order exactly — Open app → *Have an account?* → Register → Login → Home Dashboard → Create New Report → Upload Waste Image → System Captures GPS Location → Select Waste Category → Add Optional Description → Review Report Details → Submit Report → Report Successfully Submitted → Track Report Progress → Received Notification / Updates → View Completion Evidence → Rate / Confirm Resolution (Optional). No screen-level UI designs were provided, so the screen list in Section 3 is derived from those workflow nodes rather than from visual layouts. Section 13 lists every proposal and Figma item this design relies on.

The proposal does **not** specify: an image compression pipeline, a geolocation fallback strategy, an offline queueing mechanism, a local storage technology, or a client state-management approach. All of those are **proposed implementation requirements** in this document. They are marked *(proposed)* where a specific value or technology is chosen.

---

## 1. Architectural Overview

The app uses a layered structure so that the three hard problems — image processing, location resolution, and offline delivery — are isolated from the UI and independently testable.

| Layer | Responsibility | Key components |
|---|---|---|
| **Presentation** | Screens, form state, user feedback | Report wizard screens, Report History, Report Detail, notification handling |
| **Domain** | Business rules, independent of Flutter and I/O | `CreateReportUseCase`, `ProcessImageUseCase`, `ResolveLocationUseCase`, `EnqueueReportUseCase`, `ReportValidator` |
| **Data** | Persistence and network access behind repository interfaces | `ReportRepository`, `LocalReportStore` (SQLite), `RemoteReportApi` (REST), `ImageProcessor`, `LocationService`, `AuthSession` |
| **Sync engine** | Background delivery of queued reports | `SyncWorker`, `ConnectivityMonitor`, retry scheduler |

**Proposed technology choices** (all replaceable behind the repository interfaces):

| Concern | Proposed choice |
|---|---|
| State management | Riverpod or Bloc (one adopted project-wide) |
| Camera / gallery | `image_picker` (or `camera` for in-app capture) |
| Compression | `flutter_image_compress` (native encoders, EXIF handling) |
| Location | `geolocator` + `permission_handler` |
| Connectivity | `connectivity_plus` |
| Local database | SQLite via `drift` or `sqflite` (see Section 6.1) |
| Background execution | `workmanager` (Android WorkManager / iOS BGTaskScheduler) |
| Auth / push | `firebase_auth`, `firebase_messaging` (per Section 13) |
| HTTP | `dio` with an interceptor attaching the signed bearer token |

**Design principle:** the report wizard never talks to the network directly. It always writes to the local store through `EnqueueReportUseCase`, and the sync engine is the only component that sends reports to the backend. This makes online and offline submission the **same code path** — online simply means the sync engine fires immediately.

---

## 2. Authentication and Session (Client Side)

- Login, registration, and password reset use Firebase Authentication (if adopted per Section 13) or the project's chosen auth provider, as defined in Citizen Functions 1–4.
- The HTTP client attaches the signed token as `Authorization: Bearer <token>` on every request, per the API Protection requirements. Tokens are stored in platform secure storage (Keychain / Keystore), never in plain preferences.
- A `401` response triggers **at most one** silent token refresh and retry of the same request. If refresh fails, the session is marked expired, queued items move to `paused_auth`, sync pauses, and the user is routed to login. **Queued reports are preserved**, keep their original idempotency key, and resume after re-authentication.
- A `403` is an authorization or account-state failure (for example a disabled account), **not** an expired token. It is never answered with a refresh loop; the queue pauses and the user sees an explanatory message.
- Each queued report is stamped with the `user_id` that created it. The sync engine only sends items belonging to the currently authenticated user, so a second account on the same device can never submit another user's queued report.

---

## 3. Screens (Derived from Figure 6)

| Screen | Figma node(s) — Figure 6 step | Notes |
|---|---|---|
| Splash / session check | Open CleanStreet AI Mobile Application — 1 | Restores a stored session and routes to Home, or to the account decision |
| Account decision, Register, Login, Reset | *Have an account?* → Register → Login — 2–3 | As drawn in Figure 6, Register leads into Login. Citizen Functions 1–4 |
| Home dashboard | Home Dashboard — 3 | Entry point; shows recent reports and a queued-item banner |
| Report wizard: Photo | Create New Report, Upload Waste Image — 4–5 | Mandatory; triggers the compression pipeline. MVP supports one required photo (Section 6.6 covers the multi-image extension) |
| Report wizard: Location | System Captures GPS Location — 5 | Automatic capture; runs the fallback algorithm and asks for map confirmation only when needed |
| Report wizard: Category | Select Waste Category — 5 | Required; list from `CATEGORIES` |
| Report wizard: Description | Add Optional Description — 5 | Optional; maximum 500 characters *(proposed, per Citizen Functions, Function 9)* |
| Review & Submit | Review Report Details, Submit Report — 6 | Summary of all inputs; submit enabled only when valid. Submitting sends the report for AI-assisted analysis (the Figure 6 side note) |
| Submission result | Report Successfully Submitted — 6 | Shows the server tracking ID, or a "queued" state when offline |
| Report History / Detail | Track Report Progress — 8 | Reads server data with a local cache for offline viewing; shows the visible status feedback the proposal calls the primary adoption lever (acknowledged / in progress / resolved, Section 19) |
| Notifications | Received Notification / Updates — 8 | Push via FCM; deep-links to Report Detail |
| Completion evidence & confirm | View Completion Evidence; Rate / Confirm Resolution (Optional) — 9 | Showing real cleanup evidence is the adoption mechanism named in Section 16.1; confirmation is optional |

The citizen app does not show operator-side content (priority score, hotspot checks, team assignment). Those belong to the Operator workflow (4.2) and stay on the operations dashboard.

---

## 4. Image Compression Pipeline

**Why compress on the client:** field photos from modern phones are commonly 3–12 MB. Uploading them over weak mobile connections is slow and failure-prone, and the backend enforces a size ceiling (Citizen Functions, Function 6: JPEG/PNG, e.g. 10 MB maximum). Compression must reduce size **without** degrading the visual detail the YOLOv8 detection model relies on (Section 11) — small litter objects are the hardest case.

### 4.1 Pipeline stages

```
Capture/Select → Validate → Normalize → Resize → Compress (adaptive) → Verify → Store locally
```

| Stage | Behavior |
|---|---|
| **1. Capture / select** | Camera capture or gallery pick. The original file is read once. |
| **2. Validate** | Confirm the file decodes as a real image (by content, not extension). Accepted inputs: JPEG, PNG, HEIC/HEIF. Reject anything else with a clear message. |
| **3. Normalize** | Apply EXIF orientation so the pixels are upright. Convert HEIC and PNG to JPEG. **Strip all EXIF metadata** (including embedded GPS), because location is captured separately and explicitly, and stripping supports the proposal's privacy principle (Section 17). If a trustworthy capture time is available from the picker or capture flow it is sent as a separate optional `captured_at` value; the pipeline never depends on EXIF after stripping it, and device time is treated as untrusted input. |
| **4. Resize** | If the long edge exceeds **1920 px** *(proposed)*, downscale preserving aspect ratio. Never upscale. |
| **5. Compress (adaptive)** | Encode as JPEG starting at quality **85** *(proposed)*. If the result exceeds the **target size of 2 MB** *(proposed)*, reduce quality in steps of 5 down to a floor of **60**. |
| **6. Verify** | Re-decode the output to confirm it is valid. Check final size ≤ the backend hard limit (10 MB). If still over (pathological input), reduce the long edge by 20% and repeat once; if it still fails, ask the user to retake. |
| **7. Store locally** | Write the compressed JPEG to a temporary app-private file, verify it, then atomically rename it into its final path **before** committing the queue row. If file creation or the database transaction fails, delete the orphaned temporary or final file. The queue record references only the final path. The original is not retained by the app. |

### 4.2 Rules and thresholds

| Rule | Value | Rationale |
|---|---|---|
| Max long edge | 1920 px *(proposed)* | Enough resolution for small-object detection; large savings vs. 12 MP originals |
| Minimum acceptable long edge | 640 px *(proposed)* | Below this, detection quality is unreliable — user is warned and asked to retake |
| Initial JPEG quality / floor | 85 / 60 *(proposed)* | Floor prevents compression artifacts that would hurt classification |
| Soft target size | 2 MB *(proposed)* | Fast upload on weak connections |
| Hard limit | 10 MB | Matches the backend validation in Citizen Functions, Function 6 |

### 4.3 Execution and UX
- CPU-heavy decoding and resizing run off the UI isolate where the chosen plugin supports it; native plugins may instead use native worker threads. Responsiveness is verified on target devices rather than assumed for every plugin call.
- The user sees a thumbnail and a short "Preparing photo…" indicator; the Next button is disabled until the pipeline succeeds.
- Failures (corrupt file, unsupported format, too small) return specific error messages and keep the user on the Photo step — no other entered data is lost.
- **Out of scope for the client:** face and licence-plate blurring. The proposal lists blurring as a privacy mitigation "where feasible" (Section 19); it is treated as a server-side processing step, not a client responsibility.

---

## 5. Geolocation GPS Fallback Algorithm

**Goal:** always end with either a trustworthy coordinate or an explicit user-confirmed one — never a silent bad one. Location is mandatory (Citizen Functions, Function 7): a report cannot be submitted without valid coordinates.

### 5.1 Permission and service pre-checks

```
if location services disabled      → prompt to enable; offer manual pin (Tier 5)
if permission == denied            → request permission once
if permission == deniedForever     → explain; offer "Open Settings" and manual pin (Tier 5)
else                               → proceed to Tier 1
```

### 5.2 Fallback tiers

| Tier | Source | Accept condition | Result handling |
|---|---|---|---|
| **1** | High-accuracy GPS fix, **10 s timeout** *(proposed)* | Accuracy ≤ **50 m** *(proposed)* | Accepted automatically; `location_source = gps` |
| **2** | Best sample received during the Tier 1 window | Accuracy ≤ **150 m** *(proposed)* | Pre-filled on a map; user must confirm or adjust; `gps_approx` |
| **3** | Last known device location | Age ≤ **5 min** and accuracy ≤ 150 m *(proposed)* | Pre-filled on map; user must confirm; `last_known` |
| **4** | Network/coarse location (cell/Wi-Fi) | Any (typically hundreds of metres) | **Never auto-accepted.** Pre-fills the map as a starting point; user must place or confirm the pin; `network_confirmed` |
| **5** | Manual pin on map (with address search) | User explicitly places pin | `manual_pin` |
| **Fail** | None available | — | Submit blocked; draft can still be saved |

### 5.3 Algorithm

```
function resolveLocation():
    precheckPermissionsAndServices()          # Section 5.1
    best = null

    # Tier 1 + 2: collect samples for up to 10 s
    for sample in gpsStream(timeout = 10s):
        if best == null or sample.accuracy < best.accuracy: best = sample
        if sample.accuracy <= 50: return Accept(sample, source = "gps")

    if best != null and best.accuracy <= 150:
        return ConfirmOnMap(best, source = "gps_approx")

    # Tier 3
    last = getLastKnown()
    if last != null and age(last) <= 5min and last.accuracy <= 150:
        return ConfirmOnMap(last, source = "last_known")

    # Tier 4
    coarse = getNetworkLocation()
    if coarse != null:
        return ConfirmOnMap(coarse, source = "network_confirmed")   # user must adjust/confirm

    # Tier 5
    return ManualPin()                                              # mandatory user action
```

All returned coordinates are validated before use: latitude within −90…90, longitude within −180…180, and not the exact (0, 0) "null island" default.

### 5.4 Behavioral rules
- **Accuracy and source are stored with the report** (`location_accuracy_m`, `location_source`) so operators can see how reliable a location is. These are proposed additions to the `REPORTS` table (see Section 9).
- **Freshness:** location is captured when the photo is taken. At the Review step, if the stored fix is older than **2 minutes** or the user has moved (a fresh fix differs by more than **100 m**) *(proposed)*, the app re-runs resolution before allowing submit.
- **Offline behavior:** GPS works without a data connection, so Tiers 1–3 are unaffected by being offline. Tier 5 (map) needs map tiles; if offline with no cached tiles, the app lets the user enter the report as a **draft** and complete the pin later when online rather than forcing a bad coordinate.
- Non-Tier-1 results always show a map confirmation so the user sees and owns the final position.

---

## 6. Offline Report Queueing

Because online submission also goes through the queue (Section 1), offline support is not a special mode — it is the normal architecture.

### 6.1 Storage choice: SQLite over Hive *(proposed)*

| Criterion | SQLite (`drift`/`sqflite`) | Hive |
|---|---|---|
| Relational queries (by status, by user, ordered by time) | Native | Manual filtering |
| Transactions (atomic enqueue of record + image reference) | Yes | Limited |
| Schema migrations | Mature tooling | Manual |
| Queue semantics (ordering, retry timestamps) | Straightforward | Awkward |
| Fit for report-history cache | Good | Adequate |

**Decision:** SQLite for the report queue and history cache. Hive is acceptable for small key-value settings (e.g., onboarding flags) but is not used for queue data. Because the queue stores location data and photo references, the database uses an **explicitly encrypted** SQLite implementation (for example SQLCipher) with its key held in platform secure storage *(proposed)*. Plain `sqflite` or `drift` alone does not imply encryption at rest. Photo files are protected separately: they live in app-private storage and, if the threat model requires encryption at rest, are encrypted with a key held in secure storage.

### 6.2 Local queue schema *(proposed)*

| Column | Purpose |
|---|---|
| `local_id` (UUID v4, PK) | Doubles as the **idempotency key** sent to the server |
| `user_id` | Owner; only this user's session may sync the item |
| `category_id`, `description` | Report fields |
| `latitude`, `longitude`, `location_accuracy_m`, `location_source` | Location result (Section 5) |
| `image_path` | Path to the compressed JPEG in app-private storage |
| `captured_at` | Capture time from the picker or camera when trustworthy; informational only, never used for ordering |
| `status` | `draft` · `queued` · `uploading` · `paused_auth` · `submitted` · `failed` · `expired` |
| `attempt_count`, `next_retry_at`, `last_error` | Retry bookkeeping |
| `server_report_id` / `tracking_id` | Filled in after the server accepts the report |
| `created_at`, `updated_at` | Auditing |

### 6.3 Queue item lifecycle

```
draft ──(user submits)──► queued ──(sync picks up)──► uploading ──(2xx)──► submitted
                             ▲                            │
                             │                            ├─(timeout / 5xx / no network)─► queued  (attempt++, backoff)
                             │                            ├─(429)──► queued (wait Retry-After)
                             │                            ├─(401, refresh fails)──► paused_auth ──(re-login)──► queued
                             │                            ├─(403)──► queue paused, message shown (no refresh loop)
                             │                            └─(4xx validation, incl. 413)──► failed ──(user edits)──► draft
                             └──────────── (TTL exceeded) ───────────────────────────► expired
```

A `403` is an authorization or account-state failure, not a refreshable token expiry. A `413` or other image-validation error is shown with actionable guidance (for example "retake a smaller photo") rather than a generic failure.

### 6.4 Sync engine behavior
- **Triggers:** immediately after enqueue; on connectivity regained; on app foreground; and via a periodic background task (WorkManager / BGTaskScheduler).
- **One atomic request per report:** a single multipart `POST /reports` carrying the fields, the image, and the `local_id` idempotency key. This avoids orphaned images or half-created reports that a two-step upload would risk, and keeps retries simple. (Resumable chunked upload is out of scope; the compressed image is typically ~2 MB.)
- **Idempotency:** the server de-duplicates on `local_id` (stored as `client_report_id`). For a duplicate it returns the **original** success response (same report and tracking ID) rather than an error, so the client treats a replayed request as a normal success and a lost response never creates a duplicate report.
- **Crash recovery:** on every app launch, items left in `uploading` for more than 2 minutes are reset to `queued`. Combined with idempotency, a crash or kill mid-upload cannot lose or duplicate a report.
- **Double-tap protection:** `local_id` is generated when the wizard starts, and the Submit button is disabled after the first tap, so repeated taps resolve to a single queue record.
- **Ordering:** FIFO per user, one upload at a time (avoids saturating weak connections).
- **Backoff for transient failures:** reuse the project's established pattern — 1 → 5 → 15 minutes, then every 15 minutes — as a starting point *(proposed; adjustable after field testing)*.
- **Rate-limit awareness:** the effective quota is whatever the API Protection and Rate Limiting Requirements currently specify; this document deliberately does not repeat the number, so the two cannot drift apart. On `429`, the engine honors `Retry-After`; when flushing a backlog it paces requests rather than bursting.
- **Permanent failures:** a `400`/validation error (including `413`) moves the item to `failed` with the server's field-level message; the user is notified and can edit and resubmit. A `401` that cannot be refreshed moves items to `paused_auth`, and a `403` pauses the queue (Section 2). Items are never silently dropped.
- **Expiry:** items that cannot be delivered for **7 days** *(proposed)* become `expired` and the user is notified. They are not silently deleted: enough local data is kept for the citizen to see why delivery failed and to choose to retry or discard. The TTL and the discard action are explicit product policy (Section 12).
- **Cleanup:** after a `submitted` result, the local compressed image is deleted; the history row remains as a cache.

### 6.5 User-facing behavior
- Submitting offline shows a confirmation such as **"Saved — will send when you're back online"** with a visible queued badge on Home and in History.
- **Tracking ID nuance:** the tracking ID is assigned by the server (Citizen Functions, Function 5). Offline, the app shows a local reference and a "Pending" state; the real tracking ID appears once sync succeeds. This is the one deliberate exception to "tracking ID shown immediately on submit."
- Queued items can be viewed and, while still `queued`, cancelled by the user.
- Report History and Detail screens cache the last successfully fetched data in SQLite so previously submitted reports remain viewable offline.
- **Storage guardrail:** a cap of **20 queued items** *(proposed)*; beyond that the user is asked to connect before creating more.
- **Logout with pending items:** the app warns that unsent reports exist; items remain stored (encrypted) and tied to their owner.

### 6.6 Edge Cases and Failure Handling

| Case | Handling |
|---|---|
| App killed or crashed mid-upload | Stale `uploading` items reset to `queued` on next launch; idempotency prevents duplicates (Section 6.4) |
| Phone storage nearly full | Free space is checked before compression and enqueue (proposed minimum 50 MB); if insufficient, the user gets a clear message and nothing is half-saved |
| Original photo deleted from the gallery after selection | No effect — the app keeps only its own compressed copy in private storage |
| Device clock is wrong | `captured_at` is informational only. The server's own receive time is authoritative, queue ordering uses a local sequence number rather than wall-clock time, and the server clamps future timestamps |
| Session expires while offline for days | Queue is preserved; after re-login the sync engine resumes. Items owned by a different account are untouched |
| Account disabled or password reset (403 / persistent 401) | Queue pauses and the user is told why; no items are discarded |
| Category removed server-side after the item was queued | Server returns a validation error; item moves to `failed`, the user reselects a category and resubmits. The `CATEGORIES` list is refreshed on every launch |
| Location permission revoked while a draft is open | Location resolution re-runs at the Review step (Section 5.4) |
| Backend unavailable | Treated as a transient failure — backoff and retry. AI-service downtime has **no client effect**: the report is accepted and shows "Pending AI Analysis" (Availability & Reliability Requirements) |
| iOS background execution limits | Background tasks are best-effort and not guaranteed. Foreground and connectivity-regained triggers are therefore essential, and the app shows a reminder if queued items stay undelivered for more than 24 hours |
| Data saver / metered network | Syncing respects OS network constraints; an optional "Wi-Fi only" upload setting is an open decision (Section 12) |
| Multiple images per report | The proposal's `IMAGES` table allows several images per report, but the MVP requires exactly one photo. Extending to several (proposed maximum of 5) needs a child table for queued images and a repeated pipeline run per image |

---

## 7. UML Activity Diagram — Citizen Report Creation

This section gives the citizen reporting sequence in two forms:

- **Formal UML source (Section 7.5):** a PlantUML activity diagram with three swimlanes (Citizen, Client App, Backend & AI Service), a fork/join, loops, and a response switch. It is the canonical diagram. GitHub does not render PlantUML natively, so the rendered diagram is embedded in this file as an image (Section 7.0; the image data sits at the very end of the file).
- **Mermaid diagrams (Sections 7.1–7.4):** render directly on GitHub. 7.1 is the main activity; 7.2–7.4 expand its three call-behavior nodes.

Both forms use UML activity notation (initial node ●, final nodes ◉, decision diamonds with guards, fork/join bars, partitions) and the Figure 6 node names. They map to Figure 6, steps 1–9.

### 7.0 UML Activity Diagram — rendered, and in words

![UML Activity Diagram — Citizen Report Creation][report-activity-diagram]

*Formal UML activity diagram with three swimlanes (Citizen, Client App, Backend & AI Service), rendered from the PlantUML source in Section 7.5. If your viewer does not display embedded images, use the numbered flow below or the Mermaid diagram in 7.1.*

**The same diagram as a numbered flow** (each decision, loop, fork and final node in order):

1. **Citizen:** opens the CleanStreet AI mobile app. **Client App — decision:** valid stored session? *Yes* → Home. *No* → **Citizen — decision:** have an account? *No* → Register; then Login. The Client App creates a session.
2. **Citizen:** Home Dashboard → Create New Report.
3. **Loop — repeat while the photo is rejected.** **Citizen:** uploads a waste image (capture or select). **Client App — fork, in parallel:** (a) compress the image (validate, normalize, strip EXIF, resize, compress, verify) and (b) capture the GPS location (fallback tiers 1–5). *Join* when both finish.
4. **Client App — decision:** location resolved? *No* → save a draft to resume later → **Final node (draft saved).** *Yes* → continue.
5. **Citizen:** selects the waste category and adds an optional description. **Loop — review report details**, returning to "Correct fields" until the image, location and category are all valid.
6. **Citizen:** submits the report. **Client App:** saves it to the encrypted local queue (status `queued`, with a `local_id`). **Decision:** online with a valid session? *No* → shows "Saved — will send when online".
7. **Loop — until the server accepts the report.** The Client App waits for connectivity, a retry time or re-login, then sends a multipart `POST /reports` with the `local_id`. **Backend:** validates the token, authorization, rate limit and payload. **Switch on the response:**
   - **2xx accepted:** the backend stores the report and image, de-duplicates on `local_id`, assigns the tracking ID and sends the report for AI-assisted analysis (Pending AI Analysis). The Client App marks it submitted, stores the tracking ID and deletes the local image.
   - **401:** refresh the token once; otherwise pause and prompt login.
   - **403:** pause the queue and show an account or permission message.
   - **429, 5xx or timeout:** apply `Retry-After` or backoff, then loop.
   - **4xx validation:** mark failed and show field errors. **Citizen:** corrects the report and resubmits; only then does the loop send again.
8. **Client App:** shows Report Successfully Submitted with the tracking ID.
9. **Fork, in parallel.** **Backend:** the AI detects waste, classifies it and scores severity; an operator reviews and assigns a cleaning team; the team completes the work and uploads evidence; a push notification is sent. **Citizen:** tracks report progress. *Join.*
10. **Citizen:** receives the notification or update and views the completion evidence. **Decision:** rate or confirm resolution? *Optional* → confirm. **Final node.**

### 7.1 Main activity — report creation (Mermaid)

```mermaid
flowchart TD
    START(("●  Initial"))

    subgraph CIT["Partition: Citizen"]
        C1["Open CleanStreet AI mobile app"]
        AH{"Have an account?"}
        AR["Register"]
        AL["Login"]
        C2["Create New Report"]
        C3["Upload waste image - capture or select photo"]
        C4["Select waste category"]
        C5["Add optional description"]
        C6["Review report details"]
        C7["Submit report"]
        C8["Correct fields"]
        C9["Retake or choose another photo"]
        C10["Track report progress"]
        C10B["Receive notification or update"]
        C11["View completion evidence"]
        C12["Rate or confirm resolution - optional"]
    end

    subgraph APP["Partition: Client App"]
        A1{"Valid stored session?"}
        A3["Home dashboard"]
        A4{"Image decodes and format supported?"}
        FORK["━━ Fork ━━"]
        A5[["Compress image - see 7.2"]]
        A6[["System captures GPS location - see 7.3"]]
        JOIN["━━ Join ━━"]
        A7{"Photo prepared successfully?"}
        A8{"Location resolved?"}
        A9["Save draft - resume when location is available"]
        A10{"Image, location and category all valid?"}
        A11["Enqueue in encrypted SQLite queue with local_id"]
        A12{"Online with valid session?"}
        A13["Show: Saved - will send when online"]
        A14["Wait: connectivity regained, retry timer or app foreground"]
        A15[["Sync engine sends multipart POST - see 7.4"]]
        A16{"Server response?"}
        A17["attempt plus 1, apply backoff or Retry-After"]
        A18["Mark failed, show field errors"]
        A19["Mark submitted, store tracking ID, delete local image"]
        A20["Show Report Successfully Submitted, or local notification if synced in background"]
        A21["Refresh token once; if refresh fails pause queue and prompt login"]
    end

    subgraph BE["Partition: Backend and AI Service"]
        B1["Validate token, rate limit and payload"]
        B2["Save report and image, de-duplicate on idempotency key"]
        B3["Report sent for AI-assisted analysis - status Pending AI Analysis"]
        B4["AI detects, classifies and scores severity"]
        B5["Operator reviews and assigns; cleaning team completes"]
        B6["Push notification to citizen"]
    end

    FINAL(("◉  Final"))
    DRAFT(("◉  Final - draft saved"))

    START --> C1 --> A1
    A1 -- "No" --> AH
    AH -- "No" --> AR --> AL
    AH -- "Yes" --> AL
    AL --> A3
    A1 -- "Yes" --> A3
    A3 --> C2 --> C3 --> A4
    A4 -- "No" --> C9 --> C3
    A4 -- "Yes" --> FORK
    FORK --> A5
    FORK --> A6
    A5 --> JOIN
    A6 --> JOIN
    JOIN --> A7
    A7 -- "No" --> C9
    A7 -- "Yes" --> A8
    A8 -- "No" --> A9 --> DRAFT
    A8 -- "Yes" --> C4 --> C5 --> C6 --> C7 --> A10
    A10 -- "No" --> C8 --> C6
    A10 -- "Yes" --> A11 --> A12
    A12 -- "No" --> A13 --> A14
    A12 -- "Yes" --> A15
    A14 --> A15
    A15 --> B1 --> B2 --> A16
    A16 -- "2xx accepted" --> A19 --> A20 --> B3 --> B4
    A16 -- "401" --> A21 --> A14
    A16 -- "403" --> A14
    A16 -- "Timeout, 5xx or 429" --> A17 --> A14
    A16 -- "4xx validation" --> A18 --> C8
    B4 --> B5 --> B6 --> C10 --> C10B --> C11 --> C12 --> FINAL
```

**Reading notes**
- **Account decision:** Figure 6 asks *Have an account?* and routes No → Register → Login. A stored-session check comes first (an engineering addition) so returning users skip straight to Home.
- **Fork/Join:** image compression and GPS capture run in parallel after a valid image is selected, because location acquisition (up to 10 s) would otherwise sit idle behind compression. Both must finish before the flow continues.
- **Two final nodes:** the normal path ends after the citizen has tracked the report to completion. The alternative ends with "draft saved" when no location could be resolved (for example offline with no cached map tiles). The draft is kept, not lost.
- **Queued path:** the report is stored before any network call. Offline, the citizen sees "Saved — will send when online" once, and the flow then waits on events (connectivity, timer, foreground) instead of blocking.
- **Server lane:** `B1`/`B2` are drawn on the success path for readability. A rejection at `B1` (bad token, rate limit, invalid payload) surfaces through the response decision as 401, 403, 429 or 4xx.
- **AI is asynchronous:** `B3`/`B4` happen *after* acceptance, so the citizen never waits for analysis. If the AI service is down the report stays "Pending AI Analysis" (Availability & Reliability Requirements).
- **Time scale:** `B5`–`C12` can occur hours or days after submission. They are drawn in one flow to show the full Figure 6 sequence, not to imply the citizen waits.

### 7.2 Sub-activity — image compression pipeline (node A5)

```mermaid
flowchart TD
    S(("●  Initial"))
    V1{"Decodes as JPEG, PNG or HEIC by content?"}
    N1["Apply EXIF orientation, convert HEIC and PNG to JPEG, strip all EXIF"]
    Z1{"Long edge 640 px or more?"}
    R1{"Long edge over 1920 px?"}
    R2["Downscale to 1920 px, keep aspect ratio"]
    C1["Encode JPEG at current quality - starts at 85"]
    C2{"Size 2 MB or less?"}
    C3{"Quality above floor of 60?"}
    C4["Reduce quality by 5"]
    C5{"Size 10 MB or less?"}
    C6{"Long edge already reduced once?"}
    C7["Reduce long edge by 20 percent"]
    VF["Re-decode to verify, store in app-private storage"]
    VOK{"Valid image?"}
    E1(("◉  Prepared"))
    X1(("◉  Rejected - user retakes"))

    S --> V1
    V1 -- "No" --> X1
    V1 -- "Yes" --> N1 --> Z1
    Z1 -- "No" --> X1
    Z1 -- "Yes" --> R1
    R1 -- "Yes" --> R2 --> C1
    R1 -- "No" --> C1
    C1 --> C2
    C2 -- "Yes" --> VF
    C2 -- "No" --> C3
    C3 -- "Yes" --> C4 --> C1
    C3 -- "No" --> C5
    C5 -- "Yes" --> VF
    C5 -- "No" --> C6
    C6 -- "No" --> C7 --> C1
    C6 -- "Yes" --> X1
    VF --> VOK
    VOK -- "Yes" --> E1
    VOK -- "No" --> X1
```

### 7.3 Sub-activity — location resolution with GPS fallback (node A6)

```mermaid
flowchart TD
    S(("●  Initial"))
    P{"Services on and permission granted?"}
    P1["Prompt to enable services or request permission"]
    P2{"Granted now?"}
    P3["Explain and offer Open Settings"]
    T1["Collect GPS samples for up to 10 s - tiers 1 and 2"]
    D1{"Sample with accuracy 50 m or better?"}
    D2{"Best sample 150 m or better?"}
    D3{"Last known: age 5 min or less and 150 m or better?"}
    D4{"Network location available?"}
    M1["Map pre-filled - source gps_approx"]
    M2["Map pre-filled - source last_known"]
    M3["Map pre-filled - source network_confirmed"]
    D5{"User confirmed pin?"}
    T5["Manual pin with address search - source manual_pin"]
    D6{"Map tiles available or coordinates entered?"}
    D7{"Pin placed?"}
    R1["Accept automatically - source gps"]
    V{"Latitude and longitude in range and not 0,0?"}
    E1(("◉  Resolved"))
    E2(("◉  Unresolved - draft"))

    S --> P
    P -- "No - can ask" --> P1 --> P2
    P2 -- "Yes" --> T1
    P2 -- "No" --> T5
    P -- "No - denied forever" --> P3 --> T5
    P -- "Yes" --> T1
    T1 --> D1
    D1 -- "Yes" --> R1 --> V
    D1 -- "No" --> D2
    D2 -- "Yes" --> M1 --> D5
    D2 -- "No" --> D3
    D3 -- "Yes" --> M2 --> D5
    D3 -- "No" --> D4
    D4 -- "Yes" --> M3 --> D5
    D4 -- "No" --> T5
    D5 -- "Yes" --> V
    D5 -- "No" --> T5
    T5 --> D6
    D6 -- "No" --> E2
    D6 -- "Yes" --> D7
    D7 -- "No" --> E2
    D7 -- "Yes" --> V
    V -- "Yes" --> E1
    V -- "No" --> T5
```

### 7.4 Sub-activity — sync engine (node A15)

The sync engine is a long-running background activity with **no final node**: it loops on triggers for as long as the app is installed.

```mermaid
flowchart TD
    S(("●  Initial"))
    W["Wait for trigger: enqueue, connectivity regained, app foreground, background task or retry timer"]
    Q{"Online with valid session?"}
    G["Select oldest eligible item: owner is current user, status queued, retry time passed"]
    H{"Item found?"}
    U["Set status uploading; send multipart POST with local_id"]
    R{"Response?"}
    OK["Mark submitted, save tracking ID, delete local image"]
    T["Refresh token once"]
    T2{"Refresh succeeded?"}
    PA["Mark pending items paused_auth and prompt login"]
    PF["Pause queue and show account or permission message"]
    RL["Set retry time from Retry-After"]
    BO["attempt plus 1; retry time by backoff 1, 5, 15 min then every 15 min"]
    X{"Undelivered for more than 7 days?"}
    EX["Mark expired and notify user"]
    F["Mark failed with field errors and notify user"]

    S --> W --> Q
    Q -- "No" --> W
    Q -- "Yes" --> G --> H
    H -- "No" --> W
    H -- "Yes" --> U --> R
    R -- "2xx" --> OK --> W
    R -- "401" --> T --> T2
    T2 -- "Yes" --> U
    T2 -- "No" --> PA --> W
    R -- "403" --> PF --> W
    R -- "429" --> RL --> W
    R -- "Timeout, 5xx or network error" --> BO --> X
    X -- "Yes" --> EX --> W
    X -- "No" --> W
    R -- "4xx validation incl. 413" --> F --> W
```

### 7.5 Formal UML activity diagram (PlantUML source)

```plantuml
@startuml
title CleanStreet AI - Citizen Report Creation (UML Activity Diagram)

|Citizen|
start
:Open CleanStreet AI mobile app;
|Client App|
if (Valid stored session?) then (yes)
else (no)
  |Citizen|
  if (Have an account?) then (no)
    :Register;
  else (yes)
  endif
  :Login;
  |Client App|
  :Create session;
endif
|Citizen|
:Home dashboard;
:Create New Report;
repeat
  :Upload waste image (capture or select photo);
  |Client App|
  fork
    :Compress image (sub-activity 7.2);
  fork again
    :System captures GPS location (sub-activity 7.3);
  end fork
  |Citizen|
repeat while (Photo rejected?) is (yes) not (no)
|Client App|
if (Location resolved?) then (no)
  :Save draft - resume when location is available;
  stop
else (yes)
endif
|Citizen|
:Select waste category;
:Add optional description;
repeat
  :Review report details;
backward:Correct fields;
repeat while (Image, location and category valid?) is (no) not (yes)
:Submit report;
|Client App|
:Save report to encrypted local queue (status queued, local_id);
if (Online with valid session?) then (no)
  :Show "Saved - will send when online";
else (yes)
endif
repeat
  :Wait for connectivity, retry time or re-login;
  :Send multipart POST /reports with local_id (sub-activity 7.4);
  |Backend & AI Service|
  :Validate token, authorization, rate limit and payload;
  |Client App|
  switch (Server response?)
  case (2xx accepted)
    |Backend & AI Service|
    :Persist report and image, de-duplicate on local_id;
    :Assign tracking ID;
    :Report sent for AI-assisted analysis (Pending AI Analysis);
    |Client App|
    :Mark submitted, store tracking ID, delete local image;
  case (401)
    :Refresh token once, otherwise pause and prompt login;
  case (403)
    :Pause queue and show account or permission message;
  case (429, 5xx or timeout)
    :Apply Retry-After or backoff;
  case (4xx validation)
    :Mark failed and show field errors;
    |Citizen|
    :Correct report and resubmit;
    |Client App|
  endswitch
repeat while (Accepted by server?) is (no) not (yes)
:Show Report Successfully Submitted with tracking ID;
fork
  |Backend & AI Service|
  :AI detects waste, classifies and scores severity;
  :Operator reviews and assigns cleaning team;
  :Cleaning team completes work and uploads evidence;
  :Send push notification;
fork again
  |Citizen|
  :Track report progress;
end fork
|Citizen|
:Receive notification or update;
:View completion evidence;
if (Rate or confirm resolution?) then (optional)
  :Rate or confirm resolution;
else (skip)
endif
stop
@enduml
```

**How it differs from the Mermaid diagrams:** it models the post-submission phase as a fork — the backend chain (AI analysis → operator review and assignment → cleaning and evidence → push notification) runs concurrently with the citizen tracking progress — and it keeps the delivery loop as one `repeat … while (Accepted by server?)` with a response `switch`. A validation failure sends the citizen to "Correct report and resubmit" *before* the loop sends again, so a failed item is never resent automatically.

### 7.6 Mapping to Figure 6

| Figure 6 step | Diagram 7.1 nodes |
|---|---|
| 1. Open app | `C1`, `A1` |
| 2. Register if no account | `AH`, `AR` |
| 3. Login, home dashboard | `AL`, `A1`, `A3` |
| 4. Create new report | `C2` |
| 5. Provide image, location, category, description | `C3`, `A4`–`A9` (with `A5` = 7.2 and `A6` = 7.3), `C4`, `C5` |
| 6. Review and submit | `C6`, `C7`, `A10`–`A21` (with `A15` = 7.4) |
| 7. System analyses report using AI | `B3`, `B4` |
| 8. Track report and receive updates | `B6`, `C10`, `C10B` |
| 9. View completion evidence and rate / confirm resolution | `C11`, `C12` |

---

## 8. Security and Privacy Considerations (Client)

- Tokens in Keychain/Keystore; all traffic over HTTPS; the signed-token and rate-limit behavior follows the API Protection requirements.
- The local queue database is encrypted; compressed images live in app-private storage and are deleted after a successful submit.
- EXIF metadata, including embedded GPS, is stripped from every image before it is stored or sent (Section 4.1).
- Location is collected **only** when the user is creating a report — there is no background location tracking in the citizen app. This is consistent with data minimization (Section 17) and deliberately contrasts with the assignment-scoped tracking in the field cleaning-team app.
- Any mapping SDK key embedded in the app is a platform-restricted client key and is never the backend service-role key.
- Queued items are bound to their owner's `user_id` and are never sent under a different authenticated user.

---

## 9. Proposed Data Model Extensions

| Table | Proposed new field(s) | Purpose |
|---|---|---|
| `REPORTS` | `location_source`, `location_accuracy_m` | Let operators judge how reliable a coordinate is |
| `REPORTS` | `client_report_id` (unique) | Server-side idempotency / de-duplication of retried submissions |
| `REPORTS` | `captured_at` | Preserve the device capture time separately from server `created_at`, since offline reports are created server-side later |

---

## 10. Non-Functional Targets, Localization and Accessibility *(all proposed)*

| Target | Value | Notes |
|---|---|---|
| Photo preparation time | ≤ 3 s at the 95th percentile for a 12 MP photo on a reference mid-range Android device | The reference device is to be named by the team before testing |
| Location Tier 1 wait | ≤ 10 s before the fallback UI appears | Section 5.2 |
| Enqueue latency | ≤ 500 ms from tapping Submit to the "saved" confirmation | Submission never waits on the network |
| UI responsiveness | No dropped-frame jank during compression or sync | Work runs in isolates / background workers |
| Background battery cost | No location polling outside the report wizard; sync only on triggers | See Section 8 |

**Localization:** user-facing strings are externalized from the start so a second language can be added without code changes. Whether the app ships in Arabic and English, with right-to-left layout support, is an open decision (Section 12); the proposal does not state a language requirement.

**Accessibility:** interactive controls meet a 48 dp minimum touch target, all images and icons carry semantic labels for screen readers, and status (queued, failed, submitted) is never conveyed by colour alone.

---

## 11. Testing and Verification

| Area | Approach |
|---|---|
| Image pipeline | Unit tests with fixture images: 12 MP JPEG, HEIC, PNG, tiny (< 640 px), corrupt file, EXIF-rotated, and a file with embedded GPS EXIF. Assert dimensions, size limits, quality floor, and that output contains no EXIF. Fault-injection test: fail the file write and the database commit separately and assert no orphaned file or queue row remains |
| Location resolution | Unit tests with mocked sample streams for every tier and for each permission state (granted, denied, denied-forever, services off); assert tier order, thresholds, and the 0,0 and out-of-range rejections |
| Queue and sync | Unit tests with a fake clock and a fake API covering 2xx, duplicate replay, 401 with refresh success and failure, 403 (no refresh loop), 429 with `Retry-After`, 5xx, timeout, 413, and 4xx validation. Crash-recovery test that kills the process mid-upload |
| Offline integration | On real devices: create a report in airplane mode, restore connectivity, and verify exactly one report arrives with the correct fields |
| Security | Inspect uploaded bytes for EXIF GPS; confirm the local database file is not readable as plain SQLite; confirm tokens never appear in logs |
| Device matrix | Low-end and mid-range Android; iOS if it is in MVP scope (Section 12) |
| Diagram review | Walk Figure 6 step by step against diagrams 7.1–7.5; confirm the Mermaid blocks and the PlantUML source each render without syntax errors, and that the embedded image still matches the PlantUML source |

---

## 12. Open Decisions

These items need a team decision; the document uses the stated default until then.

| # | Decision | Default used here |
|---|---|---|
| 1 | State-management library (Riverpod or Bloc) | Either; adopt one project-wide |
| 2 | SQLite library (`drift` or `sqflite`) and encryption approach (SQLCipher) | `drift` + SQLCipher |
| 3 | Map provider and offline tile strategy (Google Maps or OpenStreetMap) | Undecided; affects offline manual pin |
| 4 | Is iOS in MVP scope? The proposal allows "Flutter, or a native Android implementation" | Cross-platform, with iOS background limits handled by foreground triggers |
| 5 | Approve the offline exception to "tracking ID shown immediately on submit" | "Pending" local reference until the server assigns the ID |
| 6 | Approve the proposed `REPORTS` additions (Section 9) | Approved for design purposes |
| 7 | Languages and right-to-left support | English only until decided |
| 8 | Multiple photos per report in MVP | One photo |
| 9 | Default for the "Wi-Fi only" upload setting | Off |
| 10 | Who regenerates the embedded diagram image | Re-render and re-embed it whenever Section 7.5 changes |

---

## 13. Compatibility with the Proposal and Figma Design

| Proposal / Figma item | Where addressed | Basis |
|---|---|---|
| Flutter as the mobile technology (Section 14) | Section 1 | Direct |
| Report inputs: photo, GPS, category, optional description (Sections 2, 6, 10; Figure 6 step 5) | Sections 3, 4, 5 | Direct |
| Citizen workflow, all nine steps (Section 16.1, Figure 6) | Section 7 (7.1–7.6) | Direct |
| Registration and login; Firebase Authentication as a candidate (Sections 9, 13) | Section 2 | Direct |
| Push notifications; Firebase Cloud Messaging as a candidate (Sections 9, 13) | Section 3 (Notifications) | Direct |
| Status tracking and history of submitted reports (Section 10) | Sections 3, 6.5 | Direct |
| Completion evidence and optional confirmation (Figure 6 step 9; Section 16.1) | Section 3, diagrams 7.1 and 7.5 | Direct |
| `REPORTS`, `IMAGES`, `CATEGORIES` schema (Section 15.2) | Sections 6.2, 9 | Direct, plus four proposed `REPORTS` fields (an extension) |
| AI analysis runs after the report is stored, written back to the report (Section 15.1, Figure 4) | Diagram 7.1 (`B3`, `B4`) | Direct |
| "AI assists, operator decides"; operator-side content stays off the citizen app (Sections 16.2, 16.3) | Section 3 | Direct |
| Data minimization and image privacy (Sections 17, 19) | Sections 4.1, 8 | Direct principle |
| Out of scope respected: no physical collection, no real-time worker tracking, no routing in the citizen app (Sections 9, 19) | Section 8 | Direct |
| Image compression, GPS fallback tiers, offline queue, SQLite storage | Sections 4, 5, 6 | **Extension** — not specified in the proposal |

---

## 14. Acceptance Conditions

| ID | Requirement | Acceptance Condition |
|---|---|---|
| AC-01 | Mandatory image | The wizard cannot proceed past the Photo step without a valid, decodable image. |
| AC-02 | Compression size | For representative 12 MP test images the pipeline targets ≤ 2 MB while keeping quality at or above the floor; every accepted upload is ≤ 10 MB. The 2 MB figure is a target, not a guarantee for every image. |
| AC-03 | Detection-safe quality | Output long edge is ≤ 1920 px, JPEG quality is never below the floor of 60, and images under 640 px are rejected with a retake prompt. |
| AC-04 | Metadata stripping | Images stored and uploaded contain no EXIF GPS data. |
| AC-05 | Non-blocking processing | Compression does not freeze the UI; responsiveness is verified on the reference devices. |
| AC-06 | GPS tier order | Location resolution attempts tiers in the defined order and stops at the first acceptable result. |
| AC-07 | No silent poor location | Any location with accuracy worse than 50 m, or from network/last-known sources, requires explicit user map confirmation. |
| AC-08 | Permission handling | Denied, permanently denied, and disabled-services cases each lead to a defined path (prompt, settings, or manual pin) — never a crash or dead end. |
| AC-09 | Location recorded | Each report stores `location_source` and `location_accuracy_m`. |
| AC-10 | Offline submission | A report completed with no connectivity is saved locally and delivered automatically once connectivity returns, without user retyping. |
| AC-11 | No duplicates | A retried or replayed submission never creates a second report; the server returns the original success response. |
| AC-12 | Retry and rate limits | Transient failures retry with backoff; `429` responses honor `Retry-After`; a backlog flush stays within the quota defined in the API Protection and Rate Limiting Requirements. |
| AC-13 | No silent loss | Permanently failed or expired queue items are surfaced to the user, never silently discarded. |
| AC-14 | Tracking ID honesty | Offline items show a "Pending" local reference; the real tracking ID is displayed only after server acceptance. |
| AC-15 | Queue ownership | Queued reports are only sent under the authenticated user who created them. |
| AC-16 | Encrypted local data | The SQLite implementation is verified to encrypt at rest; photo-file protection is specified separately; local images are removed only after confirmed server acceptance. |
| AC-17 | Diagram completeness | The main activity diagram, its three sub-activity diagrams, and the formal PlantUML diagram cover every Figure 6 step (1–9), including the *Have an account?* decision and the offline, retry, 401, 403, and validation-failure branches, and all render without errors. |
| AC-18 | Crash recovery | A report in `uploading` when the app is killed is retried on next launch with no loss and no duplicate. |
| AC-19 | Double submit | Rapid repeated taps on Submit create exactly one queue record. |
| AC-20 | Storage guard | With insufficient free storage the app blocks enqueue with a clear message instead of failing midway. |
| AC-21 | Offline session expiry | If the token expires while the device is offline, queued reports stay stored and are delivered after re-login; none are lost. |
| AC-22 | Photo preparation time | A 12 MP photo is prepared within 3 s (95th percentile) on the reference mid-range device without UI jank. |
| AC-23 | Atomic image storage | Injected failures during file write or database commit leave no orphaned image file and no queue row without its image. |
| AC-24 | Auth failure handling | A `401` triggers at most one refresh per request and moves items to `paused_auth` if refresh fails; a `403` never triggers a refresh loop; queued reports survive both. |
| AC-25 | Figma conformance | The wizard and tracking flow reproduce the Figure 6 node order, with operator-only content absent from the citizen app. |

---

## Delivered Means

A citizen Flutter app architecture specification covering: a layered client architecture with a single queue-first submission path; a staged client-side image compression pipeline (validate, normalize, strip EXIF, resize, adaptive JPEG compression, verify) tuned to preserve detection quality; a five-tier geolocation fallback algorithm with explicit accept thresholds, permission handling, and stored accuracy and source; an offline report queue on encrypted SQLite with idempotent delivery, crash recovery, backoff, rate-limit awareness, and defined failure and expiry handling; edge-case, non-functional, testing, and open-decision sections; and a formal UML Activity Diagram (PlantUML source plus GitHub-rendering Mermaid versions), partitioned by Citizen / Client App / Backend & AI, mapping the full citizen reporting sequence in the exact node order of Figure 6 (steps 1–9), supported by three sub-activity diagrams for image compression, location resolution, and the sync engine, and a compatibility matrix tying every design element to the proposal or marking it as an extension.

---

## Source Note

The proposal establishes the citizen inputs (photo, GPS, category, optional description), Flutter as the proposed technology (Section 14), the citizen workflow (Figure 6), the `REPORTS`/`IMAGES` schema, Firebase Authentication and Cloud Messaging as candidate services, and the data-minimization and image-privacy principles (Sections 17 and 19).

It does **not** specify an image compression pipeline or any thresholds, a geolocation fallback strategy or accuracy values, an offline queueing design, a local storage technology, a state-management approach, performance targets, language requirements, or the proposed `REPORTS` field additions. All of these, including every numeric value marked *(proposed)*, are proposed implementation requirements that should be tuned after prototype and field testing. No screen-level Figma designs were available; screens are derived from the Figure 6 workflow nodes.

*End of document.*

<!-- Embedded diagram image for Section 7.0 (SVG, base64). Re-render from the PlantUML source in Section 7.5 if the diagram changes. -->
[report-activity-diagram]: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDYzIiBoZWlnaHQ9IjI3OTYiIHByZXNlcnZlQXNwZWN0UmF0aW89Im5vbmUiIHN0eWxlPSJ3aWR0aDozMDYzcHg7aGVpZ2h0OjI3OTZweDtiYWNrZ3JvdW5kOiNmZmYiIHZpZXdCb3g9IjAgMCAzMDYzIDI3OTYiPjx0aXRsZT5DbGVhblN0cmVldCBBSSAtIENpdGl6ZW4gUmVwb3J0IENyZWF0aW9uIChVTUwgQWN0aXZpdHkgRGlhZ3JhbSk8L3RpdGxlPjx0ZXh0IHg9IjEyNzguNjQ5IiB5PSIzMi45OTUiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjE0IiBmb250LXdlaWdodD0iYm9sZCIgdGV4dExlbmd0aD0iNTAzLjI4OSI+Q2xlYW5TdHJlZXQgQUkgLSBDaXRpemVuIFJlcG9ydCBDcmVhdGlvbiAoVU1MIEFjdGl2aXR5IERpYWdyYW0pPC90ZXh0PjxwYXRoIGZpbGw9Im5vbmUiIGQ9Ik0xNSA1MC4wNDJoMzAzMC41ODZ2MjAuOTUzSDE1eiIgc3R5bGU9InN0cm9rZTpub25lO3N0cm9rZS13aWR0aDoxIi8+PGNpcmNsZSBjeD0iMjA3Ljk1OSIgY3k9Ijg1Ljk5NSIgcj0iMTAiIGZpbGw9IiMyMjIiIHN0eWxlPSJzdHJva2U6IzIyMjtzdHJva2Utd2lkdGg6MSIvPjxyZWN0IHdpZHRoPSIyMTMuMTI1IiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTAxLjM5NyIgeT0iMTE1Ljk5NSIgZmlsbD0iI2YxZjFmMSIgcng9IjEyLjUiIHJ5PSIxMi41IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMTExLjM5NyIgeT0iMTM3LjEzNCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIHRleHRMZW5ndGg9IjE5My4xMjUiPk9wZW4gQ2xlYW5TdHJlZXQgQUkgbW9iaWxlIGFwcDwvdGV4dD48cmVjdCB3aWR0aD0iNjkuOTQ1IiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTcyLjk4NiIgeT0iMjY2Ljc2OSIgZmlsbD0iI2YxZjFmMSIgcng9IjEyLjUiIHJ5PSIxMi41IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMTgyLjk4NiIgeT0iMjg3LjkwNyIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIHRleHRMZW5ndGg9IjQ5Ljk0NSI+UmVnaXN0ZXI8L3RleHQ+PHBhdGggZmlsbD0iI2YxZjFmMSIgZD0iTTE1OC42MzEgMjE4LjM2Nmg5OC42NTZsMTIgMTItMTIgMTJoLTk4LjY1NmwtMTItMTJ6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMjExLjk1OSIgeT0iMjUyLjU3NyIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjEzLjcwMiI+bm88L3RleHQ+PHRleHQgeD0iMTU4LjYzMSIgeT0iMjM0LjE3NCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9Ijk4LjY1NiI+SGF2ZSBhbiBhY2NvdW50PzwvdGV4dD48dGV4dCB4PSIyNjkuMjg3IiB5PSIyMjcuNzcyIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMSIgdGV4dExlbmd0aD0iMTkuMDA4Ij55ZXM8L3RleHQ+PHBhdGggZmlsbD0iI2YxZjFmMSIgZD0ibTIwNy45NTkgMzIwLjczNyAxMiAxMi0xMiAxMi0xMi0xMnoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48cmVjdCB3aWR0aD0iNTIuNTg0IiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTgxLjY2NyIgeT0iMzY4LjMxOSIgZmlsbD0iI2YxZjFmMSIgcng9IjEyLjUiIHJ5PSIxMi41IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMTkxLjY2NyIgeT0iMzg5LjQ1OCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIHRleHRMZW5ndGg9IjMyLjU4NCI+TG9naW48L3RleHQ+PHJlY3Qgd2lkdGg9IjEyMi45NDMiIGhlaWdodD0iMzMuOTY5IiB4PSIxNDYuNDg3IiB5PSI1MjAuMjU3IiBmaWxsPSIjZjFmMWYxIiByeD0iMTIuNSIgcnk9IjEyLjUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIxNTYuNDg3IiB5PSI1NDEuMzk1IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMTAyLjk0MyI+SG9tZSBkYXNoYm9hcmQ8L3RleHQ+PHJlY3Qgd2lkdGg9IjEzNC4yNTgiIGhlaWdodD0iMzMuOTY5IiB4PSIxNDAuODMiIHk9IjU3NC4yMjYiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjE1MC44MyIgeT0iNTk1LjM2NCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIHRleHRMZW5ndGg9IjExNC4yNTgiPkNyZWF0ZSBOZXcgUmVwb3J0PC90ZXh0PjxyZWN0IHdpZHRoPSIyOTUuOTE4IiBoZWlnaHQ9IjMzLjk2OSIgeD0iNjAiIHk9IjY3Mi4xOTQiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjcwIiB5PSI2OTMuMzMzIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMjc1LjkxOCI+VXBsb2FkIHdhc3RlIGltYWdlIChjYXB0dXJlIG9yIHNlbGVjdCBwaG90byk8L3RleHQ+PHBhdGggZmlsbD0iI2YxZjFmMSIgZD0ibTIwNy45NTkgNjI4LjE5NCAxMiAxMi0xMiAxMi0xMi0xMnpNMTY0Ljk5IDgzMi4xMzJoODUuOTM4bDEyIDEyLTEyIDEySDE2NC45OWwtMTItMTJ6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMjExLjk1OSIgeT0iODY2LjM0MiIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjEzLjcwMiI+bm88L3RleHQ+PHRleHQgeD0iMTY0Ljk5IiB5PSI4NDcuOTQiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjExIiB0ZXh0TGVuZ3RoPSI4NS45MzgiPlBob3RvIHJlamVjdGVkPzwvdGV4dD48dGV4dCB4PSIyNjIuOTI4IiB5PSI4NDEuNTM4IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMSIgdGV4dExlbmd0aD0iMTkuMDA4Ij55ZXM8L3RleHQ+PHJlY3Qgd2lkdGg9IjE1My4xOSIgaGVpZ2h0PSIzMy45NjkiIHg9IjEzMS4zNjQiIHk9IjEwNjkuMjEzIiBmaWxsPSIjZjFmMWYxIiByeD0iMTIuNSIgcnk9IjEyLjUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIxNDEuMzY0IiB5PSIxMDkwLjM1MiIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIHRleHRMZW5ndGg9IjEzMy4xOSI+U2VsZWN0IHdhc3RlIGNhdGVnb3J5PC90ZXh0PjxyZWN0IHdpZHRoPSIxNjYuNDI2IiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTI0Ljc0NiIgeT0iMTEyMy4xODIiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjEzNC43NDYiIHk9IjExNDQuMzIxIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMTQ2LjQyNiI+QWRkIG9wdGlvbmFsIGRlc2NyaXB0aW9uPC90ZXh0PjxyZWN0IHdpZHRoPSIxNDcuODc1IiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTM0LjAyMiIgeT0iMTIyMS4xNTEiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjE0NC4wMjIiIHk9IjEyNDIuMjkiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiB0ZXh0TGVuZ3RoPSIxMjcuODc1Ij5SZXZpZXcgcmVwb3J0IGRldGFpbHM8L3RleHQ+PHBhdGggZmlsbD0iI2YxZjFmMSIgZD0ibTIwNy45NTkgMTE3Ny4xNTEgMTIgMTItMTIgMTItMTItMTJ6bS05OC41MzUgMTA3Ljk2OWgxOTcuMDdsMTIgMTItMTIgMTJoLTE5Ny4wN2wtMTItMTJ6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMjExLjk1OSIgeT0iMTMxOS4zMyIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjE5LjAwOCI+eWVzPC90ZXh0Pjx0ZXh0IHg9IjEwOS40MjQiIHk9IjEzMDAuOTI4IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMSIgdGV4dExlbmd0aD0iMTk3LjA3MSI+SW1hZ2UsIGxvY2F0aW9uIGFuZCBjYXRlZ29yeSB2YWxpZD88L3RleHQ+PHRleHQgeD0iMzE4LjQ5NCIgeT0iMTI5NC41MjUiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjExIiB0ZXh0TGVuZ3RoPSIxMy43MDIiPm5vPC90ZXh0PjxyZWN0IHdpZHRoPSIxMDAuMjMyIiBoZWlnaHQ9IjMzLjk2OSIgeD0iMzQyLjQ5NCIgeT0iMTIyMS4xNTEiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjM1Mi40OTQiIHk9IjEyNDIuMjkiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiB0ZXh0TGVuZ3RoPSI4MC4yMzIiPkNvcnJlY3QgZmllbGRzPC90ZXh0PjxyZWN0IHdpZHRoPSIxMDMuMjk3IiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTU2LjMxIiB5PSIxMzQwLjgzIiBmaWxsPSIjZjFmMWYxIiByeD0iMTIuNSIgcnk9IjEyLjUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIxNjYuMzEiIHk9IjEzNjEuOTY5IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iODMuMjk3Ij5TdWJtaXQgcmVwb3J0PC90ZXh0PjxyZWN0IHdpZHRoPSIxODguNzI3IiBoZWlnaHQ9IjMzLjk2OSIgeD0iNDkwLjAxNCIgeT0iMTkxOS40MTIiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjUwMC4wMTQiIHk9IjE5NDAuNTUxIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMTY4LjcyNyI+Q29ycmVjdCByZXBvcnQgYW5kIHJlc3VibWl0PC90ZXh0PjxyZWN0IHdpZHRoPSIxNTAuMDM3IiBoZWlnaHQ9IjMzLjk2OSIgeD0iMzE3Ljk3NyIgeT0iMjMzOS40NTEiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjMyNy45NzciIHk9IjIzNjAuNTg5IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMTMwLjAzNyI+VHJhY2sgcmVwb3J0IHByb2dyZXNzPC90ZXh0PjxyZWN0IHdpZHRoPSI0MzIuMDE0IiBoZWlnaHQ9IjYiIHg9IjQ4IiB5PSIyNDgxLjg3MyIgZmlsbD0iIzU1NSIgcng9IjIuNSIgcnk9IjIuNSIgc3R5bGU9InN0cm9rZTojNTU1O3N0cm9rZS13aWR0aDoxIi8+PHJlY3Qgd2lkdGg9IjIwMS4wMDIiIGhlaWdodD0iMzMuOTY5IiB4PSIxMDcuNDU4IiB5PSIyNTA3Ljg3MyIgZmlsbD0iI2YxZjFmMSIgcng9IjEyLjUiIHJ5PSIxMi41IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMTE3LjQ1OCIgeT0iMjUyOS4wMTEiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiB0ZXh0TGVuZ3RoPSIxODEuMDAyIj5SZWNlaXZlIG5vdGlmaWNhdGlvbiBvciB1cGRhdGU8L3RleHQ+PHJlY3Qgd2lkdGg9IjE3Ny43MjMiIGhlaWdodD0iMzMuOTY5IiB4PSIxMTkuMDk4IiB5PSIyNTYxLjg0MSIgZmlsbD0iI2YxZjFmMSIgcng9IjEyLjUiIHJ5PSIxMi41IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMTI5LjA5OCIgeT0iMjU4Mi45OCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIHRleHRMZW5ndGg9IjE1Ny43MjMiPlZpZXcgY29tcGxldGlvbiBldmlkZW5jZTwvdGV4dD48cmVjdCB3aWR0aD0iMTc3LjA2IiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTE5LjQyOSIgeT0iMjY2NC4yMTIiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjEyOS40MjkiIHk9IjI2ODUuMzUxIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMTU3LjA2Ij5SYXRlIG9yIGNvbmZpcm0gcmVzb2x1dGlvbjwvdGV4dD48cGF0aCBmaWxsPSIjZjFmMWYxIiBkPSJNMTMzLjA1NCAyNjE1LjgxaDE0OS44MWwxMiAxMi0xMiAxMmgtMTQ5LjgxbC0xMi0xMnoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIyMTEuOTU5IiB5PSIyNjUwLjAyMSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjQ0LjU4Ij5vcHRpb25hbDwvdGV4dD48dGV4dCB4PSIxMzMuMDU0IiB5PSIyNjMxLjYxOCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjE0OS44MSI+UmF0ZSBvciBjb25maXJtIHJlc29sdXRpb24/PC90ZXh0Pjx0ZXh0IHg9IjI5NC44NjQiIHk9IjI2MjUuMjE2IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMSIgdGV4dExlbmd0aD0iMjIuMTQiPnNraXA8L3RleHQ+PHBhdGggZmlsbD0iI2YxZjFmMSIgZD0ibTIwNy45NTkgMjcxOC4xODEgMTIgMTItMTIgMTItMTItMTJ6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PGNpcmNsZSBjeD0iMjA3Ljk1OSIgY3k9IjI3NzMuMTgxIiByPSIxMSIgZmlsbD0ibm9uZSIgc3R5bGU9InN0cm9rZTojMjIyO3N0cm9rZS13aWR0aDoxIi8+PGNpcmNsZSBjeD0iMjA3Ljk1OSIgY3k9IjI3NzMuMTgxIiByPSI2IiBmaWxsPSIjMjIyIiBzdHlsZT0ic3Ryb2tlOiMyMjI7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTUgNTAuMDQydjI3MzQuMTM5IiBzdHlsZT0ic3Ryb2tlOiMwMDA7c3Ryb2tlLXdpZHRoOjEuNSIvPjxyZWN0IHdpZHRoPSIxMDguMzcxIiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTM4NS45MjkiIHk9IjQyMi4yODgiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjEzOTUuOTI5IiB5PSI0NDMuNDI3IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iODguMzcxIj5DcmVhdGUgc2Vzc2lvbjwvdGV4dD48cGF0aCBmaWxsPSIjZjFmMWYxIiBkPSJNMTM4Mi4xMzYgMTY5Ljk2NGgxMTUuOTU3bDEyIDEyLTEyIDEyaC0xMTUuOTU3bC0xMi0xMnoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIxNDQ0LjExNCIgeT0iMjA0LjE3NCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjEzLjcwMiI+bm88L3RleHQ+PHRleHQgeD0iMTM4Mi4xMzYiIHk9IjE4NS43NzIiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjExIiB0ZXh0TGVuZ3RoPSIxMTUuOTU3Ij5WYWxpZCBzdG9yZWQgc2Vzc2lvbj88L3RleHQ+PHRleHQgeD0iMTUxMC4wOTIiIHk9IjE3OS4zNyIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjE5LjAwOCI+eWVzPC90ZXh0PjxwYXRoIGZpbGw9IiNmMWYxZjEiIGQ9Im0xNDQwLjExNCA0NzYuMjU3IDEyIDEyLTEyIDEyLTEyLTEyeiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjxyZWN0IHdpZHRoPSI1ODkuNjciIGhlaWdodD0iNiIgeD0iMTE0NS4yNzkiIHk9IjcyNi4xNjMiIGZpbGw9IiM1NTUiIHJ4PSIyLjUiIHJ5PSIyLjUiIHN0eWxlPSJzdHJva2U6IzU1NTtzdHJva2Utd2lkdGg6MSIvPjxyZWN0IHdpZHRoPSIyMjcuMTUyIiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTE1OS4yNzkiIHk9Ijc1Mi4xNjMiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjExNjkuMjc5IiB5PSI3NzMuMzAyIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMjA3LjE1MiI+Q29tcHJlc3MgaW1hZ2UgKHN1Yi1hY3Rpdml0eSA3LjIpPC90ZXh0PjxyZWN0IHdpZHRoPSIzMDYuNTE4IiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTQxNC40MzIiIHk9Ijc1Mi4xNjMiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjE0MjQuNDMyIiB5PSI3NzMuMzAyIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMjg2LjUxOCI+U3lzdGVtIGNhcHR1cmVzIEdQUyBsb2NhdGlvbiAoc3ViLWFjdGl2aXR5IDcuMyk8L3RleHQ+PHJlY3Qgd2lkdGg9IjU4OS42NyIgaGVpZ2h0PSI2IiB4PSIxMTQ1LjI3OSIgeT0iODA2LjEzMiIgZmlsbD0iIzU1NSIgcng9IjIuNSIgcnk9IjIuNSIgc3R5bGU9InN0cm9rZTojNTU1O3N0cm9rZS13aWR0aDoxIi8+PHJlY3Qgd2lkdGg9IjI5OC4zMzgiIGhlaWdodD0iMzMuOTY5IiB4PSIxMjkwLjk0NSIgeT0iOTM2LjI0NSIgZmlsbD0iI2YxZjFmMSIgcng9IjEyLjUiIHJ5PSIxMi41IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMTMwMC45NDUiIHk9Ijk1Ny4zODMiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiB0ZXh0TGVuZ3RoPSIyNzguMzM4Ij5TYXZlIGRyYWZ0IC0gcmVzdW1lIHdoZW4gbG9jYXRpb24gaXMgYXZhaWxhYmxlPC90ZXh0PjxjaXJjbGUgY3g9IjE0NDAuMTE0IiBjeT0iMTAxNi4yMTMiIHI9IjExIiBmaWxsPSJub25lIiBzdHlsZT0ic3Ryb2tlOiMyMjI7c3Ryb2tlLXdpZHRoOjEiLz48Y2lyY2xlIGN4PSIxNDQwLjExNCIgY3k9IjEwMTYuMjEzIiByPSI2IiBmaWxsPSIjMjIyIiBzdHlsZT0ic3Ryb2tlOiMyMjI7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjZjFmMWYxIiBkPSJNMTM4OC41NTQgODg3Ljg0MmgxMDMuMTJsMTIgMTItMTIgMTJoLTEwMy4xMmwtMTItMTJ6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMTQ0NC4xMTQiIHk9IjkyMi4wNTMiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjExIiB0ZXh0TGVuZ3RoPSIxMy43MDIiPm5vPC90ZXh0Pjx0ZXh0IHg9IjEzODguNTU0IiB5PSI5MDMuNjUiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjExIiB0ZXh0TGVuZ3RoPSIxMDMuMTIiPkxvY2F0aW9uIHJlc29sdmVkPzwvdGV4dD48dGV4dCB4PSIxNTAzLjY3NCIgeT0iODk3LjI0OCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjE5LjAwOCI+eWVzPC90ZXh0PjxyZWN0IHdpZHRoPSIzOTUuNjAzIiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTI0Mi4zMTMiIHk9IjEzOTQuNzk5IiBmaWxsPSIjZjFmMWYxIiByeD0iMTIuNSIgcnk9IjEyLjUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIxMjUyLjMxMyIgeT0iMTQxNS45MzgiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiB0ZXh0TGVuZ3RoPSIzNzUuNjAzIj5TYXZlIHJlcG9ydCB0byBlbmNyeXB0ZWQgbG9jYWwgcXVldWUgKHN0YXR1cyBxdWV1ZWQsIGxvY2FsX2lkKTwvdGV4dD48cmVjdCB3aWR0aD0iMjQ1LjM5MyIgaGVpZ2h0PSIzMy45NjkiIHg9IjEzMTcuNDE4IiB5PSIxNDk3LjE3IiBmaWxsPSIjZjFmMWYxIiByeD0iMTIuNSIgcnk9IjEyLjUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIxMzI3LjQxOCIgeT0iMTUxOC4zMDkiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiB0ZXh0TGVuZ3RoPSIyMjUuMzkzIj5TaG93ICZxdW90O1NhdmVkIC0gd2lsbCBzZW5kIHdoZW4gb25saW5lJnF1b3Q7PC90ZXh0PjxwYXRoIGZpbGw9IiNmMWYxZjEiIGQ9Ik0xMzY5LjAwOSAxNDQ4Ljc2OGgxNDIuMjExbDEyIDEyLTEyIDEyaC0xNDIuMjExbC0xMi0xMnoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIxNDQ0LjExNCIgeT0iMTQ4Mi45NzgiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjExIiB0ZXh0TGVuZ3RoPSIxMy43MDIiPm5vPC90ZXh0Pjx0ZXh0IHg9IjEzNjkuMDA5IiB5PSIxNDY0LjU3NiIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjE0Mi4yMSI+T25saW5lIHdpdGggdmFsaWQgc2Vzc2lvbj88L3RleHQ+PHRleHQgeD0iMTUyMy4yMTkiIHk9IjE0NTguMTczIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMSIgdGV4dExlbmd0aD0iMTkuMDA4Ij55ZXM8L3RleHQ+PHBhdGggZmlsbD0iI2YxZjFmMSIgZD0ibTE0NDAuMTE0IDE1NTEuMTM5IDEyIDEyLTEyIDEyLTEyLTEyeiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjxyZWN0IHdpZHRoPSIyNzguMTkzIiBoZWlnaHQ9IjMzLjk2OSIgeD0iMTMwMS4wMTgiIHk9IjE2MzkuMTM5IiBmaWxsPSIjZjFmMWYxIiByeD0iMTIuNSIgcnk9IjEyLjUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIxMzExLjAxOCIgeT0iMTY2MC4yNzciIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiB0ZXh0TGVuZ3RoPSIyNTguMTkzIj5XYWl0IGZvciBjb25uZWN0aXZpdHksIHJldHJ5IHRpbWUgb3IgcmUtbG9naW48L3RleHQ+PHJlY3Qgd2lkdGg9IjM3OS44OTQiIGhlaWdodD0iMzMuOTY5IiB4PSIxMjUwLjE2NyIgeT0iMTY5My4xMDciIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjEyNjAuMTY3IiB5PSIxNzE0LjI0NiIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIHRleHRMZW5ndGg9IjM1OS44OTQiPlNlbmQgbXVsdGlwYXJ0IFBPU1QgL3JlcG9ydHMgd2l0aCBsb2NhbF9pZCAoc3ViLWFjdGl2aXR5IDcuNCk8L3RleHQ+PHBhdGggZmlsbD0iI2YxZjFmMSIgZD0iTTEzOTIuMzA5IDE4MDEuMDQ1aDk1LjYxMWwxMiAxMi0xMiAxMmgtOTUuNjExbC0xMi0xMnoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIxMzkyLjMwOSIgeT0iMTgxNi44NTMiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjExIiB0ZXh0TGVuZ3RoPSI5NS42MTEiPlNlcnZlciByZXNwb25zZT88L3RleHQ+PHJlY3Qgd2lkdGg9IjM0MC40NjEiIGhlaWdodD0iMzMuOTY5IiB4PSI2ODguNzQiIHk9IjIwMjcuMzUiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjY5OC43NCIgeT0iMjA0OC40ODgiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiB0ZXh0TGVuZ3RoPSIzMjAuNDYxIj5NYXJrIHN1Ym1pdHRlZCwgc3RvcmUgdHJhY2tpbmcgSUQsIGRlbGV0ZSBsb2NhbCBpbWFnZTwvdGV4dD48cmVjdCB3aWR0aD0iMzUwLjIyMyIgaGVpZ2h0PSIzMy45NjkiIHg9IjEwMzkuMjAxIiB5PSIxODYwLjY1NCIgZmlsbD0iI2YxZjFmMSIgcng9IjEyLjUiIHJ5PSIxMi41IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMTA0OS4yMDEiIHk9IjE4ODEuNzkzIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMzMwLjIyMyI+UmVmcmVzaCB0b2tlbiBvbmNlLCBvdGhlcndpc2UgcGF1c2UgYW5kIHByb21wdCBsb2dpbjwvdGV4dD48cmVjdCB3aWR0aD0iMzUzLjQ2OSIgaGVpZ2h0PSIzMy45NjkiIHg9IjE0MDkuNDI0IiB5PSIxODYwLjY1NCIgZmlsbD0iI2YxZjFmMSIgcng9IjEyLjUiIHJ5PSIxMi41IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMTQxOS40MjQiIHk9IjE4ODEuNzkzIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMzMzLjQ2OSI+UGF1c2UgcXVldWUgYW5kIHNob3cgYWNjb3VudCBvciBwZXJtaXNzaW9uIG1lc3NhZ2U8L3RleHQ+PHJlY3Qgd2lkdGg9IjE4OC4xNTIiIGhlaWdodD0iMzMuOTY5IiB4PSIxNzcyLjg5MyIgeT0iMTg2MC42NTQiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjE3ODIuODkzIiB5PSIxODgxLjc5MyIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIHRleHRMZW5ndGg9IjE2OC4xNTIiPkFwcGx5IFJldHJ5LUFmdGVyIG9yIGJhY2tvZmY8L3RleHQ+PHJlY3Qgd2lkdGg9IjIxNy4xNjgiIGhlaWdodD0iMzMuOTY5IiB4PSIxOTg2LjA4OCIgeT0iMTg2MC42NTQiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjE5OTYuMDg4IiB5PSIxODgxLjc5MyIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIHRleHRMZW5ndGg9IjE5Ny4xNjgiPk1hcmsgZmFpbGVkIGFuZCBzaG93IGZpZWxkIGVycm9yczwvdGV4dD48cGF0aCBmaWxsPSIjZjFmMWYxIiBkPSJtMTQ0MC4xMTQgMjA3MS4zMTggMTIgMTItMTIgMTItMTItMTJ6bTAtNDc2LjE3OSAxMiAxMi0xMiAxMi0xMi0xMnptLTU2LjI4OSA1MjAuMTc5aDExMi41NzhsMTIgMTItMTIgMTJoLTExMi41NzhsLTEyLTEyeiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjE0NDQuMTE0IiB5PSIyMTQ5LjUyOSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjE5LjAwOCI+eWVzPC90ZXh0Pjx0ZXh0IHg9IjEzODMuODI1IiB5PSIyMTMxLjEyNiIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjExMi41NzgiPkFjY2VwdGVkIGJ5IHNlcnZlcj88L3RleHQ+PHRleHQgeD0iMTUwOC40MDMiIHk9IjIxMjQuNzI0IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMSIgdGV4dExlbmd0aD0iMTMuNzAyIj5ubzwvdGV4dD48cmVjdCB3aWR0aD0iMzM5LjA5NiIgaGVpZ2h0PSIzMy45NjkiIHg9IjEyNzAuNTY2IiB5PSIyMTcxLjAyOSIgZmlsbD0iI2YxZjFmMSIgcng9IjEyLjUiIHJ5PSIxMi41IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMTI4MC41NjYiIHk9IjIxOTIuMTY4IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMzE5LjA5NiI+U2hvdyBSZXBvcnQgU3VjY2Vzc2Z1bGx5IFN1Ym1pdHRlZCB3aXRoIHRyYWNraW5nIElEPC90ZXh0PjxyZWN0IHdpZHRoPSI1NDguMTA5IiBoZWlnaHQ9IjYiIHg9IjExNjYuMDYiIHk9IjIyMjQuOTk4IiBmaWxsPSIjNTU1IiByeD0iMi41IiByeT0iMi41IiBzdHlsZT0ic3Ryb2tlOiM1NTU7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNNjgyLjc0IDUwLjA0MnYyNzM0LjEzOSIgc3R5bGU9InN0cm9rZTojMDAwO3N0cm9rZS13aWR0aDoxLjUiLz48cmVjdCB3aWR0aD0iMzM0LjM3MyIgaGVpZ2h0PSIzMy45NjkiIHg9IjI3MDUuMzUyIiB5PSIxNzQ3LjA3NiIgZmlsbD0iI2YxZjFmMSIgcng9IjEyLjUiIHJ5PSIxMi41IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMjcxNS4zNTIiIHk9IjE3NjguMjE1IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMzE0LjM3MyI+VmFsaWRhdGUgdG9rZW4sIGF1dGhvcml6YXRpb24sIHJhdGUgbGltaXQgYW5kIHBheWxvYWQ8L3RleHQ+PHJlY3Qgd2lkdGg9IjMxOC40IiBoZWlnaHQ9IjMzLjk2OSIgeD0iMjI2Mi4xNyIgeT0iMTg2MC42NTQiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjIyNzIuMTciIHk9IjE4ODEuNzkzIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMjk4LjQiPlBlcnNpc3QgcmVwb3J0IGFuZCBpbWFnZSwgZGUtZHVwbGljYXRlIG9uIGxvY2FsX2lkPC90ZXh0PjxyZWN0IHdpZHRoPSIxMjguNzczIiBoZWlnaHQ9IjMzLjk2OSIgeD0iMjM1Ni45ODMiIHk9IjE5MTkuNDEyIiBmaWxsPSIjZjFmMWYxIiByeD0iMTIuNSIgcnk9IjEyLjUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIyMzY2Ljk4MyIgeT0iMTk0MC41NTEiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiB0ZXh0TGVuZ3RoPSIxMDguNzczIj5Bc3NpZ24gdHJhY2tpbmcgSUQ8L3RleHQ+PHJlY3Qgd2lkdGg9IjM2Mi4yMjgiIGhlaWdodD0iMzMuOTY5IiB4PSIyMjQwLjI1NiIgeT0iMTk3My4zODEiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjIyNTAuMjU2IiB5PSIxOTk0LjUyIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMzQyLjIyOCI+UmVwb3J0IHNlbnQgZm9yIEFJLWFzc2lzdGVkIGFuYWx5c2lzIChQZW5kaW5nIEFJIEFuYWx5c2lzKTwvdGV4dD48cmVjdCB3aWR0aD0iMzAyLjQ0NSIgaGVpZ2h0PSIzMy45NjkiIHg9IjI2MzIuMjk4IiB5PSIyMjUwLjk5OCIgZmlsbD0iI2YxZjFmMSIgcng9IjEyLjUiIHJ5PSIxMi41IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOi41Ii8+PHRleHQgeD0iMjY0Mi4yOTgiIHk9IjIyNzIuMTM2IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgdGV4dExlbmd0aD0iMjgyLjQ0NSI+QUkgZGV0ZWN0cyB3YXN0ZSwgY2xhc3NpZmllcyBhbmQgc2NvcmVzIHNldmVyaXR5PC90ZXh0PjxyZWN0IHdpZHRoPSIyODguMTkiIGhlaWdodD0iMzMuOTY5IiB4PSIyNjM5LjQyNiIgeT0iMjMwNC45NjYiIGZpbGw9IiNmMWYxZjEiIHJ4PSIxMi41IiByeT0iMTIuNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDouNSIvPjx0ZXh0IHg9IjI2NDkuNDI2IiB5PSIyMzI2LjEwNSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIHRleHRMZW5ndGg9IjI2OC4xOSI+T3BlcmF0b3IgcmV2aWV3cyBhbmQgYXNzaWducyBjbGVhbmluZyB0ZWFtPC90ZXh0PjxyZWN0IHdpZHRoPSIzNDIuMDcyIiBoZWlnaHQ9IjMzLjk2OSIgeD0iMjYxMi40ODQiIHk9IjIzNzMuOTM1IiBmaWxsPSIjZjFmMWYxIiByeD0iMTIuNSIgcnk9IjEyLjUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIyNjIyLjQ4NCIgeT0iMjM5NS4wNzQiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiB0ZXh0TGVuZ3RoPSIzMjIuMDcyIj5DbGVhbmluZyB0ZWFtIGNvbXBsZXRlcyB3b3JrIGFuZCB1cGxvYWRzIGV2aWRlbmNlPC90ZXh0PjxyZWN0IHdpZHRoPSIxNTQuNDE0IiBoZWlnaHQ9IjMzLjk2OSIgeD0iMjcwNi4zMTQiIHk9IjI0MjcuOTA0IiBmaWxsPSIjZjFmMWYxIiByeD0iMTIuNSIgcnk9IjEyLjUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6LjUiLz48dGV4dCB4PSIyNzE2LjMxNCIgeT0iMjQ0OS4wNDMiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjEyIiB0ZXh0TGVuZ3RoPSIxMzQuNDE0Ij5TZW5kIHB1c2ggbm90aWZpY2F0aW9uPC90ZXh0PjxwYXRoIGQ9Ik0yMjM0LjI1NiA1MC4wNDJ2MjczNC4xMzltODA5LjQ3LTI3MzQuMTM5djI3MzQuMTM5IiBzdHlsZT0ic3Ryb2tlOiMwMDA7c3Ryb2tlLXdpZHRoOjEuNSIvPjxwYXRoIGQ9Ik0yMDcuOTU5IDk1Ljk5NXYyMCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTIwMy45NTkgMTA1Ljk5NSA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTIwNy45NTkgMjQyLjM2NnYyNC40MDMiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMDMuOTU5IDI1Ni43NjkgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0yNjkuMjg3IDIzMC4zNjZoMTIiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yNzcuMjg3IDI3My43NTMgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0yODEuMjg3IDIzMC4zNjZ2MTAyLjM3MW0wIDBoLTYxLjMyOCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTIyOS45NTkgMzI4LjczNy0xMCA0IDEwIDQtNC00eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTIwNy45NTkgMzAwLjczN3YyMCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTIwMy45NTkgMzEwLjczNyA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTIwNy45NTkgMzQ0LjczN3YyMy41ODIiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMDMuOTU5IDM1OC4zMTkgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0yMDcuOTU5IDU1NC4yMjZ2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMDMuOTU5IDU2NC4yMjYgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0yMDcuOTU5IDY1Mi4xOTR2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMDMuOTU5IDY2Mi4xOTQgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0xNTIuOTkgODQ0LjEzMkgzNCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTMwIDc0NC42NjMgNC0xMCA0IDEwLTQtNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0zNCA2NDAuMTk0djIwMy45MzhtMC0yMDMuOTM4aDE2MS45NTkiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0xODUuOTU5IDYzNi4xOTQgMTAgNC0xMCA0IDQtNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0yMDcuOTU5IDYwOC4xOTR2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMDMuOTU5IDYxOC4xOTQgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0yMDcuOTU5IDExMDMuMTgydjIwIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMjAzLjk1OSAxMTEzLjE4MiA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTIwNy45NTkgMTIwMS4xNTF2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMDMuOTU5IDEyMTEuMTUxIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMzE4LjQ5NCAxMjk3LjEyaDc0LjExN20wLTQydjQyIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMzg4LjYxMSAxMjY1LjEyIDQtMTAgNCAxMC00LTR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMzkyLjYxMSAxMTg5LjE1MXYzMm0wLTMySDIxOS45NTkiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMjkuOTU5IDExODUuMTUxLTEwIDQgMTAgNC00LTR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjA3Ljk1OSAxMjU1LjEydjMwIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMjAzLjk1OSAxMjc1LjEyIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjA3Ljk1OSAxMTU3LjE1MXYyMCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTIwMy45NTkgMTE2Ny4xNTEgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0yMDcuOTU5IDEzMDkuMTJ2MzEuNzEiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMDMuOTU5IDEzMzAuODMgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0zOTIuOTk1IDIzNzMuNDE5djEwOC40NTQiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0zODguOTk1IDI0NzEuODczIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjA3Ljk1OSAyNDg3Ljg3M3YyMCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTIwMy45NTkgMjQ5Ny44NzMgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0yMDcuOTU5IDI1NDEuODQxdjIwIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMjAzLjk1OSAyNTUxLjg0MSA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTIwNy45NTkgMjYzOS44MXYyNC40MDIiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMDMuOTU5IDI2NTQuMjEyIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjk0Ljg2NCAyNjI3LjgxaDEyIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMzAyLjg2NCAyNjcxLjE5NyA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTMwNi44NjQgMjYyNy44MXYxMDIuMzcxbTAgMGgtODYuOTA1IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMjI5Ljk1OSAyNzI2LjE4MS0xMCA0IDEwIDQtNC00eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTIwNy45NTkgMjY5OC4xODF2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMDMuOTU5IDI3MDguMTgxIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjA3Ljk1OSAyNTk1LjgxdjIwIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMjAzLjk1OSAyNjA1LjgxIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjA3Ljk1OSAyNzQyLjE4MXYyMCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTIwMy45NTkgMjc1Mi4xODEgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0xNTEwLjA5MiAxODEuOTY0aDEzLjM1IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTUxOS40NDIgMzM4LjMxOSA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTE1MjMuNDQyIDE4MS45NjR2MzA2LjI5M20wIDBoLTcxLjMyOCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTE0NjIuMTE0IDQ4NC4yNTctMTAgNCAxMCA0LTQtNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0xNDQwLjExNCA0NTYuMjU3djIwIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTQzNi4xMTQgNDY2LjI1NyA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTEyNzIuODU1IDczMi4xNjN2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0xMjY4Ljg1NiA3NDIuMTYzIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTU2Ny42OSA3MzIuMTYzdjIwIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTU2My42OSA3NDIuMTYzIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTI3Mi44NTUgNzg2LjEzMnYyMCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTEyNjguODU2IDc5Ni4xMzIgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0xNTY3LjY5IDc4Ni4xMzJ2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0xNTYzLjY5IDc5Ni4xMzIgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0xNDQwLjExNCA5NzAuMjEzdjM1IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTQzNi4xMTQgOTk1LjIxMyA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTE0NDAuMTE0IDkxMS44NDJ2MjQuNDAzIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTQzNi4xMTQgOTI2LjI0NSA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTE1MDMuNjc0IDg5OS44NDJoOTUuNjA5IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTU5NS4yODMgOTc3LjQ3OSA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTE1OTkuMjgzIDg5OS44NDJ2MTU0LjM3MW0wIDBIMjA3Ljk1OW0wIDB2MTUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMDMuOTU5IDEwNTkuMjEzIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTQ0MC4xMTQgMTQ3Mi43Njh2MjQuNDAyIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTQzNi4xMTQgMTQ4Ny4xNyA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTE1MjMuMjE5IDE0NjAuNzY4aDQ5LjU5MiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTE1NjguODExIDE1MDQuMTU0IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTU3Mi44MTEgMTQ2MC43Njh2MTAyLjM3MW0wIDBoLTEyMC42OTciIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0xNDYyLjExNCAxNTU5LjEzOS0xMCA0IDEwIDQtNC00eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTE0NDAuMTE0IDE1MzEuMTM5djIwIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTQzNi4xMTQgMTU0MS4xMzkgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0xNDQwLjExNCAxNDI4Ljc2OHYyMCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTE0MzYuMTE0IDE0MzguNzY4IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTQ0MC4xMTQgMTY3My4xMDd2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0xNDM2LjExNCAxNjgzLjEwNyA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTE0OTkuOTIgMTgxMy4wNDVoNTk0Ljc1Mm0wIDB2NDcuNjA5IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMjA5MC42NzIgMTg1MC42NTQgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjx0ZXh0IHg9IjIwOTQuNjcyIiB5PSIxODQwLjY1OCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9Ijc3LjY3MSI+NHh4IHZhbGlkYXRpb248L3RleHQ+PHBhdGggZD0iTTEyMTQuMzEzIDE4MTMuMDQ1djQ3LjYwOSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTEyMTAuMzEzIDE4NTAuNjU0IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48dGV4dCB4PSIxMjE0LjMxMyIgeT0iMTgzNS42NTgiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjExIiB0ZXh0TGVuZ3RoPSIyMC45OTYiPjQwMTwvdGV4dD48cGF0aCBkPSJNMTU4Ni4xNTggMTgxMy4wNDV2NDcuNjA5IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTU4Mi4xNTggMTg1MC42NTQgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjx0ZXh0IHg9IjE1ODYuMTU4IiB5PSIxODM1LjY1OCIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTEiIHRleHRMZW5ndGg9IjIwLjk5NiI+NDAzPC90ZXh0PjxwYXRoIGQ9Ik0xODY2Ljk2OSAxODEzLjA0NXY0Ny42MDkiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0xODYyLjk2OSAxODUwLjY1NCA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHRleHQgeD0iMTg2Ni45NjkiIHk9IjE4MzUuNjU4IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMSIgdGV4dExlbmd0aD0iMTA5LjExOSI+NDI5LCA1eHggb3IgdGltZW91dDwvdGV4dD48cGF0aCBkPSJNODU4Ljk3MSAyMDYxLjMxOHYyMm0wIDBoNTY5LjE0MyIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTE0MTguMTE0IDIwNzkuMzE4IDEwIDQtMTAgNCA0LTR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTIxNC4zMTMgMTg5NC42MjN2MTg4LjY5NSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTEyMTAuMzEzIDIwNzMuMzE4IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTU4Ni4xNTggMTg5NC42MjN2MTg4LjY5NSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTE1ODIuMTU4IDIwNzMuMzE4IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTg2Ni45NjkgMTg5NC42MjN2MTg4LjY5NSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTE4NjIuOTY5IDIwNzMuMzE4IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTQ0MC4xMTQgMTYxOS4xMzl2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0xNDM2LjExNCAxNjI5LjEzOSA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTE1MDguNDAzIDIxMjcuMzE4aDcwNi44NTMiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yMjExLjI1NiAxOTE0LjYyMyA0LTEwIDQgMTAtNC00eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTIyMTUuMjU2IDE2MDcuMTM5djUyMC4xNzltMC01MjAuMTc5aC03NjMuMTQyIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTQ2Mi4xMTQgMTYwMy4xMzktMTAgNCAxMCA0LTQtNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0xNDQwLjExNCAyMDk1LjMxOHYyMCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTE0MzYuMTE0IDIxMDUuMzE4IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTQ0MC4xMTQgMTU3NS4xMzl2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0xNDM2LjExNCAxNTg1LjEzOSA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTE0NDAuMTE0IDIxMzkuMzE4djMxLjcxMSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTE0MzYuMTE0IDIxNjEuMDI5IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMTQ0MC4xMTQgMjIwNC45OTh2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0xNDM2LjExNCAyMjE0Ljk5OCA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTI0MjEuMzcgMTg5NC42MjN2MjQuNzg5IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMjQxNy4zNyAxOTA5LjQxMiA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTI0MjEuMzcgMTk1My4zODF2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yNDE3LjM3IDE5NjMuMzgxIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjc4My41MjEgMjI4NC45NjZ2MjAiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yNzc5LjUyMSAyMjk0Ljk2NiA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTI3ODMuNTIxIDIzMzguOTM1djM1IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMjc3OS41MjEgMjM2My45MzUgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0yNzgzLjUyMSAyNDA3LjkwNHYyMCIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTI3NzkuNTIxIDI0MTcuOTA0IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjA3Ljk1OSA0MDIuMjg4djVtMCAwaDEyMzIuMTU1bTAgMHYxNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTE0MzYuMTE0IDQxMi4yODggNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0xNDQwLjExNCAxOTMuOTY0djEyLjIwMW0wIDBIMjA3Ljk1OW0wIDB2MTIuMjAxIiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMjAzLjk1OSAyMDguMzY2IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjA3Ljk1OSAxNDkuOTY0djVtMCAwaDEyMzIuMTU1bTAgMHYxNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTE0MzYuMTE0IDE1OS45NjQgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0xNDQwLjExNCA1MDAuMjU3djVtMCAwSDIwNy45NTltMCAwdjE1IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMjAzLjk1OSA1MTAuMjU3IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjA3Ljk1OSA3MDYuMTYzdjVtMCAwaDEyMzIuMTU1bTAgMHYxNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTE0MzYuMTE0IDcxNi4xNjMgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0xNDQwLjExNCA4MTIuMTMydjVtMCAwSDIwNy45NTltMCAwdjE1IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMjAzLjk1OSA4MjIuMTMyIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjA3Ljk1OSA4NTYuMTMydjE2LjcxbTAgMGgxMjMyLjE1NW0wIDB2MTUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0xNDM2LjExNCA4NzcuODQyIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjA3Ljk1OSAxMzc0Ljc5OXY1bTAgMGgxMjMyLjE1NW0wIDB2MTUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0xNDM2LjExNCAxMzg0Ljc5OSA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTE0NDAuMTE0IDE3MjcuMDc2djVtMCAwaDE0MzIuNDI1bTAgMHYxNSIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTI4NjguNTM5IDE3MzcuMDc2IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjQyMS4zNyAyMDA3LjM1djVtMCAwSDg1OC45NzFtMCAwdjE1IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtODU0Ljk3MSAyMDE3LjM1IDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjA5NC42NzIgMTg5NC42MjN2Ny4yODltMCAwSDU4NC4zNzdtMCAwdjE3LjUiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im01ODAuMzc3IDE5MDkuNDEyIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBkPSJNMjg3Mi41MzkgMTc4MS4wNDV2NW0wIDBIMTQ0MC4xMTRtMCAwdjE1IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTQzNi4xMTQgMTc5MS4wNDUgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0xMzUxLjA5NiAyMjMwLjk5OHY0bTAgMGgxNDMyLjQyNW0wIDB2MTYiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGZpbGw9IiMxODE4MTgiIGQ9Im0yNzc5LjUyMSAyMjQwLjk5OCA0IDEwIDQtMTAtNCA0eiIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZD0iTTE2MjUuMTUgMjIzMC45OTh2NG0wIDBIMzkyLjk5NW0wIDB2MTA0LjQ1MyIgc3R5bGU9InN0cm9rZTojMTgxODE4O3N0cm9rZS13aWR0aDoxIi8+PHBhdGggZmlsbD0iIzE4MTgxOCIgZD0ibTM4OC45OTUgMjMyOS40NTEgNCAxMCA0LTEwLTQgNHoiIHN0eWxlPSJzdHJva2U6IzE4MTgxODtzdHJva2Utd2lkdGg6MSIvPjxwYXRoIGQ9Ik0yNzgzLjUyMSAyNDYxLjg3M3Y2bTAgMEgxMTguOTRtMCAwdjE0IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48cGF0aCBmaWxsPSIjMTgxODE4IiBkPSJtMTE0Ljk0IDI0NzEuODczIDQgMTAgNC0xMC00IDR6IiBzdHlsZT0ic3Ryb2tlOiMxODE4MTg7c3Ryb2tlLXdpZHRoOjEiLz48dGV4dCB4PSIzMTguMDkxIiB5PSI2Ni43NSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTgiIHRleHRMZW5ndGg9IjYxLjU1OSI+Q2l0aXplbjwvdGV4dD48dGV4dCB4PSIxNDExLjk5OSIgeT0iNjYuNzUiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjE4IiB0ZXh0TGVuZ3RoPSI5Mi45OTciPkNsaWVudCBBcHA8L3RleHQ+PHRleHQgeD0iMjU0Mi41MTMiIHk9IjY2Ljc1IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgdGV4dExlbmd0aD0iMTkyLjk1NSI+QmFja2VuZCAmYW1wOyBBSSBTZXJ2aWNlPC90ZXh0Pjwvc3ZnPg==
