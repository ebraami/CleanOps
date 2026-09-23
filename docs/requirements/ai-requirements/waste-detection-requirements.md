# Waste Detection Requirements

**Status:** In Progress
**Priority:** Medium

Define the requirements for the waste-detection model — input (submitted image), output (bounding boxes of detected waste objects), model choice (YOLOv8 fine-tuned on TACO), and the target accuracy threshold (mAP@0.5 ≥ 0.5 vs. pretrained-only baseline).

---

## 1. Input

A single image submitted by the citizen through the reporting app at the time of a waste report. The image is accepted in standard formats (JPEG/PNG), consistent with the upload constraints defined in the Citizen Functions requirements (max 5 MB per image).

---

## 2. Output

A set of bounding boxes drawn around each detected waste object in the submitted image. Each bounding box is returned with:
- Object coordinates (x, y, width, height)
- A predicted class label (e.g., Bottle, Plastic bag, Cardboard)
- A confidence score (0–1) indicating the model's certainty in that detection

---

## 3. Model Choice

**YOLOv8**, pretrained on the COCO dataset, fine-tuned on the **TACO dataset** (6,004 real-world street-litter images across 18 classes).

Transfer learning is used instead of training from scratch: the early layers (general shape/edge recognition) are kept frozen, while the final detection layers are retrained on litter-specific classes. This baseline model will later be further fine-tuned on locally collected Egyptian street images to close the domain gap identified in the dataset review (see External Datasets Documentation).

---

## 4. Target Accuracy & Testing Method

**Target:** mAP@0.5 (mean Average Precision at 0.5 IoU threshold) of at least **0.5**.

**How it will be tested:** The fine-tuned model's mAP@0.5 is measured on a held-out test split of the TACO dataset and compared against a pretrained-only baseline (YOLOv8 with no fine-tuning) evaluated on the same test split. The fine-tuned model must outperform this baseline and reach the 0.5 threshold to be considered successful at this stage.

---

> **Note:** The 0.5 mAP@0.5 target and dataset choice are as stated in the project proposal (Sections 12 and 22). Performance will be re-evaluated after incorporating locally collected images, and the threshold may be revisited based on those results.
