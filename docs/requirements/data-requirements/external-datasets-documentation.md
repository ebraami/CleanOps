# External Datasets Documentation

**Status:** In Progress
**Priority:** Medium

Document the three acquired datasets (TACO, Garbage Classification v2, RealWaste) — their role (detection vs. classification), size, format, and why each was selected over alternatives.

---

## 1. TACO Dataset (YOLO Format)

**Role:** Object Detection

**Source:** [https://www.kaggle.com/datasets/vencerlanz09/taco-dataset-yolo-format](https://www.kaggle.com/datasets/vencerlanz09/taco-dataset-yolo-format)

**Size & Format:**
- 6,004 images
- 18 litter classes (Aluminium foil, Bottle cap, Bottle, Broken glass, Can, Carton, Cigarette, Cup, Lid, Other litter, Other plastic, Paper, Plastic bag - wrapper, Plastic container, Pop tab, Straw, Styrofoam piece, Unlabeled litter)
- YOLOv8 annotation format, pre-split into train/valid/test folders with a `data.yaml` class map
- Images resized to 416x416 during export, with horizontal/vertical flip and 90° rotation augmentations applied

**Relevance to the Pipeline:**
TACO is the closest dataset to real-world deployment conditions among the three, as it was captured in outdoor, real-street environments (sand, asphalt, vegetation) rather than staged studio photos. It provides labeled bounding boxes needed to train the detection stage of the pipeline (locating litter within a full scene), and serves as the primary detection baseline before local Egyptian street images are added for fine-tuning.

**Why selected over alternatives:** Compared to other candidate detection datasets (e.g., generic "Domestic Trash" collections), TACO offers pre-annotated bounding boxes in a ready-to-use YOLO format, removing the need for manual annotation on the full dataset and accelerating the detection-model baseline.

---

## 2. RealWaste

**Role:** Classification (baseline)

**Source:** [https://www.kaggle.com/datasets/joebeachcapital/realwaste](https://www.kaggle.com/datasets/joebeachcapital/realwaste)

**Size & Format:**
- Approx. 4,752 images
- 9 classes: Cardboard, Food Organics, Glass, Metal, Miscellaneous Trash, Paper, Plastic, Textile Trash, Vegetation
- One folder per class; images captured against a consistent facility background

**Relevance to the Pipeline:**
RealWaste images were collected from actual waste received at a real waste-and-resource-recovery facility (Whyte's Gully, Wollongong, Australia), meaning the items are genuinely post-use and often damaged, crushed, or soiled — closer to real litter condition than staged product photography. This makes it a strong classification baseline for teaching the model realistic item appearance, despite its uniform studio-style background.

**Why selected over alternatives:** RealWaste was chosen over purely synthetic or product-catalog datasets because its images reflect authentic waste condition (damaged packaging, mixed materials) rather than clean, unused items — a better foundation for a classifier expected to work on real street waste.

---

## 3. Garbage Classification v2

**Role:** Classification

**Source:** [https://www.kaggle.com/datasets/sumn2u/garbage-classification-v2](https://www.kaggle.com/datasets/sumn2u/garbage-classification-v2)

**Size & Format:**
- 10 classes: battery, biological, cardboard, clothes, glass, metal, paper, plastic, shoes, trash
- Each class provided in three resolutions: original, standardized_256 (256x256), and standardized_384 (384x384)

**Relevance to the Pipeline:**
This dataset extends category coverage beyond RealWaste, adding classes not present there (battery, shoes, clothes, biological waste), which broadens the classifier's ability to recognize a wider range of common street-litter categories relevant to the CleanStreet AI use case.

**Why selected over alternatives:** Chosen for its broader class coverage (10 categories vs. 9 in RealWaste) and for providing multiple pre-standardized resolutions, simplifying preprocessing during model training. Note: a data-quality review found a portion of images in some categories (e.g., "shoes") resemble product/e-commerce photography rather than discarded items; this is documented as a known limitation to be mitigated with locally collected images.

---

> **Note:** All three datasets are used as an initial training baseline. As documented in the project proposal (Section 13, "Important dataset limitation"), locally collected street images from Egypt are still required to fine-tune the model for real deployment conditions, since none of the above datasets contain region-specific imagery.
