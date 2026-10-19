# YOLOv8 Detection Model Specification & AI Two-Stage Inference Pipeline

**Task:** YOLOv8 Detection Model Architecture & Inference Pipeline
**Package:** Computer Vision Pipeline & Dataset Preparation
**Scope:** input tensor dimensions · confidence cut-offs · Non-Maximum Suppression (NMS) parameters · visual two-stage pipeline (Proposal §11.1–11.3)

> **How to read the values in this document.** Every parameter is tagged with its basis (see §10): **Framework default** (fixed by Ultralytics YOLOv8), **Measured** (taken from our TACO audit), or **Design choice** (decided by the team, with an initial value that must be tuned on the validation split). Nothing in this document is a measured *result* of a trained model — no model has been trained yet.

---

## 1. Purpose and Scope

CleanStreet AI analyses a citizen-submitted street photo in two stages (Proposal §11.1 waste detection, §11.2 waste classification):

1. **Stage 1 — Detection (this document).** A YOLOv8 object detector finds *where* litter is in the photo and returns bounding boxes.
2. **Stage 2 — Classification.** Each detected box is cropped and classified into a material category (see *Waste Classification Requirements*).

The Stage-1 output feeds the priority-scoring formula (Proposal §11.3 — quantity of waste comes from the number/area of detected boxes). The detector is trained on the cleaned, leakage-free TACO split produced by `scripts/ai/clean_taco.py` (see *TACO Dataset Analysis*).

---

## 2. Model Selection

### 2.1 Why YOLOv8

YOLOv8 (Ultralytics) is a single-stage, **anchor-free** detector. Its main architectural elements:

| Component | YOLOv8 design |
|---|---|
| Backbone | CSP-style backbone built from **C2f** blocks (replaces C3 of YOLOv5) with an SPPF layer |
| Neck | Path-aggregation (PAN-style) feature fusion |
| Head | **Decoupled / split head** — separate branches for box regression and classification; anchor-free |
| Detection scales | 3 scales, strides **8, 16, 32** |
| Loss | BCE (classification) + CIoU and Distribution Focal Loss (box regression), task-aligned assignment |

The proposal (Section 12) selects YOLOv8/YOLOv5 as the first detection candidate for its accuracy/speed balance, which matters because a citizen expects prompt feedback after submitting a report. Faster R-CNN stays a benchmark only.

### 2.2 Model size candidates

Reference figures published by Ultralytics (COCO val, input 640; **not** our data and **not** our hardware):

| Variant | Params (M) | FLOPs (B) | mAP val 50-95 (COCO) | CPU ONNX speed (ms)* |
|---|---|---|---|---|
| YOLOv8n | 3.2 | 8.7 | 37.3 | 80.4 |
| **YOLOv8s** | **11.2** | **28.6** | **44.9** | **128.4** |
| YOLOv8m | 25.9 | 78.9 | 50.2 | 234.7 |

\* Ultralytics reference benchmark hardware; our latency must be measured separately (§9.3).

**Decision (design choice): baseline = YOLOv8s**, initialised from COCO-pretrained weights (transfer learning, as in Proposal §12). It sits between the lightweight `n` and the heavier `m`. **YOLOv8n** is the fallback if server latency is too high; **YOLOv8m** is the accuracy upper bound. The final variant is selected by benchmarking all three on the cleaned TACO *validation* split for accuracy and measured latency.

### 2.3 Label space

| Variant | Classes (`nc`) | Use |
|---|---|---|
| **Primary — single-class detector** | 1 (`litter`) | Localisation only. Material is assigned by Stage 2. Produced with `clean_taco.py --classes-mode single`. |
| Benchmark — 18-class detector | 18 (TACO classes) | Comparison baseline only |

Rationale: with a separate classifier in Stage 2, the detector's job is to *find* litter. TACO's classes include catch-all labels (*Unlabeled litter* and *Other litter* = 13.9% of boxes) that carry no material meaning.

---

## 3. Input Specification

| Property | Specification |
|---|---|
| Tensor layout | `[B, 3, H, W]` — batch, channels (RGB), height, width |
| Data type / range | float32, pixel values divided by 255 → **0.0–1.0** |
| Colour order | RGB |
| Resize method | **Letterbox**: scale so the long side = 640, keep aspect ratio, pad with grey value **114** |
| Dimension constraint | `H` and `W` must be multiples of **32** (largest stride) |
| Training/inference size (`imgsz`) | **640** (design choice; ablation at 416, see below) |

**Shapes (computed):**

| Case | Original photo | Model input tensor |
|---|---|---|
| Landscape 4:3 phone photo (rectangular inference) | 4032 × 3024 | `(1, 3, 480, 640)` |
| Portrait 3:4 phone photo | 3024 × 4032 | `(1, 3, 640, 480)` |
| Fixed-shape export (ONNX/TFLite) | any | `(1, 3, 640, 640)` |

**Why 640 and not the dataset's native 416.** Our TACO export is a fixed **416×416** (stretch-resized; measured in the audit). Training at 640 matches the YOLOv8 default and the scale of the COCO-pretrained weights, and gives the detector larger feature maps for small objects: measured in the audit, **59.9%** of training boxes are smaller than 32×32 px at 416. Up-scaling does not add real detail, so this is a **hypothesis to validate**: `imgsz=640` vs `imgsz=416` are both trained and compared on validation small-object AP; the better one becomes final. Inference on citizen photos (any resolution) always letterboxes to the chosen `imgsz`.

**Pre-processing before letterbox (shared with the AI Architecture document):** validate JPEG/PNG, correct EXIF orientation, reject corrupted uploads.

---

## 4. Output Specification

### 4.1 Raw network output

| Variant | Raw output shape at 640×640 | Meaning |
|---|---|---|
| Single-class (`nc=1`) | `(1, 5, 8400)` | 4 box values (x, y, w, h in input pixels) + 1 class score, for each of 8,400 candidate points |
| 18-class (`nc=18`) | `(1, 22, 8400)` | 4 box values + 18 class scores |

- Candidate points = `80² + 40² + 20² = 6,400 + 1,600 + 400 = 8,400` (strides 8/16/32 at 640×640). For `(480, 640)` input: `60·80 + 30·40 + 15·20 = 6,300`. For 416×416: `52² + 26² + 13² = 3,549`.
- There is **no separate objectness score** in the YOLOv8 detect head: the confidence of a candidate is its highest class score (for `nc=1`, the single `litter` score).

### 4.2 Post-processed output (after confidence filter + NMS)

One list per image; coordinates are rescaled back to the **original photo's pixels**:

```
[ x1, y1, x2, y2, confidence, class_id ]   # at most max_det rows
```

---

## 5. Confidence Cut-offs

Confidence is the detector's class score (0–1). Three different cut-offs are used for three different purposes:

| Purpose | Cut-off | Basis | Behaviour |
|---|---|---|---|
| **Evaluation** (mAP, PR curves) | **0.001** | Framework default for validation | Very low on purpose, so the full precision–recall curve is computed |
| **Deployment — keep** | **≥ 0.25** | Framework default for prediction; *initial* value, to be tuned | Boxes below 0.25 are discarded |
| **Operator-facing tiers** | **≥ 0.50** → confident · **0.25–0.50** → `low_det_conf` flag | Design choice | Both tiers are kept and sent to Stage 2; the flag is shown to the operator |

**Tuning procedure.** The deployment cut-off is chosen on the cleaned **validation** split (never the test split) from the precision/recall/F1-vs-confidence curves, targeting the best F1 unless the team decides to favour recall. The final value is then recorded in this document and frozen before the single evaluation on the test split.

**Why not simply discard everything below 0.50?** (This refines the 50% figure used as a starting threshold in the *AI Architecture* document.) 59.9% of TACO training boxes are small, and small objects naturally receive lower confidence; a 0.50 hard cut would remove many real items and understate the *quantity* factor of the priority score. Keeping 0.25–0.50 boxes with a visible flag preserves recall while still letting the operator judge — consistent with the principle that AI assists and the operator decides.

**Report-level rule:** if no box reaches the deployment cut-off, the report is marked `no_waste_detected` and routed to manual operator review (it is never silently dropped).

---

## 6. Non-Maximum Suppression (NMS) Parameters

NMS removes duplicate boxes: boxes are sorted by confidence, and any box overlapping a higher-confidence box of the same class by more than the IoU threshold is suppressed. A **lower** IoU threshold suppresses more (fewer boxes); a **higher** one keeps more overlapping boxes.

| Parameter | Value | Basis | Notes |
|---|---|---|---|
| `iou` (NMS IoU threshold) | **0.70** (initial) | Framework default | Tuning grid {0.50, 0.60, 0.70} on the validation split, chosen by F1/recall and duplicate-box rate. Litter in TACO is often small and densely packed (e.g. cigarette butts, bottle caps), so over-suppression is the main risk. |
| `agnostic_nms` | **False** | Framework default | Class-aware NMS. Irrelevant for the single-class detector (only one class). |
| `max_det` | **100** | Design choice (framework default is 300) | The audit measured a maximum of **90** boxes in one TACO image. Capping at 100 also bounds how many crops Stage 2 must classify per report. If exceeded: keep the top 100 by confidence and set the `dense_scene` flag. |

---

## 7. Fine-Tuning Configuration (initial)

| Item | Value |
|---|---|
| Initial weights | `yolov8s.pt` (COCO-pretrained) |
| Dataset | Cleaned TACO from `clean_taco.py` (leakage-free, class-stratified 80/10/10 split); single-class variant primary |
| Epochs / batch | 100 / 16 (Ultralytics defaults) with early stopping enabled — first baseline, adjusted after the first run |
| Augmentation | Ultralytics built-in augmentation (mosaic, flips, HSV, scale…). Because the TACO export already contains flipped/rotated copies, `--dedupe-groups` (one image per photo, 3,665 photos) is recommended for training to avoid redundant copies |
| Class imbalance | Not relevant to the single-class detector; for the 18-class benchmark the audit shows a 15:1 imbalance (largest vs smallest class) |

---

## 8. Two-Stage Inference Pipeline

![CleanStreet AI two-stage inference pipeline](figures/ai-two-stage-inference-pipeline.png)

### 8.1 Stage contracts

| # | Step | Input | Output | Rules |
|---|---|---|---|---|
| 1 | Ingestion | Citizen photo | Stored image + AI job | Asynchronous: submission is never blocked by AI |
| 2 | Pre-processing | Image | Tensor `(1, 3, H, W)` | EXIF fix, RGB, ÷255, letterbox to 640 |
| 3 | **Stage 1 — YOLOv8** | Tensor | Boxes `[x1, y1, x2, y2, conf]` | conf ≥ 0.25 · NMS IoU 0.70 · `max_det` 100 |
| 4 | Crop extractor | Photo + boxes | One crop per box | +10% margin (clamped to the image); crops with shorter side < 32 px are skipped and flagged `too_small`; resize to 224×224 |
| 5 | **Stage 2 — classifier** | Crop | Material category + confidence | Confidence < 0.50 → `low_cls_conf` (see *Waste Classification Requirements*) |
| 6 | Aggregation | All detections | AI result JSON | Passed to priority scoring and the operator dashboard |

The crop margin (10%) and the minimum crop size (32 px) are **design choices with initial values** to be tuned on the validation split.

### 8.2 AI result (illustrative values)

```json
{
  "image": { "width": 4032, "height": 3024, "model_input": [480, 640] },
  "detector": { "model": "yolov8s", "conf": 0.25, "iou": 0.70, "max_det": 100 },
  "detections": [
    { "id": 1, "bbox_xyxy": [1210, 1804, 1498, 2150], "det_conf": 0.83,
      "material": "Plastic", "cls_conf": 0.91, "flags": [] },
    { "id": 2, "bbox_xyxy": [2210, 2604, 2240, 2631], "det_conf": 0.31,
      "material": null, "cls_conf": null, "flags": ["low_det_conf", "too_small"] }
  ],
  "report_flags": []
}
```

Flags: `low_det_conf` (0.25–0.50) · `low_cls_conf` (< 0.50) · `too_small` · `dense_scene` · `no_waste_detected` (report level).

### 8.3 Failure handling

| Situation | Behaviour |
|---|---|
| Corrupted / unreadable image | Rejected at ingestion with a clear error to the app |
| No box ≥ 0.25 | `no_waste_detected`, manual operator review |
| > 100 boxes | Top 100 kept, `dense_scene` flag |
| Box too small to classify | `too_small`; still counted toward the *quantity* factor of priority scoring |
| AI service unavailable | Report is still created and shown to operators as "analysis unavailable" (never blocks the citizen) |

---

## 9. Evaluation Protocol and Targets

### 9.1 Metrics

- **mAP@0.5** — primary metric, as in Proposal §22.
- mAP@0.5:0.95, precision and recall at the chosen operating confidence.
- **AP by object size** (small < 32², medium 32²–96², large ≥ 96², in pixels² at the training resolution) — important because ~60% of boxes are small.
- Per-class AP for the 18-class benchmark (with a caution for *Broken glass*, which exists in only 39 distinct photos).
- Comparison against the **pretrained-only baseline without fine-tuning**, as the proposal requires.

### 9.2 Target

The proposal's working target is **mAP@0.5 ≥ 0.50**. It was written for the Domestic Trash / Garbage dataset; for this project it is applied to the **cleaned TACO test split** and must be **confirmed after the first baseline run**, because the small-object share is high. Metrics are reported only on the leakage-free split, never on the original TACO `valid`/`test` (24.7% and 42% of their images were found to be copies of training photos).

### 9.3 Latency benchmark protocol

Measure on the target server hardware: median and 95th-percentile end-to-end time (pre-processing → NMS) over **100 images** at the chosen `imgsz`, excluding the first (warm-up) call. Report Stage 1 and Stage 2 separately. No latency figure is claimed until this is run.

---

## 10. Parameter Register

| Parameter | Value | Basis |
|---|---|---|
| Model | YOLOv8s (fallback n, upper bound m) | Design choice |
| Initial weights | COCO-pretrained `yolov8s.pt` | Proposal §12 (transfer learning) |
| Input tensor | `[B, 3, H, W]`, RGB, float32 0–1 | Framework |
| `imgsz` | 640 (ablation 416) | Design choice |
| Letterbox pad / stride rule | 114 / multiples of 32 | Framework |
| Native dataset resolution | 416×416 | Measured (TACO audit) |
| Small objects (< 32×32 px) | 59.9% of train boxes | Measured (TACO audit) |
| Max boxes in one image (TACO) | 90 | Measured (TACO audit) |
| Candidate points @640 / @416 | 8,400 / 3,549 | Computed from strides 8/16/32 |
| Raw output | `(1, 4+nc, N)` | Framework |
| Evaluation `conf` | 0.001 | Framework default (val) |
| Deployment `conf` | 0.25 (tuned on valid) | Framework default (predict) + tuning |
| Confident tier | ≥ 0.50 | Design choice |
| NMS `iou` | 0.70 (grid 0.5/0.6/0.7) | Framework default + tuning |
| `agnostic_nms` | False | Framework default |
| `max_det` | 100 | Design choice (audit max = 90) |
| Crop margin / min crop size | 10% / 32 px | Design choice (initial) |
| Classifier input | 224×224 | *Waste Classification Requirements* |
| Classifier low-confidence flag | < 0.50 | *Waste Classification Requirements* |
| Target mAP@0.5 | ≥ 0.50 (to be confirmed) | Proposal §22 |

---

## 11. Alignment with Other Project Documents

| Document | Alignment |
|---|---|
| *AI Waste Detection, Classification & Severity Scoring Architecture* | Same two-stage flow. **One refinement:** the detection cut-off there (50%, described as configurable) becomes the *confident tier*; boxes between 0.25 and 0.50 are kept with a `low_det_conf` flag instead of being discarded (§5). |
| *Waste Classification Requirements* | Stage 2 input = detected-object crops; 224×224; confidence < 0.50 flagged as low confidence — unchanged. |
| *TACO Dataset Analysis & Cleaning Pipeline* | Uses the cleaned leakage-free split, the single-class option, the measured 90-box maximum and the 59.9% small-object share. |
| Proposal §11, §12, §22 | §11.1–11.3 define the stages and scoring link; §12 names YOLOv8 with transfer learning; §22 sets the mAP@0.5 target. |

---

## 12. Verification Checklist

- [ ] A 4032×3024 photo produces an input tensor of shape `(1, 3, 480, 640)`; fixed-shape export produces `(1, 3, 640, 640)`.
- [ ] Raw output has `4 + nc` rows (5 for single-class, 22 for 18-class) and 8,400 columns at 640×640.
- [ ] Final boxes are in original-photo pixel coordinates, at most 100 per image, none below the deployment confidence.
- [ ] Two boxes of the same class overlapping more than the NMS IoU threshold are never both returned.
- [ ] Images with no qualifying box produce `no_waste_detected` and appear in the operator review queue.
- [ ] Crops under 32 px are flagged `too_small` and not sent to the classifier.
- [ ] Metrics are computed on the cleaned split only; the final confidence and NMS values are chosen on validation and frozen before the test run.

---

## 13. References

- Ultralytics documentation — *YOLOv8 models* (architecture, variant parameters/FLOPs/mAP), *Predict mode* arguments (`conf` 0.25, `iou` 0.7, `imgsz` 640, `max_det` 300, `agnostic_nms` False), *Val mode* arguments (`conf` 0.001, `iou` 0.7, `max_det` 300). https://docs.ultralytics.com
- CleanStreet AI Graduation Project Proposal — §11, §12, §22.
- Project documents: *TACO Dataset Analysis* (`docs/design/ai/taco-dataset-analysis.md`), *Waste Classification Requirements*, *AI Detection, Classification & Severity Scoring Architecture*.
