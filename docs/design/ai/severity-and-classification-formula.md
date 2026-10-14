# Severity & Classification Formula Specification

**Package:** Computer Vision Pipeline & Dataset Preparation (P02 — Design & Preparation)
**Deliverable path:** `docs/design/ai/severity-and-classification-formula.md`

Specify the CNN classification model applied to detected waste crops, and the formal mathematical formulas for the **Severity assessment** and **Priority ranking** calculations.

**Proposal references:** Section 11.2 (waste classification), Section 11.3 (priority prediction), Section 12 (interpretable rule-weighted baseline), Section 22 (success criteria).

---

## 1. Scope and Pipeline Position

```
Citizen photo
   │
   ▼
[1] Waste detection (YOLOv8, fine-tuned on TACO)  ──►  bounding boxes + confidence
   │
   ▼
[2] Crop each box  ──►  CNN classifier  ──►  material class + probabilities   (Section 2)
   │
   ▼
[3] Severity formula  ──►  score 0–100                                        (Section 3)
   │
   ▼
[4] Priority formula (severity + repeats + age + location)  ──►  score 0–100  (Section 4)
   │
   ▼
Operator dashboard / cleaning-team task list
```

**Design principles (from the proposal):**
- **Transparent over opaque.** Severity and Priority are rule-weighted formulas with named inputs and fixed weights, so an operator can see *why* a report ranked where it did and challenge it (Section 12 of the proposal). A learned model (e.g., LightGBM) is only evaluated later, once enough labeled outcome data exists.
- **AI assists, humans decide.** Scores order and flag reports; they never reject a report or assign work on their own. Operators can override any score (Section 5).

---

## 2. CNN Classification Model (on detected crops)

### 2.1 Role
The detector locates waste items; the classifier decides **what material** each one is. The classifier's output is the authoritative material label for downstream scoring.

**Output classes (10, unified taxonomy):** `battery`, `biological`, `cardboard`, `clothes`, `glass`, `metal`, `paper`, `plastic`, `shoes`, `trash`
(taxonomy mapping and training data are defined in the RealWaste & Garbage Classification v2 dataset analysis).

### 2.2 Input
| Item | Specification |
|---|---|
| Source | Crop of each detected bounding box that passes the detection confidence threshold (τ_det = 0.40) |
| Context margin | Box expanded by 10% on each side before cropping, so item edges are not cut off |
| Resize | 224 × 224, aspect-ratio-preserving (pad mode) — identical to the training preprocessing |
| Normalization | Pixels scaled to [0, 1], then per-channel standardization with ImageNet mean = [0.485, 0.456, 0.406], std = [0.229, 0.224, 0.225] |

### 2.3 Architecture
| Component | Specification |
|---|---|
| Backbone | ImageNet-pretrained CNN. **Primary candidate: EfficientNet-B0.** Alternatives to benchmark: MobileNetV3-Large (lighter/faster), ResNet50 (accuracy reference) |
| Pooling | Global average pooling over the final feature map |
| Head | Dropout (p = 0.2) → fully connected layer (feature dimension → 10) → softmax |
| Output | Probability vector `p = (p_1 … p_10)`, with Σ p_k = 1 |

The final backbone is chosen by benchmark on the validation set (accuracy and inference latency), consistent with Section 12 of the proposal. The numbers above are the starting configuration, not a final decision.

### 2.4 Training procedure (transfer learning)
1. **Phase 1 — head only:** freeze the backbone, train the new head for a few epochs (AdamW, learning rate 1e-3).
2. **Phase 2 — partial fine-tuning:** unfreeze the last backbone blocks, continue with a lower learning rate (1e-4) and cosine decay.
3. **Loss:** cross-entropy with label smoothing 0.1 and **class weights inversely proportional to class frequency** (the training data is imbalanced).
4. **Augmentation (train split only):** horizontal flip, small rotations, brightness/contrast/colour jitter, random crop-and-resize.
5. **Model selection:** early stopping on validation **macro-F1** (not plain accuracy, so small classes are not ignored).

### 2.5 Inference rules
- **Low-confidence handling:** if the top probability `max(p) < τ_cls` (initial τ_cls = 0.50), the item keeps its predicted label but is flagged **"low confidence"** in the report, for operator attention. It is never silently dropped.
- **Report-level summary:** a report's material summary is the count of detected items per material class, plus the dominant class (highest count; ties broken by summed detection confidence).

### 2.6 Evaluation
| Metric | Target / use |
|---|---|
| Top-1 accuracy on the held-out test split | **≥ 75%** across the primary waste categories (Proposal Section 22) |
| Macro-F1, per-class recall, confusion matrix | Reported alongside accuracy to expose weak classes |
| Accuracy on **detector crops** (not just clean dataset images) | Reported separately, because the classifier is trained on whole-item photos but applied to crops cut from street scenes |
| Accuracy on locally collected Egyptian images | Reported once available; public-dataset results are treated as a baseline, not a final figure |

---

## 3. Severity Assessment Formula

**Meaning:** how bad the waste problem *in the photo* is, based only on image evidence. Range 0–100.

### 3.1 Inputs per detected item *i* (only items with confidence c_i ≥ τ_det)
- `c_i` — detection confidence (0–1)
- `a_i` — bounding-box area as a fraction of the image area (0–1)
- `p_ik` — classifier probability that item *i* is material *k*

### 3.2 Components (each normalized to 0–1)

**Quantity**
```
N_eff = Σ c_i                       (confidence-weighted item count)
Q     = min(1, N_eff / N_max)       N_max = 10
```

**Coverage**
```
C = min(1, (Σ a_i) / A_max)         A_max = 0.30   (30% of the image covered = maximum)
```

**Hazard**
```
h_i = Σ_k p_ik · hz_k               (expected hazard of item i)
H   = max_i h_i                     (the most hazardous item drives the score)
```

Hazard weights `hz_k`:

| Material | hz | Reason |
|---|---|---|
| battery | 1.0 | Toxic / fire risk |
| glass | 0.6 | Cut risk |
| biological | 0.5 | Health and odour |
| metal | 0.4 | Sharp edges |
| cardboard, clothes, paper, plastic, shoes, trash | 0.2 | Baseline nuisance |

### 3.3 Severity score
```
S = 100 × ( w_q·Q + w_c·C + w_h·H )

w_q = 0.40     w_c = 0.40     w_h = 0.20     (weights sum to 1)
```

**Bands:** Low `0 ≤ S < 25` · Medium `25 ≤ S < 50` · High `50 ≤ S < 75` · Critical `75 ≤ S ≤ 100`

**Edge case — no detections:** `S = 0` and the report is flagged **"no waste detected — operator review"**. The system never auto-rejects a citizen report (Proposal Section 11: AI must not decide report validity).

### 3.4 Worked example
A photo with 4 detections:

| Item | c_i | a_i | Classifier output | h_i |
|---|---|---|---|---|
| 1 | 0.90 | 0.02 | glass 0.90, plastic 0.10 | 0.9×0.6 + 0.1×0.2 = **0.56** |
| 2 | 0.80 | 0.02 | plastic 0.85, trash 0.15 | 0.20 |
| 3 | 0.70 | 0.02 | paper 0.80, cardboard 0.20 | 0.20 |
| 4 | 0.60 | 0.02 | plastic 0.70, trash 0.30 | 0.20 |

```
N_eff = 0.9 + 0.8 + 0.7 + 0.6 = 3.0        →  Q = 3.0 / 10   = 0.300
Σ a_i = 0.08                                →  C = 0.08 / 0.30 = 0.267
H     = max(0.56, 0.20, 0.20, 0.20)         →  H = 0.560

S = 100 × (0.40×0.300 + 0.40×0.267 + 0.20×0.560)
  = 100 × (0.120 + 0.107 + 0.112)
  ≈ 33.9      →  Medium
```

---

## 4. Priority Ranking Calculation

**Meaning:** how urgently the report should be handled, combining image severity with context. Range 0–100. This maps to the four factors named in the proposal: severity, repeat occurrence, report age, and location.

### 4.1 Components (each normalized to 0–1)

| Component | Formula | Notes |
|---|---|---|
| Severity `s` | `s = S / 100` | From Section 3 |
| Repeat `r` | `r = min(1, R / 5)` | `R` = number of reports within 50 m in the last 30 days. Saturates at 5, the same threshold that defines a Hotspot (so `r = 1` means Hotspot) |
| Age `g` | `g = min(1, age_hours / 48)` | Saturates at 48 h, the SLA "overdue" threshold |
| Location `l` | zone sensitivity weight | See below |

**Location weight `l`** — derived from OpenStreetMap tags within 100 m of the report (OpenStreetMap is already a listed data source, Proposal Section 13):

| Zone | l |
|---|---|
| Sensitive: school, hospital, market, main road | 1.0 |
| Residential | 0.6 |
| Other / no zone data found | 0.3 |

Report *density* is captured by `r` and by the separate Area Burden analytics, so it is not counted twice here.

### 4.2 Priority score
```
P = 100 × ( w_s·s + w_r·r + w_a·g + w_l·l )

w_s = 0.40     w_r = 0.25     w_a = 0.20     w_l = 0.15     (weights sum to 1)
```

**Bands:** Low `0 ≤ P < 25` · Medium `25 ≤ P < 50` · High `50 ≤ P < 75` · Urgent `75 ≤ P ≤ 100`

**Ordering and tie-breaking:** reports are listed by `P` descending. Equal scores are ordered **oldest first** (by assignment time in the cleaning-team view, by submission time in the operator view), consistent with the Task List View requirements.

### 4.3 Worked example
Using the report from Section 3.4 (`S ≈ 33.9`), with 3 reports within 50 m in the last 30 days, open for 20 hours, in a residential zone:

```
s = 0.339
r = min(1, 3/5)  = 0.600
g = min(1, 20/48) = 0.417
l = 0.600

P = 100 × (0.40×0.339 + 0.25×0.600 + 0.20×0.417 + 0.15×0.600)
  = 100 × (0.1355 + 0.1500 + 0.0833 + 0.0900)
  ≈ 45.9      →  Medium
```

### 4.4 Explainability
For every report the system stores the component values and weights, so the dashboard can show "why this rank":
```json
{
  "severity": { "S": 33.9, "Q": 0.300, "C": 0.267, "H": 0.560 },
  "priority": { "P": 45.9, "s": 0.339, "r": 0.600, "g": 0.417, "l": 0.600 },
  "weights":  { "w_s": 0.40, "w_r": 0.25, "w_a": 0.20, "w_l": 0.15 }
}
```

---

## 5. Operator Override and Audit

- An operator may manually set a report's priority band. The original computed `P` is kept, and the override (new value, operator ID, timestamp, reason) is written to the audit log (Proposal Section 16).
- Overrides are never discarded; they become labeled data for later tuning of the weights.

---

## 6. Validation Plan

Success criterion (Proposal Section 22): the priority ranking agrees with an independent human operator ranking on **at least 70%** of a sampled test set.

- **Primary metric — pairwise agreement:** sample report pairs, count how often the formula's order (which of the two is higher priority) matches the operator's order. Target ≥ 70%.
- **Secondary metric — band agreement:** share of reports where the computed band equals the operator-assigned band.
- **Tuning:** the weights (`w_*`), the caps (`N_max`, `A_max`, 5 reports, 48 h) and the hazard table are adjusted by grid search against operator rankings. A learned model (LightGBM) is evaluated only if enough labeled data exists to justify it over this baseline.

---

## 7. Parameter Summary

| Parameter | Initial value | Used in |
|---|---|---|
| τ_det (detection confidence cutoff) | 0.40 | Severity |
| τ_cls (low-confidence flag) | 0.50 | Classifier |
| N_max | 10 items | Quantity |
| A_max | 0.30 of image | Coverage |
| w_q, w_c, w_h | 0.40, 0.40, 0.20 | Severity |
| Repeat saturation | 5 reports / 50 m / 30 days | Priority (matches Hotspot rule) |
| Age saturation | 48 h | Priority (matches SLA overdue rule) |
| w_s, w_r, w_a, w_l | 0.40, 0.25, 0.20, 0.15 | Priority |
| Band cut-offs | 25 / 50 / 75 | Severity and Priority |

---

## 8. Limitations

- **All weights, caps and hazard values are initial working assumptions**, chosen to be reasonable and explainable. They are not learned from data and should be validated with operators and tuned (Section 6).
- **Coverage ignores box overlap.** Summing box areas can double-count overlapping detections; this slightly overstates coverage in crowded scenes.
- **Domain shift.** The classifier is trained on whole-item photos from public datasets but applied to crops from street scenes; accuracy on detector crops may be lower than dataset accuracy until local images are added.
- **Severity is a proxy.** It estimates visible burden from a single photo; it does not measure the physical amount of waste.
- **Location data dependency.** The location weight relies on OpenStreetMap coverage; where no zone data exists the neutral default (0.3) is used.
