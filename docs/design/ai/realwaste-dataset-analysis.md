# RealWaste & Garbage Classification v2 — Dataset Analysis

**Package:** Computer Vision Pipeline & Dataset Preparation (P02 — Design & Preparation)
**Priority:** High
**Companion script:** `scripts/ai/clean_realwaste.py`

Analyze the Garbage Classification v2 and RealWaste datasets, define the 10-class material taxonomy mapping, the image normalization pipeline, and the train/val/test splits.

---

## 1. Purpose & Scope

These two datasets feed the **classification** stage of the AI pipeline (deciding *what material* a detected item is). Waste **detection** (locating items in a street scene) uses a separate dataset, TACO, and is out of scope here.

This document records what each dataset contains, how both are mapped into one shared 10-class taxonomy, and how images are cleaned, normalized and split before training.

> **Evidence note:** Counts marked *(README)* come from the dataset's own documentation. Observations marked *(sample review)* come from a manual look at a small sample of images, not the full datasets. Numbers that can only be known by running the pipeline on the full data are marked **TBD — see `report.json`**.

---

## 2. Source Datasets

### 2.1 RealWaste

| Property | Value |
|---|---|
| Origin | Waste received at the Whyte's Gully Waste and Resource Recovery facility, Wollongong NSW, Australia *(README)* |
| Total images | 4,752 *(README — sum of class counts)* |
| Classes (9) | Cardboard 461, Food Organics 411, Glass 420, Metal 790, Miscellaneous Trash 495, Paper 500, Plastic 921, Textile Trash 318, Vegetation 436 *(README)* |
| Layout | One folder per class |
| License | CC BY-NC-SA 4.0 — non-commercial, share-alike, citation required *(README)* |
| Citation | *RealWaste: A Novel Real-Life Data Set for Landfill Waste Classification Using Deep Learning*, Information 14(12):633 *(README)* |

### 2.2 Garbage Classification v2

| Property | Value |
|---|---|
| Classes (10) | battery, biological, cardboard, clothes, glass, metal, paper, plastic, shoes, trash |
| Layout | One folder per class, provided in three versions: `original`, `standardized_256`, `standardized_384` |
| Total images / per-class counts | **TBD — see `report.json`** after running the script |
| License | Check the Kaggle dataset page before redistribution |

---

## 3. Observations (sample review)

**RealWaste (Cardboard sample, 18 images)**
- Single item per image, photographed top-down on a plain grey/white surface — consistent, studio-like background.
- Items are genuinely used and damaged (crushed, torn, stained packaging), which is closer to real litter than product photos.
- Packaging and brands are Australian; shapes of cardboard are broadly universal, but brand artwork is not.
- The same physical item appears several times from different angles (e.g., the same carton and the same freezer-bag box in multiple images).
- Images appeared roughly square and ~500 px wide; exact size distribution **TBD — see `report.json`**.

**Garbage Classification v2 (shoes sample, 18 images)**
- A mix of two very different image types: clean e-commerce product shots (white backgrounds, often small and low-resolution) and real photos of used shoes on indoor floors/carpet.
- Backgrounds are indoor only; no street, sidewalk or soil scenes were seen in the sample.
- Resolution and aspect ratio vary widely between images.

**Implication:** both datasets are useful for learning *material appearance*, but neither contains street scenes or Egyptian waste. The classifier trained on them is a **baseline** and is expected to need fine-tuning on locally collected images (see Section 8).

---

## 4. 10-Class Material Taxonomy Mapping

The unified taxonomy reuses the Garbage Classification v2 class set, since it is the broader of the two.

**Unified classes:** `battery`, `biological`, `cardboard`, `clothes`, `glass`, `metal`, `paper`, `plastic`, `shoes`, `trash`

| RealWaste class | Unified class | Images | Notes |
|---|---|---|---|
| Cardboard | `cardboard` | 461 | Direct match |
| Food Organics | `biological` | 411 | Food waste |
| Vegetation | `biological` | 436 | **Judgment call:** plant matter merged with food waste into one organic class |
| Glass | `glass` | 420 | Direct match |
| Metal | `metal` | 790 | Direct match |
| Paper | `paper` | 500 | Direct match |
| Plastic | `plastic` | 921 | Direct match |
| Miscellaneous Trash | `trash` | 495 | Catch-all; semantics may differ slightly from v2's `trash` |
| Textile Trash | `clothes` | 318 | **Judgment call:** textile waste mapped to `clothes`; may include non-clothing fabric |
| *(none)* | `battery` | 0 | Not in RealWaste — v2 only |
| *(none)* | `shoes` | 0 | Not in RealWaste — v2 only |

Garbage Classification v2 classes map to the unified taxonomy one-to-one (identity mapping).

**RealWaste contribution per unified class** (computed from README counts; total 4,752):
`biological` 847 · `plastic` 921 · `metal` 790 · `trash` 495 · `paper` 500 · `cardboard` 461 · `glass` 420 · `clothes` 318 · `battery` 0 · `shoes` 0

**Known issues with the mapping**
1. `battery` and `shoes` have **no RealWaste images**; those classes depend entirely on v2 (and later on local data).
2. Merging Vegetation into `biological` makes it the largest RealWaste-derived class after plastic; revisit if the operations team needs vegetation reported separately.
3. Class imbalance exists even before merging (Plastic 921 vs. Textile Trash 318). Handle with class weights or balanced sampling at training time, not by deleting data.
4. Label noise: some v2 `shoes` images are product photos rather than discarded items (Section 3).

---

## 5. Image Normalization Pipeline

Applied identically to every image from both datasets, in this order:

1. **Validate** — open and verify each file; skip and log corrupt or unreadable files.
2. **Exact-duplicate removal** — SHA-256 of file bytes; keep the first occurrence, log the rest (also removes cross-dataset duplicates).
3. **Orientation fix** — apply EXIF orientation so rotated phone photos are upright.
4. **Color mode** — convert to 3-channel RGB (handles grayscale/RGBA/palette images).
5. **Resize to a fixed square (default 224×224)** — *pad* mode (default) keeps aspect ratio and fills the border with a neutral colour so items are not distorted; *stretch* mode is available as an option.
6. **Save** as JPEG (quality 95) in `<split>/<class>/` folders.
7. **Training-time normalization (not saved to disk)** — scale pixels to [0, 1] and standardize per channel with ImageNet statistics: mean = [0.485, 0.456, 0.406], std = [0.229, 0.224, 0.225] (matches the ImageNet-pretrained backbones used for transfer learning).

**Training-time augmentation (training split only, applied in the training code):** horizontal flip, small rotations, brightness/contrast/colour jitter, random crop-and-resize. Validation and test images receive no augmentation.

---

## 6. Train / Validation / Test Split Strategy

- **Ratios:** 70% train / 15% validation / 15% test.
- **Stratified per unified class**, so every class appears in every split with the same proportions.
- **Reproducible:** fixed random seed (42); splits are deterministic for the same input.
- **Order of operations:** de-duplicate *before* splitting, so exact copies cannot land in different splits.
- **Provenance:** every image's source dataset, original path, original size and hash are recorded in `manifest.csv`, so results can later be broken down per source dataset.

**Known limitation — near-duplicate leakage:** RealWaste contains multiple photos of the same physical item from different angles (Section 3). Exact-hash deduplication does not catch these, so a random split can place one view of an item in train and another in test, making test accuracy look better than it really is. Mitigation: report this caveat alongside any accuracy figure, and consider a group-aware split (e.g., perceptual-hash clustering) as a follow-up.

---

## 7. Preprocessing Script

`scripts/ai/clean_realwaste.py` implements Sections 4–6.

```bash
pip install pillow
python scripts/ai/clean_realwaste.py \
    --realwaste /path/to/realwaste \
    --garbage-v2 /path/to/garbage-classification-v2/original \
    --out data/processed/classification \
    --size 224
```

**Outputs**
- `data/processed/classification/{train,val,test}/<class>/*.jpg` — cleaned dataset
- `manifest.csv` — one row per image (split, class, source dataset, original path, output path, original size, SHA-256)
- `report.json` — totals, per-class / per-source / per-split counts, original size statistics, corrupt and duplicate files, classes with zero images, and the normalization constants

The script warns when a unified class has no images (e.g., `battery` and `shoes` when run on RealWaste alone).

---

## 8. Limitations & Next Steps

- Neither dataset contains Egyptian street conditions; the classifier is a baseline until fine-tuned on locally collected, labeled images.
- Run the script on the full downloaded datasets and paste the resulting totals from `report.json` into Section 2 and Section 4.
- Resolve the two taxonomy judgment calls (Vegetation → `biological`, Textile Trash → `clothes`) with the team before training.
- RealWaste is licensed non-commercial (CC BY-NC-SA 4.0); confirm this is acceptable for the intended use and include the required citation in the final report.
