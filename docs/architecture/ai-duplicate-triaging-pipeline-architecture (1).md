# AI Duplicate Triaging & Service Pipeline Integration Architecture

**Status:** In Progress
**Priority:** High
**Package:** [System Architecture](https://cleanops-hq.pages.dev/#/wp/WP_44892d)

Design the AI duplicate report triaging and pipeline integration architecture: visual embedding extraction, spatio-temporal clustering algorithms, AI microservice container topology, and webhook/event payloads between Supabase Edge Functions and the AI pipeline.

---

## 1. Overview

This document specifies how the system detects **candidate duplicate reports** — reports that likely describe the same real-world waste event — and how that detection integrates with the rest of the pipeline (detection, classification, priority scoring).

**Design principle (carried over from Operator Functions — Analytics & Monitoring):** The AI pipeline never auto-merges reports. It produces a **ranked list of duplicate candidates with a similarity score**; the final merge decision is always made by a human operator in the Operations Dashboard. This document defines the architecture that produces those candidates, not an auto-merge mechanism.

---

## 2. Visual Embedding Extraction

**Purpose:** Convert each report's image into a compact numeric vector ("embedding") that captures visual similarity, independent of exact pixel match, so visually similar waste scenes can be compared mathematically.

**Pipeline step:**
1. On report submission, the uploaded image is passed through a pretrained CNN feature-extraction backbone (ResNet50 or MobileNetV3, run in inference-only mode — no fine-tuning required for this step) to produce a fixed-length embedding vector (e.g., 512 or 1024 dimensions).
2. The embedding is computed **once per report**, immediately after image validation (size/format checks), and stored alongside the report record (not inside the detection/classification model path — this is a separate, lightweight pass).
3. Embeddings are stored in a vector-indexable column (e.g., `pgvector` extension if using Supabase/Postgres) to allow approximate nearest-neighbor search.

**Why a separate lightweight model, not YOLOv8 itself:** YOLOv8 (used for waste detection, per Waste Detection Requirements) outputs bounding boxes and class labels, not a single whole-image similarity vector. Embedding extraction is a distinct, cheaper inference pass optimized for similarity comparison rather than object localization.

---

## 3. Spatio-Temporal Clustering Heuristics

**Purpose:** Narrow down which reports are even worth comparing visually, before running the (more expensive) embedding similarity check — and combine location/time proximity with visual similarity into one duplicate-candidate score.

**Stage A — Spatial & temporal pre-filtering:**
- Only reports within a **50-meter radius** and submitted within **7 days** of each other are considered for duplicate comparison (consistent with the Recurring Reports threshold already defined in Operator Functions — Analytics & Monitoring).
- This filtering happens first, using plain location/timestamp queries, to avoid running embedding comparisons against the entire report database.

**Stage B — Visual similarity scoring:**
- For each pair of reports that pass Stage A, compute cosine similarity between their image embeddings.
- A pair is flagged as a **duplicate candidate** if cosine similarity ≥ 0.85 (initial working threshold, tunable after real-usage data).

**Stage C — Combined candidate score:**
- `duplicate_score = (0.6 × visual_similarity) + (0.25 × proximity_score) + (0.15 × recency_score)`
- `proximity_score` and `recency_score` are normalized 0–1 values derived from distance (closer = higher) and time gap (closer in time = higher).
- Candidates with `duplicate_score ≥ 0.7` are surfaced to the operator as a **suggested duplicate group**, matching the "recurrence count" indicator defined in the Recurring Reports function.

---

## 4. AI Microservice Container Topology

**Purpose:** Define how the AI workloads (detection, classification, embedding extraction, clustering) are deployed and isolated from the main backend.

```
┌─────────────────────────┐        ┌──────────────────────────────┐
│   Supabase Backend       │        │      AI Service Cluster        │
│ (Edge Functions, DB,     │        │  (containerized, separate      │
│  Auth, Storage)          │        │   from the main backend)       │
│                           │        │                                │
│  - report-intake EF       │──────▶│  ┌──────────────────────────┐  │
│  - duplicate-check EF     │◀──────│  │ detection-service         │  │
│                           │        │  │ (YOLOv8 inference)        │  │
│                           │        │  └──────────────────────────┘  │
│                           │        │  ┌──────────────────────────┐  │
│                           │        │  │ embedding-service          │  │
│                           │        │  │ (CNN backbone inference)   │  │
│                           │        │  └──────────────────────────┘  │
│                           │        │  ┌──────────────────────────┐  │
│                           │        │  │ clustering-service          │  │
│                           │        │  │ (spatio-temporal + vector   │  │
│                           │        │  │  similarity scoring)         │  │
│                           │        │  └──────────────────────────┘  │
└─────────────────────────┘        └──────────────────────────────┘
```

- Each AI capability (**detection-service**, **embedding-service**, **clustering-service**) runs as an **independently deployable container**, so the detection model (YOLOv8) can be retrained/redeployed without affecting embedding extraction or clustering logic.
- Services communicate internally over HTTP/REST, each exposing a single `/infer` endpoint that accepts an image reference (not raw image bytes) and returns structured JSON output.
- Containers read images directly from Supabase Storage via a signed URL passed in the request payload, avoiding large binary transfer through the Edge Function layer.
- Services are stateless; all persistent state (embeddings, scores, candidate groups) is written back to the Supabase database, not held in-memory between requests.

---

## 5. Edge-to-AI Asynchronous Webhook Contracts

**Purpose:** Define how Supabase Edge Functions and the AI pipeline exchange events without blocking the citizen-facing submission flow (the citizen should not wait for AI processing to complete before their report is confirmed as submitted).

**Flow:**
1. Citizen submits a report → `report-intake` Edge Function saves the report with status `SUBMITTED` and returns a tracking number immediately (no AI wait).
2. `report-intake` fires an asynchronous webhook event to the AI Service Cluster.
3. AI services process the image (detection → embedding → clustering) and, on completion, call back an Edge Function webhook to update the report record.

**Event payload — Edge → AI (`report.created`):**
```json
{
  "event": "report.created",
  "report_id": "REP-2026-0089",
  "image_url": "<signed-storage-url>",
  "location": { "lat": 29.9765, "lng": 31.1313 },
  "submitted_at": "2026-10-03T14:22:00Z"
}
```

**Event payload — AI → Edge (`ai.processing_complete`):**
```json
{
  "event": "ai.processing_complete",
  "report_id": "REP-2026-0089",
  "detections": [
    { "class": "Plastic bag - wrapper", "confidence": 0.91, "bbox": [x, y, w, h] }
  ],
  "embedding_id": "emb_8f21c3",
  "duplicate_candidates": [
    { "report_id": "REP-2026-0071", "duplicate_score": 0.82 }
  ],
  "processed_at": "2026-10-03T14:22:07Z"
}
```

**Contract rules:**
- Webhook calls in both directions are retried with exponential backoff (max 3 attempts) and must be idempotent — a repeated `ai.processing_complete` event for the same `report_id` must not create duplicate database rows.
- If the AI service cluster is unavailable, the report remains valid with status `SUBMITTED` and a `pending_ai_review` flag; it is retried by a scheduled job rather than blocking the citizen-facing flow.
- `duplicate_candidates` in the callback payload only **populate the operator's suggestion list** (per Section 3) — no automatic status change or merge occurs as a result of this event.

---

## 6. Duplicate Resolution Flow

1. AI pipeline produces `duplicate_candidates` for a new report (Section 5).
2. The candidate group becomes visible to the operator in the Operations Dashboard, under the existing "Recurring Reports" suggestion view.
3. The operator reviews the suggested group (seeing both reports' images, locations, and timestamps) and either:
   - **Confirms** → reports are grouped under one primary report with a recurrence count, or
   - **Dismisses** → reports remain independent, and the system does not re-suggest that specific pair again.
4. All resolution actions (confirm/dismiss) are logged with operator ID and timestamp for auditability.

---

> **Note:** Similarity thresholds (0.85 cosine similarity, 0.7 combined duplicate score) and the embedding backbone choice are initial working assumptions, consistent in spirit with the other threshold-based rules already defined in this project (e.g., Hotspot Detection, SLA Ageing). They are expected to be tuned once real usage data and a labeled validation set of true/false duplicate pairs are available.
