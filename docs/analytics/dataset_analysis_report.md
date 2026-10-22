# CleanOps — Waste Dataset Audit, Category Analysis & Explanation Report

**Dataset:** TACO (Trash Annotations in Context)  
**Analysis basis:** supplied `annotations.json`  
**Status:** Metadata and category analysis completed; local-image duplicate/augmentation audit pending until image files are available.

## 1. Executive summary

The supplied annotation JSON contains **1,500 image records**, **4,784 object annotations**, and **60 source categories**. The source taxonomy therefore contains 60 categories in this file, rather than the 18 mentioned in the task overview. The analysis maps every category name found in this JSON to one of the five CleanOps core classes using an explicit mapping in the notebook.

The supplied JSON metadata is internally referentially consistent for image and category IDs: **0 annotations** reference an unknown image ID and **0 annotations** reference an unknown category ID. All 1,500 image records have at least one annotation. **4,784 annotations** have a valid four-value, positive-width/positive-height bounding box; **0** do not pass that validation.

> **Important limitation:** these figures are derived from JSON metadata only. Actual image files have not yet been inventoried, so exact duplicate and perceptual-similarity checks are **not reported as completed**. Do not interpret missing image files as zero duplicates.

## 2. Scope and method

The Jupyter Notebook (`data/notebooks/cleanops_waste_analysis.ipynb`) performs these checks:

1. Loads the TACO annotation JSON from documented candidate paths.
2. Counts image records, object annotations, and source categories.
3. Validates image/category references and bounding-box shape and dimensions.
4. Maps source categories into the five CleanOps classes, failing loudly if a source category is unmapped.
5. Produces the required bar chart of annotation counts by CleanOps class.
6. Searches the configured local image root for image files. When files are available, it computes SHA-256 hashes for exact duplicates and optionally perceptual hashes when `Pillow` and `ImageHash` are installed.
7. Writes a machine-readable summary to `docs/analytics/dataset_analysis_summary.json`.

## 3. CleanOps class distribution

Counts below represent **object annotations**, not unique images. One image may contain multiple annotated objects.

| CleanOps core class | Annotation count |
|---|---:|
| Plastic | 2,252 |
| Paper/Cardboard | 498 |
| Glass | 254 |
| Metal | 550 |
| Organic/Trash | 1,230 |

**Total mapped annotations:** 4,784 (expected 4,784).

The chart is saved at [`docs/analytics/figures/waste_categories_barchart.png`](figures/waste_categories_barchart.png).

## 4. Source category mapping rules

The full, exhaustive mapping is maintained in the notebook. The high-level rules are:

- **Plastic:** plastic bottles, caps, cups, bags, films, wrappers, containers, utensils, straws, and Styrofoam.
- **Paper/Cardboard:** paper, paper bags and straws, cartons, cardboard packaging, tissues, and paper cups.
- **Glass:** glass bottles, jars, cups, and broken glass.
- **Metal:** cans, aerosol containers, metal lids/caps, aluminium packaging/foil, pop tabs, and scrap metal.
- **Organic/Trash:** food waste and residual/ambiguous litter classes such as cigarette, unlabeled litter, shoe, rope/string, and battery.

**Classification caveat:** the required five-class taxonomy has no dedicated battery/e-waste or hazardous-waste class. The notebook assigns `Battery` to the broad `Organic/Trash` operational bucket only to ensure exhaustive mapping; this is not a claim that batteries are organic or safe for ordinary disposal. The project team should approve a safer dedicated handling rule if downstream routing or model training depends on this label. `Carded blister pack`, `Aluminium blister pack`, and composite/plastified packaging are also material-ambiguous and should be reviewed against CleanOps business rules.

## 5. Duplicate and augmentation audit

**Current status: NOT RUN against image files.**

The JSON and `all_image_urls.csv` provide metadata/URLs, but neither alone proves which image files are present locally or whether two image files have identical/similar pixels. To complete this part:

1. Download the actual TACO images into the repository (for example under `TACO/data/`, preserving the `file_name` subfolders where possible).
2. Open the notebook and set `IMAGE_ROOT` to the directory containing the downloaded images if it is not found automatically.
3. Run all notebook cells. SHA-256 grouping detects byte-identical files. The optional perceptual-hash pass can flag visually similar files despite resizing/re-encoding, but these are only *potential* duplicates and need review. Augmentation cannot be reliably inferred from hashes alone without source/lineage metadata or visual review.

If the notebook finds no local image files, it will explicitly show `NOT RUN — no local image files found`; it will not claim that there are no duplicates.

## 6. Data quality observations

- The source JSON contains **60 categories**, so the six example labels in the task description are examples, not a complete mapping table.
- `Unlabeled litter` and `Cigarette` are among the most frequent individual source categories, making consistent residual-waste rules important.
- Class distribution is annotation-based. It should not be described as the percentage of images containing a class unless the analysis is separately grouped by unique `image_id`.
- The mapping is an explicit operational interpretation of the five required CleanOps classes; confirm ambiguous and composite materials with the project lead before treating it as a production labeling standard.

## 7. Recommendations for Menna and Katrin

1. **Taxonomy review:** approve the explicit 60-to-5 mapping, especially batteries, composite packaging, shoes, rope/string, and unlabeled litter.
2. **Image integrity:** make image files available and rerun the notebook to record exact and potential perceptual duplicate groups.
3. **Training-data quality:** review duplicate clusters and visually ambiguous categories before training or evaluating a model.
4. **Operational reporting:** keep annotation counts separate from unique-image counts and report the denominator for every percentage.
5. **Reproducibility:** rerun the notebook from the repository root and commit the notebook, report, chart, and generated summary together.

## 8. Reproducibility and deliverables

Required deliverables:

- `data/notebooks/cleanops_waste_analysis.ipynb`
- `docs/analytics/dataset_analysis_report.md`
- `docs/analytics/figures/waste_categories_barchart.png`

Additional generated output:

- `docs/analytics/dataset_analysis_summary.json`

Run the notebook with **Run All Cells** from the repository root. The notebook requires `pandas` and `matplotlib`; `Pillow` and `ImageHash` are optional for perceptual duplicate checks. The image-level audit is complete only after actual images are present and the notebook records a completed audit status.
