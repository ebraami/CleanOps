# Cleaning Crew Mobile Application — Architecture Specification

## CleanOps (CleanStreet AI)

---

## 1. Purpose and Scope

This document defines the architecture for the **Cleaning Crew Flutter application** — the field-facing app used by cleaning team members to receive assigned tasks, navigate to report locations, log their route while working, and submit cleanup evidence. It covers four areas:

1. Assigned task queue
2. Offline map caching
3. Background GPS route logging
4. Cleanup evidence collection, including the offline evidence sync protocol

This document follows the same architectural conventions already established for the Citizen Mobile Application (MVVM + Cubit/BLoC, feature-based structure) and is functionally grounded in FR-3.x (Cleaning-Team Functions), the Task Assignment & Notification Flow, the Completion Evidence Submission (Rev. 2) specification, and the Report Lifecycle state machine — specifically the `Set → In Progress → Cleaned` portion of that model, which is the segment this app is responsible for driving.

---

## 2. Modular Architecture (MVVM)

Same pattern as the Citizen App: feature-based folders, each split into View (`presentation/`), ViewModel (`application/`, as Cubits), and Model (`data/`).

```
lib/
├── core/
│   ├── network/          # API client, interceptors, error mapping
│   ├── storage/          # Hive setup, secure storage
│   ├── location/         # GPS service wrapper, background location handling
│   ├── theme/
│   ├── widgets/
│   └── models/           # Shared models (Task, ReportSummary, EvidenceSubmission)
│
├── features/
│   ├── auth/              # Team member login (FR-2.1/2.2 equivalent for team accounts)
│   │
│   ├── task_queue/
│   │   ├── presentation/   # Task list screen, task detail screen
│   │   ├── application/    # TaskQueueCubit
│   │   └── data/           # Task repository (fetch assigned tasks, cache locally)
│   │
│   ├── map_navigation/
│   │   ├── presentation/   # Offline-capable map view, route to site
│   │   ├── application/    # MapCacheCubit, RouteCubit
│   │   └── data/           # Tile cache repository
│   │
│   ├── route_logging/
│   │   ├── presentation/   # Minimal — mostly a background service, optional in-app indicator
│   │   ├── application/    # RouteLoggingBloc (full Bloc — see Section 5)
│   │   └── data/           # Local route-point store, upload repository
│   │
│   └── evidence/
│       ├── presentation/   # Camera capture, review/confirm screen
│       ├── application/    # EvidenceSubmissionCubit
│       └── data/           # Evidence repository, offline sync queue
│
└── main.dart
```

**Rule:** identical to the Citizen App and the Maintainability Standards — no feature imports another feature's internals directly; shared concerns go through `core/`.

---

## 3. Assigned Task Queue

### 3.1 Data Source

The task queue is a filtered view of reports where `ASSIGNMENTS.team_id` matches the logged-in team and the report's lifecycle state is `Set` or `In Progress` (per the Report Lifecycle model) — the same query underpinning FR-3.1, now implemented client-side as a repository call.

### 3.2 Cubit Pattern

```dart
// features/task_queue/application/task_queue_cubit.dart
class TaskQueueCubit extends Cubit<TaskQueueState> {
  final TaskRepository _repository;
  TaskQueueCubit(this._repository) : super(TaskQueueState.initial());

  Future<void> loadTasks() async {
    emit(state.copyWith(status: TaskQueueStatus.loading));
    try {
      final tasks = await _repository.fetchAssignedTasks(); // hits backend, falls back to cache
      emit(state.copyWith(status: TaskQueueStatus.loaded, tasks: tasks));
    } catch (_) {
      final cached = await _repository.getCachedTasks();
      emit(state.copyWith(status: TaskQueueStatus.offline, tasks: cached));
    }
  }
}
```

- `TaskQueueState` holds the full list of assigned tasks as one consolidated object, each task carrying everything FR-3.2/3.3 require: report photo reference, location, category, description, priority score.
- Every successful fetch also writes the task list into a Hive box (`cached_tasks`), so the queue remains viewable (read-only) even with no connectivity — a team member can see what they're assigned to do even before reaching a signal area.
- Tasks are sorted by priority score by default (highest first), matching FR-2.7's priority concept carried through to the team's own view.

### 3.3 Authorization

Every task fetch and every subsequent action (starting work, submitting evidence) is validated server-side against `ASSIGNMENTS.team_id`, per the backend check already defined in the Completion Evidence Submission document — the app itself does not need to re-implement this check, only handle the resulting `403` gracefully if a stale cached task is no longer valid (e.g., reassigned by an operator).

---

## 4. Offline Map Caching

### 4.1 Why

Cleaning crews frequently work in areas with poor or no connectivity. Needing a live map connection just to see where a site is located would defeat the purpose of giving the team the location data at assignment time (Section 3).

### 4.2 Approach

- **Map package:** `google_maps_flutter`, consistent with the Citizen App and the Operations Dashboard, avoiding a second map SDK in the project.
- **Tile caching:** since `google_maps_flutter` does not natively support persistent offline tile storage, the app uses a tile-caching layer (`flutter_map` with the `flutter_map_tile_caching` plugin is the recommended alternative **specifically for this app**, since it supports genuine offline vector/raster tile persistence in a way `google_maps_flutter` does not — this is the one place this app's map stack diverges from the Citizen App's, and that divergence is deliberate given the offline requirement here is a hard functional need, not a convenience).
- **Caching trigger:** when a task is fetched and cached (Section 3.2), the map tiles for a bounding box around that report's coordinates (e.g., a 2 km radius) are pre-downloaded and stored locally, keyed by task ID.
- **Cache eviction:** cached tiles for a task are cleared once that task reaches `Cleaned` or is reassigned away from the team, keeping local storage bounded rather than accumulating indefinitely.

### 4.3 Fallback Behavior

If a team member opens a task with no cached tiles available (e.g., they never had connectivity since assignment), the map view shows a clear "map unavailable offline" state with the raw coordinates and a compass-style directional indicator (using the device's GPS and the target coordinate) as a minimal fallback for navigation.

---

## 5. Background GPS Route Logging

### 5.1 Why

Route logging supports two downstream needs: giving the operator visibility into how the team actually reached a site (useful context if a report's documented location turns out to be imprecise) and laying groundwork for the proposal's future-phase route optimization goal (Section 22 of the proposal) — this app logs the raw data that a routing feature would eventually consume, without implementing routing itself.

### 5.2 Why Full Bloc Here (Not Cubit)

This is the one feature in the app's state management that uses full `Bloc` rather than `Cubit`, per the pattern already established for the Citizen App: background location logging has genuinely distinct, named triggers — `TrackingStarted`, `LocationPointReceived`, `TrackingStopped`, `SyncRequested` — where explicit event naming aids debugging a background process that isn't directly tied to a visible UI interaction.

### 5.3 Implementation

- **Package:** `flutter_background_geolocation` or `background_locator_2` — both support Android/iOS background execution with battery-conscious configurable intervals; exact package selection is left as an implementation-phase decision once device testing is possible, but the architecture does not change based on which is chosen.
- **Logging trigger:** starts automatically when a team member transitions a task to `In Progress` (Report Lifecycle: `Set → In Progress`), stops when the task reaches `Cleaned`.
- **Local storage:** GPS points are appended to a Hive box (`route_log_<taskId>`) as they're captured — not sent to the backend in real time, to avoid constant network chatter and battery drain in the field.
- **Sync:** once the task reaches `Cleaned` and connectivity is available, the full route log for that task uploads as a single batch (an array of timestamped lat/lng points) to the backend, associated with the report via `report_id`. If offline at that point, it joins the same offline sync queue described in Section 6.4.

### 5.4 Privacy Note

Per the proposal's Section 17 (location/PII protection), route logs are operational data tied to a team's work, not to any individual citizen, and should be retained under the same retention policy as other operational data — this is flagged here as a dependency on the Security Requirements package rather than decided independently by this document.

---

## 6. Cleanup Evidence Collection & Offline Evidence Sync Protocol

### 6.1 Relationship to Completion Evidence Submission

This section is the **client-side implementation** of the Completion Evidence Submission (Rev. 2) specification already written for this project. That document defines the required backend transaction (IMAGES row + status change + STATUS_HISTORY + `ASSIGNMENTS.completed_at`, all atomic, triggered only at confirmation). This section defines how the Flutter app gets the team to that confirmation point, including offline.

### 6.2 Capture & Compression Pipeline

Identical in structure to the Citizen App's media pipeline (Section 6 of that document), reused here rather than redesigned:

1. Capture via `image_picker`.
2. Resize to a max 1600px longest dimension via `flutter_image_compress`.
3. Compress to JPEG at ~80% quality.
4. Strip EXIF metadata.
5. Store the compressed result locally, pending confirmation.

Reusing this exact pipeline (rather than defining a second one) keeps compression behavior consistent across both apps and is implemented as a shared package in `core/` or a small internal Dart package both apps depend on, rather than duplicated code.

### 6.3 Evidence Cubit

```dart
// features/evidence/application/evidence_submission_cubit.dart
class EvidenceSubmissionCubit extends Cubit<EvidenceSubmissionState> {
  final EvidenceRepository _repository;
  EvidenceSubmissionCubit(this._repository) : super(EvidenceSubmissionState.initial());

  void addPhoto(File compressedPhoto) =>
      emit(state.copyWith(photos: [...state.photos, compressedPhoto]));

  Future<void> confirmSubmission(String reportId) async {
    emit(state.copyWith(status: SubmissionStatus.submitting));
    final result = await _repository.submit(reportId, state.photos);
    emit(result.isQueuedOffline
        ? state.copyWith(status: SubmissionStatus.queuedOffline)
        : state.copyWith(status: SubmissionStatus.submitted));
  }
}
```

- `EvidenceSubmissionState` holds the full in-progress submission (one or more photos, per the Completion Evidence Submission document's "more than one after-photo" allowance) as one consolidated object.
- Confirmation (`confirmSubmission`) is the single point that triggers either an immediate backend call or enqueuing for offline sync — the UI does not need to know which happened beyond the resulting state.

### 6.4 Offline Evidence Sync Protocol

This protocol mirrors the offline-draft pattern already defined for the Citizen App (Section 5 of that document), adapted for evidence submission specifically:

1. **On confirmation (Section 6.3)**, the app first attempts the real submission immediately — uploading each photo to Object Storage and, on success, calling the backend endpoint that triggers the atomic transaction defined in Completion Evidence Submission Rev. 2.
2. **If offline, or if any part of the attempt fails:**
   - The confirmed submission (photos + `report_id` + a locally generated `submission_id` for idempotency) is written to a Hive box (`pending_evidence`), not discarded.
   - The task's local state shows "Evidence saved — will submit when back online," distinct from a successful submission, so the team member isn't misled into thinking the operator has already received it.
3. **Connectivity restored** triggers a background sync (via `connectivity_plus`, same as the Citizen App) that processes `pending_evidence` entries in order:
   - Each photo uploads to Object Storage first.
   - Only once all photos for that entry are confirmed uploaded does the app call the backend's evidence-confirmation endpoint, which performs the atomic transaction.
4. **Idempotency:** the locally generated `submission_id` is sent with the backend call and should be checked server-side to avoid creating duplicate IMAGES rows if a sync retry occurs after a partial success (e.g., network drop right after the backend call succeeded but before the app received confirmation). This is flagged here as a requirement on the Backend/Report Lifecycle implementation architecture, not something this client-side document can guarantee alone.
5. **On successful sync**, the entry is removed from `pending_evidence`, and the task moves to reflect its real backend status (`Cleaned`, per the Report Lifecycle model) in the task queue.
6. **On repeated failure**, the entry remains in `pending_evidence` with a visible error state and a manual retry option — mirroring the Citizen App's handling of failed offline report submissions.

### 6.5 What Is Never Queued Offline

Viewing the operator's rejection reason (if provided, per the Operator Rejection/Rework Handling document) and viewing other tasks' real-time status both require connectivity, by nature — they read from the backend. The offline capability here is scoped specifically to **evidence submission**, matching the Citizen App's equally narrow scope for report creation, and deliberately not extended to a full offline-first data layer for this app either.

---

## 7. Summary of Package Choices

| Concern | Package |
|---|---|
| State management | `flutter_bloc` (Cubit for task queue/evidence; full Bloc for route logging) |
| Maps | `flutter_map` + `flutter_map_tile_caching` (diverges from Citizen App's `google_maps_flutter` due to the offline-tile requirement) |
| Background GPS | `flutter_background_geolocation` or `background_locator_2` (final choice deferred to implementation-phase device testing) |
| Local storage (tasks, route logs, pending evidence) | `hive` + `hive_flutter` |
| Connectivity detection | `connectivity_plus` |
| Image capture & compression | `image_picker` + `flutter_image_compress` (shared pipeline with the Citizen App) |

---

## 8. Summary

- The Cleaning Crew app follows the same MVVM + feature-based structure as the Citizen App, implementing the `Set → In Progress → Cleaned` portion of the Report Lifecycle.
- The task queue is a cached, priority-sorted view of assigned reports, remaining viewable offline via Hive-cached data.
- Offline map caching uses `flutter_map` with tile caching rather than `google_maps_flutter`, since persistent offline tiles are a hard requirement here, not a convenience — this is the one deliberate divergence from the Citizen App's map stack.
- Background GPS route logging uses full Bloc (not Cubit) given its distinct, named background triggers, logs locally during work, and syncs as a batch once a task is cleaned.
- Cleanup evidence collection reuses the Citizen App's exact compression pipeline and implements the client side of the already-specified Completion Evidence Submission transaction, with its own offline sync queue (`pending_evidence`) mirroring the Citizen App's offline-draft pattern, including an idempotency requirement flagged for the backend team.
