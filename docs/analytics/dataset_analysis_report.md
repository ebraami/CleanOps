# CleanOps Waste Dataset Analysis Report

## 1. Objective
Audit the TACO waste dataset, assess annotation integrity,
summarize category distribution, and map the original categories
to the five CleanOps core classes.

## 2. Dataset Overview
- Total images listed in annotations: 1500
- Total annotations / bounding boxes: 4784
- Original TACO categories: 60
- Images found on disk: 1500
- Missing images: 0
- Exact duplicate image groups detected by SHA-256: 0
- Invalid image references: 0
- Invalid category references: 0
- Annotations missing bounding boxes: 0

## 3. CleanOps Core Class Distribution

| CleanOps Class | Bounding Box Count | Percentage |
|---|---:|---:|
| Plastic | 2063 | 43.12% |
| Paper/Cardboard | 492 | 10.28% |
| Glass | 254 | 5.31% |
| Metal | 552 | 11.54% |
| Organic/Trash | 1423 | 29.74% |
| **Total** | **4784** | **100.00% (rounded)** |

Percentages are calculated using the total annotation count.
Individual rounded percentages may not sum to exactly 100%.

![CleanOps core class distribution](figures/waste_categories_barchart.png)

## 4. Top 20 Original Categories

| TACO Category | Annotation Count |
|---|---:|
| Cigarette | 667 |
| Unlabeled litter | 517 |
| Plastic film | 451 |
| Clear plastic bottle | 285 |
| Other plastic | 273 |
| Other plastic wrapper | 260 |
| Drink can | 229 |
| Plastic bottle cap | 209 |
| Plastic straw | 157 |
| Broken glass | 138 |
| Styrofoam piece | 112 |
| Glass bottle | 104 |
| Disposable plastic cup | 104 |
| Pop tab | 99 |
| Other carton | 93 |
| Normal paper | 82 |
| Metal bottle cap | 80 |
| Plastic lid | 77 |
| Paper cup | 67 |
| Corrugated carton | 64 |

## 5. Duplicate and Augmentation Checks
All 1500 image files were found on disk.
A SHA-256 exact-file comparison found no exact duplicate groups.
This check does not detect visually similar images, resized or
re-encoded copies, or augmented versions. Those require a separate
perceptual-image comparison and review.

## 6. Mapping Method and Limitations
The 60 original TACO categories were assigned to five CleanOps
classes using name-based keyword rules. The mapping is a preliminary
rule-based mapping, not a verified material classification model.

Categories such as Cigarette, Unlabeled litter, Shoe, Rope & strings,
and Food waste were assigned to Organic/Trash by the current fallback
rule. These assignments should be reviewed and documented with the
project team before the mapping is treated as final.

## 7. Data Quality Findings
- All listed images were found on disk.
- All annotations reference valid image and category IDs.
- No annotations were missing bounding boxes.
- Exact duplicate groups were not detected by SHA-256.

## 8. Recommendations
1. Review and approve the mapping rules with the CleanOps team.
2. Decide how ambiguous or mixed-material items should be classified.
3. Run a perceptual similarity check to investigate near-duplicates.
4. Inspect image samples from each core class to validate the mapping.
5. Keep the original TACO category alongside the mapped CleanOps class
   to preserve traceability.

## 9. Reproducibility
The analysis should be reproducible by running all notebook cells
in order with the TACO annotations and image batches available.
