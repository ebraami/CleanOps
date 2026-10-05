# AI Waste Detection, Classification & Severity Scoring Architecture

Design the AI Computer Vision & Severity Scoring architecture: image ingestion/pre-processing pipeline, model inference runtime (waste type detection and multi-class classification), confidence thresholds, and dynamic severity/priority scoring formula.

---

## 1. Overview

A citizen-submitted street photo passes through three sequential AI stages before a report is ready for an operator to act on:

```
Citizen photo
     │
     ▼
[1] Image Ingestion & Pre-processing
     │
     ▼
[2] Detection (YOLO) → bounding boxes per waste item
     │
     ▼
[3] Classification (per-crop) → material category + confidence
     │
     ▼
[4] Severity / Priority Scoring → single priority score
     │
     ▼
Report ready for operator review (Report List / Map View)
```

---

## 2. Image Ingestion & Pre-processing Pipeline

**Ingestion:**
- Citizen uploads a photo via the mobile app (Report Submission — in-scope feature per proposal Section 9).
- Image is uploaded to cloud storage (Firebase Storage) and a reference URL is attached to the new `REPORTS` row.
- A backend trigger (on new image upload) kicks off the AI pipeline asynchronously, so the citizen's submission is not blocked waiting for AI results.

**Pre-processing (applied before detection):**
1. **Format validation:** confirm the file is a valid JPEG/PNG; reject corrupted uploads with a clear error back to the app.
2. **Resize:** scale the image to the input resolution expected by the detection model (e.g., 640×640 for YOLOv8), preserving aspect ratio with padding as needed.
3. **Normalization:** pixel values scaled to the [0,1] range expected by the model.
4. **EXIF orientation correction:** many mobile photos carry rotation metadata; the image is re-oriented so detection isn't thrown off by a sideways/upside-down frame.
5. **(Optional) Basic quality check:** extremely dark, blurry, or near-blank images can be flagged for "low quality — AI analysis may be unreliable" rather than silently producing a poor detection result.

---

## 3. Model Inference Runtime

### 3.1 Stage A — Detection (Waste Type Localization)

- **Model:** YOLOv8, fine-tuned via transfer learning on the **TACO dataset** (12k files, ~4,200 training images, bounding-box annotations in YOLO format).
- **Input:** the pre-processed full street image.
- **Output:** a list of bounding boxes, each with a class label and confidence score (e.g., "litter detected" regions — TACO's categories).
- **Why YOLO:** single-pass inference gives the speed needed for a mobile-submission workflow where the citizen expects reasonably prompt feedback, at an acceptable accuracy trade-off versus slower two-stage detectors (e.g., Faster R-CNN), consistent with the proposal's Section 12 technical review.

### 3.2 Stage B — Classification (Material Categorization)

- **Model:** a CNN classifier, fine-tuned via transfer learning on **Garbage Classification v2** (~19,762 images, 10 classes), validated against **RealWaste** (4,752 images from an authentic landfill environment) to check generalization to non-studio, real-world conditions.
- **Input:** each individual bounding-box crop produced by Stage A — **not** the full image (per the Waste Classification Requirements document already defined).
- **Output per crop:**
```json
{
  "predicted_category": "Plastic",
  "confidence": 0.91
}
```
- **Target accuracy:** ≥75% top-1 accuracy on the RealWaste held-out validation set (matches the proposal's Section 22 success criterion).

### 3.3 Runtime Sequencing

- Detection runs once per image; classification runs once per detected crop (so one image may trigger multiple classification calls if multiple items are detected).
- Both models run as part of the same asynchronous backend job triggered at ingestion; results are written back to the report once both stages complete.
- If detection finds **zero** waste items, the pipeline stops after Stage A and the report is flagged for manual operator review (`"AI analysis: no waste detected"`) rather than proceeding to classification or scoring.

---

## 4. Confidence Thresholds

| Stage | Threshold | Behavior below threshold |
|---|---|---|
| Detection (per bounding box) | 50% | Boxes below 50% confidence are discarded before classification — treated as noise rather than a real detection. |
| Classification (per crop) | 50% | Result is still shown, but flagged `"low confidence"` for operator review rather than presented as a certain classification (per Waste Classification Requirements). |

These thresholds are configurable parameters (not hard-coded), so they can be tuned after initial testing without a model retrain — e.g., if false positives are too high at 50%, the detection threshold can be raised to 60–65%.

---

## 5. Dynamic Severity / Priority Scoring Formula

As established in prior planning: no public or local dataset exists that labels "severity" directly, so severity/priority is computed via an **interpretable, rule-weighted formula** rather than a separate trained model — consistent with the proposal's Section 12 guidance to use a rule-based baseline before considering a learned model (e.g., LightGBM) once real outcome data exists.

### 5.1 Formula

```
Priority Score = (WasteType_score × 0.4)
               + (Quantity_score   × 0.3)
               + (RepeatCount_score × 0.2)
               + (ReportAge_score  × 0.1)
```

All four sub-scores are normalized to a 0–10 scale before weighting, so the final `Priority Score` is also on a 0–10 scale.

### 5.2 Sub-score Definitions

| Factor | Source | How it's scored (0–10) |
|---|---|---|
| **WasteType_score** | Classification output (Stage B) | Each material category maps to a base hazard weight (e.g., broken glass/hazardous materials score higher than cardboard/paper). Mapping is a configurable lookup table, reviewable/adjustable by the team. |
| **Quantity_score** | Detection output (Stage A) | Derived from the number of detected bounding boxes and/or their combined area relative to the image — more items / larger coverage → higher score. |
| **RepeatCount_score** | `REPORTS` + historical data | Number of prior reports at the same or a nearby location (hotspot signal) — more repeats → higher score, capped at a maximum. |
| **ReportAge_score** | `REPORTS.created_at` | Time elapsed since submission without resolution — older unresolved reports score higher, up to a cap (to avoid indefinitely inflating very old reports). |

### 5.3 Example Calculation

For a report with: glass detected (WasteType_score = 10), 5 items detected (Quantity_score = 7), 3 prior reports at the same location (RepeatCount_score = 6), 2-day-old report (ReportAge_score = 3):

```
Priority Score = (10 × 0.4) + (7 × 0.3) + (6 × 0.2) + (3 × 0.1)
               = 4.0 + 2.1 + 1.2 + 0.3
               = 7.6 / 10
```

### 5.4 Why Rule-Based (Not ML) for the Initial Version

- **Interpretable:** operators can see exactly why a report was ranked as it was, and challenge/override it if needed — important given the proposal's explicit caution against treating AI output as an unquestionable determination (Section 11).
- **No severity-labeled training data exists** (confirmed via prior dataset research) — a learned model would have nothing to train on yet.
- **Future upgrade path:** once sufficient labeled outcome data accumulates from real operator decisions and pilot usage, weights can be replaced by a trained model (e.g., LightGBM) per the proposal's Section 12, without changing the rest of the architecture — only the scoring function is swapped.

---

## 6. Summary

| Stage | Model / Method | Dataset(s) | Target |
|---|---|---|---|
| Pre-processing | Resize, normalize, orientation correction | — | — |
| Detection | YOLOv8 (fine-tuned) | TACO | Locate waste items with bounding boxes |
| Classification | CNN (fine-tuned) | Garbage Classification v2 (train) / RealWaste (validate) | ≥75% top-1 accuracy |
| Severity/Priority | Rule-based weighted formula | N/A (no severity dataset exists) | Interpretable 0–10 priority score |

This architecture reuses every dataset and decision already finalized for the project (detection/classification datasets, confidence-threshold behavior, and the rule-based severity approach), so it introduces no new unvalidated assumptions.
