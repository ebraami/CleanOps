# External System / API Boundary — CleanStreet AI

**Package:** P01 — Project Foundation & Requirements → System Boundaries
**Task:** External System/API Boundary
**Prepared by:** Backend (Java Spring Boot)
**Based on:** CleanStreet AI Proposal — Sections 13 ("Data Sources and Requirements"), 14 ("Proposed Technology and Methodology"), 15 ("Data Architecture"), 17 ("Security and Privacy Considerations")

---

## 1. Purpose

This document identifies every external service that CleanStreet AI's backend depends on but does **not** control, and defines exactly what data crosses each boundary and in which direction. "Does not control" means: we cannot change its behavior, guarantee its uptime, or dictate its response format — we can only call it, handle what it returns, and degrade gracefully if it fails.

The Spring Boot backend sits in the middle of every one of these boundaries: no external service talks directly to our database, and (with one noted exception) no external service talks directly to our mobile app without passing through the backend first.

---

## 2. External Systems Covered

| # | External Service | Category | Who initiates the call |
|---|---|---|---|
| 1 | Firebase Authentication | Identity / Auth | Mobile app (client-side), verified by backend |
| 2 | Firebase Cloud Messaging (FCM) | Push notifications | Backend → FCM |
| 3 | Object Storage — Firebase Storage or Amazon S3 | File/image storage | Backend (or client, via signed URL) |
| 4 | Google Maps Routes API / OpenStreetMap | Maps & routing | Backend → API |
| 5 | OpenWeather | Weather context | Backend → API |

These map directly to the "External APIs and services" listed in Section 13 of the proposal and to the technology stack in Section 14.

---

## 3. Boundary Table — What Crosses In Each Direction

| External Service | Data CleanStreet AI Sends | Data Returned to CleanStreet AI | Backend Integration Point |
|---|---|---|---|
| **Firebase Authentication** | ID token issued to the mobile client after login/registration, forwarded by the backend to Firebase Admin SDK for verification on every protected API call | Decoded/verified token containing `uid`, `email`, `email_verified`, custom claims (e.g. role: citizen/operator), token expiry | Spring Security filter using **Firebase Admin SDK** (`FirebaseAuth.getInstance().verifyIdToken(token)`) executed before controller logic; `uid` is mapped to the local `USERS.id` |
| **Firebase Cloud Messaging** | Device registration token, notification title/body, data payload (e.g. `report_id`, `new_status`, `type: STATUS_UPDATE`) | Message ID and delivery/send status (success, or error code such as invalid/unregistered token) | A `NotificationService` bean calling **Firebase Admin SDK** (`FirebaseMessaging.send()`), triggered when `REPORTS.current_status` changes (see `STATUS_HISTORY`) |
| **Object Storage (Firebase Storage / S3)** | Image bytes (citizen report photo, or cleaning-team before/after photo) plus metadata (`report_id`, `image_type`); if using signed-URL uploads, backend instead sends a signed-URL *request* (file name, content type) | Either the stored object's public/permanent URL (`storage_url`) after backend-mediated upload, **or** a time-limited signed URL that the client uploads directly to, after which the client reports the final `storage_url` back to the backend | `ImageStorageService` using the **Firebase Admin SDK (Storage)** or **AWS SDK for Java (S3Client)**; result is persisted as `IMAGES.storage_url` |
| **Google Maps Routes API / OpenStreetMap** | Origin and destination coordinates (cleaning-team location, cluster of assigned report locations), travel mode | Route geometry/polyline, distance, estimated duration, and (for Routes API) a distance/duration matrix for multiple stops | `RoutingService` using Spring's `WebClient`/`RestTemplate`; consumed by the operations dashboard for route-optimization and map-based visualization (Sections 6, 11, 14) |
| **OpenWeather** | Latitude/longitude of a report or service area, optionally a timestamp for forecast lookups | Current conditions and/or forecast (temperature, precipitation, wind) for that location | `WeatherContextService` using `WebClient`; result attached to analytics/planning views, not stored as authoritative report data |

---

## 4. Per-Service Detail

### 4.1 Firebase Authentication
- **Direction:** Two-hop. The mobile client authenticates directly with Firebase (outside our backend's control) and receives a short-lived ID token. The client attaches that token to every backend API call; the backend's only interaction with Firebase is **verifying** that token server-side.
- **What we send:** the ID token string (we never send credentials/passwords — we never see them).
- **What we get back:** a verified, decoded token (`uid`, `email`, custom claims) or a verification failure (expired/invalid/revoked token).
- **What we do NOT control:** Firebase's own login UX, password rules, token lifetime, or outage behavior. If Firebase Authentication is down, no one can log in — this is an accepted external dependency, not something the backend can work around.
- **Backend responsibility:** map `uid` → local `USERS` row on first login (provisioning), enforce role-based authorization (citizen vs. operator) using the custom claim, reject requests with missing/invalid tokens with `401`.

### 4.2 Firebase Cloud Messaging (FCM)
- **Direction:** One-way, backend → FCM → device. The backend never receives a message back from the citizen's device through this channel; it only gets an FCM-level delivery acknowledgement.
- **What we send:** device token (stored per user), notification payload (title, body) and/or a silent data payload for in-app handling.
- **What we get back:** an FCM message ID on success, or an error indicating the token is invalid/expired (which should trigger cleanup of that stale token).
- **What we do NOT control:** whether the OS actually surfaces the notification, delivery latency, or the user's device notification settings.
- **Backend responsibility:** trigger sends from `STATUS_HISTORY` changes, retry/skip on transient FCM errors, and prune invalid tokens.

### 4.3 Object Storage (Firebase Storage or Amazon S3)
- **Direction:** Depends on the chosen upload pattern — this is flagged as an **open implementation decision** (see Section 6):
  - *Backend-mediated upload:* client → backend → storage. Backend receives the image, forwards it to storage, gets back a URL.
  - *Direct client upload (signed URL):* backend → storage (request a signed URL only) → client uploads directly to storage → client reports the resulting URL back to backend for persistence.
- **What we send:** image bytes + metadata (mediated), or just a signed-URL request (direct).
- **What we get back:** a `storage_url` to persist in `IMAGES.storage_url` (per Section 15.2's schema).
- **What we do NOT control:** storage provider uptime, upload bandwidth/latency, or file size limits imposed by the provider.
- **Backend responsibility:** validate file type/size before persisting metadata, generate/verify signed URLs if that pattern is chosen, and enforce the retention/deletion policy referenced in Section 17.

### 4.4 Google Maps Routes API / OpenStreetMap
- **Direction:** One-way request/response, backend → API, used for route planning (Section 6, "Investigate route optimisation") and map-based visualization.
- **What we send:** coordinates of the cleaning team and of the reports assigned to them (no personal data — just lat/long pairs and identifiers already internal to us).
- **What we get back:** route polyline, distance, ETA, or a distance/duration matrix for multi-stop planning.
- **What we do NOT control:** traffic-model accuracy, API quota/rate limits, or pricing tiers.
- **Backend responsibility:** cache/reuse route results where reasonable to control API cost, and fail gracefully to a simple map view (no routing) if the API is unavailable — per Section 19's mitigation ("map-based visualisation first, independently useful without full routing").

### 4.5 OpenWeather
- **Direction:** One-way request/response, backend → API, used for planning/analytics context (Section 13).
- **What we send:** latitude/longitude (and optionally a date/time for forecast).
- **What we get back:** current weather or forecast data.
- **What we do NOT control:** forecast accuracy or API availability.
- **Backend responsibility:** treat this as supplementary context only — never a blocking dependency for core reporting/prioritisation functionality, since weather is not part of the priority-scoring formula in Section 11.

---

## 5. Cross-Cutting Backend Responsibilities

These apply at every boundary above and are worth stating explicitly so they don't get flagged in review:

- **Secrets management:** all API keys/credentials (Firebase service account JSON, Google Maps API key, OpenWeather API key, AWS/S3 credentials) are kept in environment variables / `application.yml` profiles — never hardcoded or committed to the repo.
- **Timeouts & retries:** every outbound call (Maps, OpenWeather, FCM, Storage) uses an explicit timeout and a bounded retry policy (e.g. via **Resilience4j**) so a slow/unavailable third party cannot hang the request thread.
- **Failure isolation:** none of these five services being down should crash core reporting. Only Firebase Authentication is a hard dependency (no auth, no access); the other four degrade gracefully (Section 19's mitigation approach).
- **No direct external → database access:** all five services interact only with the backend layer; none of them read from or write to PostgreSQL/PostGIS directly. This is what makes the backend the actual system boundary.

---

## 6. Open Questions for the Team

1. **Storage upload pattern** — backend-mediated vs. direct-to-storage signed URL. This affects the mobile team's upload implementation and should be confirmed jointly.
2. **Maps provider** — Google Maps Routes API vs. OpenStreetMap-based routing; proposal (Section 14) leaves this "subject to the team's final technology decision," largely a cost/quota question.
3. **Object Storage provider** — Firebase Storage vs. Amazon S3; affects which SDK the backend integrates.

These three are flagged rather than decided unilaterally, since they affect the mobile and infrastructure roles as well.
