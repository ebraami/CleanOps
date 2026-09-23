# Waste Classification Requirements

Define the requirements for the classification model — input (detected object crops), output (material category), model/dataset choice (classifier on Garbage Classification v2, validated against RealWaste), and the target accuracy (≥75% top-1 accuracy).

---

## 1. Input

**Format:** Cropped image regions ("object crops"), not full uploaded photos.

**Pipeline context:**
1. A citizen-submitted street photo is first passed through the detection model (YOLOv8, fine-tuned on the TACO dataset), which locates waste items and outputs bounding boxes.
2. Each detected bounding box is cropped from the original image.
3. Each individual crop is passed as a separate input to the classification model.

**Rationale:** Classifying a cropped, single-object region is more accurate and consistent than classifying an entire street scene at once, since the classification model (trained on single-object datasets) was never designed to handle multiple overlapping items in one frame. This matches how the classification training data (Garbage Classification v2, RealWaste) is itself structured — one item per image.

**Expected input specification:**
- Image format: JPEG/PNG crop, resized to the classifier's expected input resolution (e.g., 224×224, matching standard transfer-learning backbones).
- Each crop corresponds to exactly one detected object.

---

## 2. Output

**Format:** A single predicted material category per input crop, along with a confidence score.

**Category set:** Based on Garbage Classification v2's 10 classes: Metal, Glass, Biological, Paper, Battery, Trash, Cardboard, Shoes, Clothes, Plastic.

**Output structure (example):**
```json
{
  "predicted_category": "Plastic",
  "confidence": 0.91
}
```

- If the model's top confidence score falls below a defined threshold (e.g., 50%), the result is flagged as "low confidence" for operator review rather than presented as a certain classification.

---

## 3. Model / Dataset Choice

**Base model:** A convolutional neural network classifier trained via transfer learning (fine-tuning a pretrained ImageNet backbone), consistent with the approach defined for the project's AI components.

**Training dataset:** [Garbage Classification v2](https://www.kaggle.com/datasets/sumn2u/garbage-classification-v2) — approximately 19,762 images across 10 waste categories. Used as the primary training source since it offers the broadest category coverage among the available public datasets.

**Validation dataset:** [RealWaste](https://www.kaggle.com/datasets/joebeachcapital/realwaste) — 4,752 images captured in an authentic landfill environment across 9 material types. Used specifically to validate (not train) the model, since its images better represent real-world, non-studio conditions (natural lighting, dirtied/used items, cluttered backgrounds) closer to what citizens will submit.

**Why this split:** Training on Garbage Classification v2 gives the model broad category coverage and a large sample size. Validating on RealWaste — a dataset the model never trained on — tests whether the model generalizes to realistic conditions rather than only performing well on clean, studio-style images. This directly addresses the "clean single-object image" limitation noted in the project proposal's dataset section.

---

## 4. Target Accuracy

**Target:** ≥75% top-1 accuracy, measured on the held-out RealWaste validation set.

**Definition of top-1 accuracy:** The percentage of test crops for which the model's single highest-confidence predicted category exactly matches the ground-truth label.

**How it will be tested:**
1. The trained model (fine-tuned on Garbage Classification v2) is run on the full RealWaste dataset (used purely as a held-out validation set, not seen during training).
2. For each image, the model's top-1 predicted category is compared against RealWaste's ground-truth label.
3. Top-1 accuracy = (number of correctly classified images) / (total number of validation images).
4. This figure is reported alongside a confusion matrix to identify which categories the model confuses most often (e.g., Cardboard vs. Paper), so weak categories can be prioritized for additional data or augmentation if the 75% target is not initially met.

**Consistency note:** This 75% top-1 target matches the classification-accuracy success criterion defined in the project proposal (Section 22), ensuring this requirement is aligned with the project's overall evaluation plan rather than introducing a separate, conflicting standard.
