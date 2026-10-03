# Flutter Citizen Mobile Application — Architecture Design Document

## CleanStreet AI (CleanOps)

---

## 1. Purpose and Scope

This document defines the technical architecture for the Citizen Mobile Application — the Flutter app through which citizens register, log in, submit waste reports (photo + GPS + category + description), track report status, and view completion evidence. It covers four areas specifically:

1. Modular app architecture (MVVM)
2. State management pattern (Cubit/BLoC)
3. Interactive map integration for location picking
4. Offline draft reporting and media capture optimization before upload

This document assumes the Functional Requirements (FR-1.x) and the Images Entity Schema as its functional baseline — it does not redefine *what* the app must do, only *how* it is structured to do it.

---

## 2. Modular Architecture

### 2.1 Folder Structure

The app follows a **feature-based structure**, consistent with how the project's maintainability standards are already defined for this codebase: each feature owns its screens, widgets, and state management, with shared code isolated in `core/`.

```
lib/
├── core/
│   ├── network/          # API client, interceptors, error mapping
│   ├── storage/          # SQLite/Hive setup, secure storage
│   ├── theme/            # App-wide theming, text styles
│   ├── widgets/          # Shared widgets (buttons, loaders, empty states)
│   ├── utils/            # Validators, formatters, constants
│   └── models/           # Shared models (Report, User, Category, ReportImage)
│
├── features/
│   ├── auth/
│   │   ├── presentation/   # Screens: login, register, password reset
│   │   ├── application/    # State management (providers/blocs)
│   │   └── data/           # Repository + API calls for auth
│   │
│   ├── reporting/
│   │   ├── presentation/   # New report screen, map picker, review screen
│   │   ├── application/    # Report draft state, submission state
│   │   └── data/           # Report repository, offline draft store, upload logic
│   │
│   ├── tracking/
│   │   ├── presentation/   # Report history, status detail, completion photo view
│   │   ├── application/
│   │   └── data/
│   │
│   └── notifications/
│       ├── presentation/
│       ├── application/
│       └── data/
│
└── main.dart
```

### 2.2 Layering Within Each Feature (MVVM)

Each feature follows **MVVM**, mapped onto the same three folders:

- **presentation/** — the **View**: widgets and screens only; no business logic, no direct API/database calls. Views only read state from and dispatch events/calls to their ViewModel (Cubit).
- **application/** — the **ViewModel**: one `Cubit` per feature concern, holding and exposing UI state, and orchestrating calls to the data layer. This is where business logic for that feature lives.
- **data/** — the **Model** layer: repositories and data sources (REST API client calls, local SQLite/Hive access); this is the only layer allowed to talk to `core/network` or `core/storage` directly.

**Rule:** no feature imports another feature's internal files directly (matching the Maintainability Standards document already written for this project). Cross-feature needs (e.g., `tracking` needing to know if a report was just submitted by `reporting`) go through shared models in `core/models/` or a shared event/notification mechanism — never a direct import between feature folders.

---

## 3. State Management — Cubit (BLoC)

### 3.1 Choice: Cubit, Under the MVVM Pattern

State management uses **Cubit** (the simplified subset of the BLoC library) as the ViewModel layer in MVVM. Each feature concern gets one Cubit holding a single, consolidated state object — matching the project's preference for consolidated state over fragmented providers — rather than full BLoC's Event→State mapping, which adds boilerplate this app doesn't need for most screens.

Full `Bloc` (with explicit Events) is reserved for flows where distinct, named triggers genuinely matter for traceability — the offline sync queue (Section 5) is the clearest candidate, since "connectivity restored," "retry triggered," and "upload succeeded/failed" are meaningfully distinct events worth naming explicitly rather than folding into one Cubit method.

### 3.2 Pattern, Concretely

Each feature's `application/` layer exposes one or more `Cubit` classes, each paired with an immutable state class:

```dart
// features/reporting/application/report_draft_state.dart
class ReportDraftState {
  final File? photo;
  final LatLng? location;
  final Category? category;
  final String description;

  const ReportDraftState({this.photo, this.location, this.category, this.description = ''});

  ReportDraftState copyWith({File? photo, LatLng? location, Category? category, String? description}) {
    return ReportDraftState(
      photo: photo ?? this.photo,
      location: location ?? this.location,
      category: category ?? this.category,
      description: description ?? this.description,
    );
  }
}

// features/reporting/application/report_draft_cubit.dart
class ReportDraftCubit extends Cubit<ReportDraftState> {
  ReportDraftCubit() : super(const ReportDraftState());

  void setPhoto(File photo) => emit(state.copyWith(photo: photo));
  void setLocation(LatLng location) => emit(state.copyWith(location: location));
  void setCategory(Category category) => emit(state.copyWith(category: category));
  void setDescription(String description) => emit(state.copyWith(description: description));
}
```

- `ReportDraftState` is a single immutable object holding the entire in-progress report — one Cubit, one state object, rather than separate state holders for photo/location/category/description.
- Views (`presentation/`) use `BlocBuilder`/`BlocListener` to react to `ReportDraftCubit`'s state and call its methods directly — they hold no business state themselves beyond purely local UI concerns (e.g., a text field's focus).
- Submission is handled by a separate `ReportSubmissionCubit`, distinct from `ReportDraftCubit`, with its own state (`idle` / `loading` / `success` / `failure`) — keeping the "editing a draft" concern cleanly separate from the "submitting it" concern.
- `MultiBlocProvider` is used at the feature root (e.g., wrapping the report-creation flow) so the draft Cubit's state survives across the multi-step creation screens (photo → location → category → review) without being recreated on each step.

---

## 4. Interactive Map Integration (Location Picking)

### 4.1 Provider Choice

**Google Maps** is the primary recommendation, consistent with the proposal's stated preference (Section 14) and because the `google_maps_flutter` package integrates directly with the same Google Maps Platform already referenced for the Operations Dashboard — keeping both citizen app and dashboard on one mapping provider avoids maintaining two separate map SDKs/API keys across the project. OpenStreetMap remains the fallback if cost becomes a concern at scale, per the proposal's own stated flexibility on this point.

### 4.2 Location Picking Flow

Per FR-1.7, GPS coordinates are **captured automatically at submission time, not manually entered** — so "location picking" here specifically means letting the citizen *confirm or fine-tune* the auto-captured point on a map, not freely search for an arbitrary address.

1. On reaching the location step of report creation, the app requests the device's current GPS fix (`geolocator` package).
2. The map (`google_maps_flutter`) centers on that coordinate with a draggable marker.
3. The citizen may drag the marker a short distance to correct for GPS drift (e.g., pinpointing the exact side of the street), but the underlying coordinate remains a real GPS-derived value, not a manually typed one — satisfying FR-1.7's intent while allowing for practical correction.
4. The final marker position is what's written to `ReportDraft.location` and ultimately to `REPORTS.latitude`/`longitude`.

### 4.3 Map Package and Performance Notes

- `google_maps_flutter` for the map widget itself.
- `geolocator` for GPS access and permission handling.
- The map is only initialized on the location step of report creation — not kept alive across the whole app — to avoid unnecessary battery/memory cost on screens that don't need it.

---

## 5. Offline Draft Reporting

### 5.1 Why This Is Needed

Citizens reporting street waste are, by definition, out in the field — connectivity can't be assumed. A citizen should be able to start (and even fully complete) a report with no network connection, and have it queue for submission automatically once connectivity returns, rather than losing their work.

### 5.2 Storage Choice: Hive

**Hive** is recommended over raw SQLite for the draft/queue use case specifically:

- Report drafts are simple, self-contained objects (photo path, lat/lng, category, description, timestamp) — not relational data requiring joins, which is exactly what Hive (a key-value, NoSQL local store) is built for, with less boilerplate than hand-written SQLite queries.
- Hive is pure Dart (no native platform code to maintain), which reduces build complexity — relevant given the team's prior experience with Windows/Gradle build friction on this project.
- If a future need arises for more complex local relational queries (e.g., searching across many cached reports), SQLite (via `sqflite` or `drift`) remains a valid addition for that specific feature without replacing Hive for the simple draft/queue case.

### 5.3 Offline Flow

1. **Draft creation** — as the citizen fills in the report (photo, location, category, description), the `ReportDraftNotifier` state is mirrored into a Hive box (`drafts`) on every change, keyed by a locally generated draft ID (UUID). This means even an app kill/crash mid-draft doesn't lose progress.
2. **Submission attempt** — on confirming submission (FR-1.11), the app attempts to upload the photo and POST the report data immediately.
3. **If offline or the request fails:**
   - The draft is moved from `drafts` to a `pending_uploads` Hive box, marked with a `queued_at` timestamp.
   - The citizen sees a clear "Queued — will send when back online" state on this report in their history (an addition to FR-1.12/FR-1.14's status view, distinct from "Sent," since the report does not yet exist on the backend).
4. **Connectivity restored** — a connectivity listener (`connectivity_plus` package) triggers a background sync process that iterates `pending_uploads` in order and retries submission for each.
5. **On successful submission**, the entry is removed from `pending_uploads` — the report now exists on the backend with a real `report_id`, and the app's report history switches that entry over from the local "Queued" placeholder to the real tracked report (FR-1.12).
6. **On repeated failure** (e.g., malformed data), the entry stays in `pending_uploads` with an error state the citizen can view and retry manually.

### 5.4 What Is Never Queued Offline

Viewing report history, status, and notifications (FR-1.12–1.15) requires connectivity by nature — these read from the backend. The offline capability here is scoped specifically to **report creation**, not to giving the whole app an offline-first data layer. This keeps the offline scope deliberately narrow and achievable within the project timeline, rather than attempting full offline sync for all data.

---

## 6. Camera/Media Capture Optimization Before Upload

### 6.1 Why This Matters

An uncompressed photo straight from a modern phone camera can be several megabytes. Uploading that directly, especially on a mobile data connection or a queued offline upload, is slow, wastes the citizen's data, and puts unnecessary load on Object Storage. Compression needs to happen **before** the upload step described in FR-1.11/FR-4.2 — not after.

### 6.2 Pipeline

1. **Capture** — photo is taken via `image_picker` (camera) or selected from gallery.
2. **Resize** — the image is downscaled to a maximum dimension (e.g., 1600px on the longest side) using `flutter_image_compress`. This is more than sufficient for the AI detection/classification pipeline (Section 11 of the proposal), which does not need full camera-sensor resolution to identify waste objects.
3. **Compress** — the resized image is re-encoded as JPEG at a quality setting (e.g., 80%) that balances visible quality against file size, using the same `flutter_image_compress` package.
4. **Strip metadata** — EXIF data (which can include precise GPS coordinates embedded in the image itself, separate from the report's own GPS field) is stripped during compression, both to reduce file size further and to avoid redundant/conflicting location data living in two places (the image's EXIF vs. `REPORTS.latitude`/`longitude`).
5. **Store compressed result** — the compressed file replaces the raw capture in the draft (Section 5), so the Hive-stored draft never holds the full-size original, keeping local storage usage low for citizens with many queued drafts.
6. **Upload** — only the final, compressed file is sent to Object Storage (per the Images Entity Schema's upload flow).

### 6.3 Target Benchmarks

| Stage | Target |
|---|---|
| Max dimension after resize | 1600px longest side |
| JPEG quality | 80% |
| Target final file size | Under 500 KB per photo (typical case) |
| Compression time | Under 1 second on a mid-range device, so it doesn't noticeably delay the review screen (FR-1.10) |

These are starting targets, not hard requirements — they should be validated against real device testing once the AI team confirms the minimum image quality their detection model needs (tying back to the Waste Detection Requirements document).

---

## 7. Summary of Package Choices

| Concern | Package |
|---|---|
| State management | `flutter_bloc` (Cubit for most features; full Bloc for the offline sync queue) |
| Maps | `google_maps_flutter` |
| GPS | `geolocator` |
| Local draft/queue storage | `hive` + `hive_flutter` |
| Connectivity detection | `connectivity_plus` |
| Image capture | `image_picker` |
| Image compression | `flutter_image_compress` |

---

## 8. Summary

- The app uses a feature-based modular structure (`auth`, `reporting`, `tracking`, `notifications`), following MVVM: View (presentation/), ViewModel (application/, as Cubits), Model (data/) — with no feature importing another feature's internals directly.
- Cubit is the default state management choice, using one consolidated state object per concern (e.g., the whole report draft as a single `ReportDraftState`) rather than many fragmented state holders; full Bloc is reserved for the offline sync queue, where distinct named events add real value.
- Google Maps handles location picking, used to let citizens confirm/fine-tune an auto-captured GPS point rather than manually search for an address, preserving FR-1.7's intent.
- Offline report drafting uses Hive for local draft and pending-upload queues, with a connectivity listener triggering background sync — scoped specifically to report creation, not full offline-first app behavior.
- Every photo is resized, compressed, and stripped of EXIF metadata before upload, keeping file sizes small and local storage usage low for queued offline drafts.
