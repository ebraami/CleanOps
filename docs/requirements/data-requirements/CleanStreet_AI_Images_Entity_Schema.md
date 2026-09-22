# Images Entity Schema — CleanStreet AI

## Purpose

Every report submitted through CleanStreet AI is built around visual evidence — a citizen's photo of the problem, and later, a cleaning team's photo proving it was resolved. The IMAGES table exists to store references to all of these photos in a structured, queryable way, without mixing image storage into the REPORTS table itself or into the database engine directly.

This document defines the full field-level schema for IMAGES, explains why it is a separate table, and details exactly how it connects to external Object Storage.

---

## 1. Why IMAGES Is a Separate Table (Not a Field on REPORTS)

A naive design might add a single `photo_url` column directly to REPORTS. This does not work for CleanStreet AI because a single report needs to hold **more than one photo, of more than one kind, at different points in its lifecycle**:

- The citizen's original photo, submitted when the report is created (`before`)
- The cleaning team's photo, submitted as proof of work after cleanup (`after`)
- Potentially multiple photos of either type — a citizen might attach more than one angle of the same waste pile, and a cleaning team might document the site from multiple angles as evidence

If images lived as a column on REPORTS, only one image per report could ever be stored, and there would be no way to distinguish a "before" photo from an "after" photo without an awkward workaround (e.g., two separate columns, which breaks down the moment more than one photo of either type is needed).

By making IMAGES its own table with a foreign key back to REPORTS, the relationship becomes **one-to-many**: one report can have any number of associated images, each tagged with its type and upload time.

---

## 2. Field-Level Schema

| Field | Type | Required? | Description |
|---|---|---|---|
| `id` | Integer / UUID (Primary Key) | Required, system-generated | Uniquely identifies each image record. Auto-incremented or generated on insert — never provided by the client. |
| `report_id` | Integer / UUID (Foreign Key → REPORTS.id) | Required | Identifies which report this image belongs to. Every image must be linked to exactly one existing report; an image cannot exist without a parent report. |
| `storage_url` | String (URL / path) | Required | The reference to where the actual image file lives in Object Storage. This is the only piece of image data stored in the relational database — the binary file itself never touches PostgreSQL. |
| `image_type` | Enum: `before` / `after` | Required | Marks whether this image is the citizen's original evidence (`before`) or the cleaning team's completion evidence (`after`). This field is what allows the app and dashboard to display the right photo at the right stage of the report's lifecycle. |
| `uploaded_at` | Datetime | Required, system-generated | Records exactly when the image was uploaded. Used to order multiple images chronologically and to support audit/history views. |

### Notes on each field

- **`id`**: Follows the same primary-key convention as every other table in the schema (see Section 15.2 of the proposal — USERS, REPORTS, etc. all use `id` as PK).
- **`report_id`**: This is a strict foreign key constraint — the database should reject any attempt to insert an image row pointing to a `report_id` that doesn't exist. This guarantees every image is always traceable back to a real report.
- **`storage_url`**: Must be a valid, resolvable URL/path at the time it's written. The backend is responsible for uploading the file to Object Storage *first*, and only writing this field *after* the upload succeeds — never writing a placeholder or an image reference to a file that hasn't finished uploading.
- **`image_type`**: Kept as a fixed enum (not free text) so the application logic can reliably filter and display images by type without needing to parse or guess. If a future version needs more granularity (e.g., multiple stages of "in progress" evidence), this enum can be extended without changing the table structure.
- **`uploaded_at`**: Always set by the server at the moment of successful upload — never provided or editable by the citizen or the cleaning team. This keeps the timestamp trustworthy for audit purposes.

---

## 3. Relationship to Other Tables

```
REPORTS (1) ────< (many) IMAGES
```

- One `REPORTS` row can be linked to **zero or more** `IMAGES` rows at the time of creation (in practice, at least one `before` image is required by the Functional Requirements, so a submitted report will always have at least one).
- As the report moves through its lifecycle and is resolved, additional `IMAGES` rows with `image_type = after` are added by the cleaning team — the original `before` images are never deleted or overwritten.
- This means querying "all images for report X" and filtering by `image_type` is how both the citizen app (to show the after-photo once resolved) and the operator dashboard (to review submitted evidence) retrieve exactly the image they need.

---

## 4. Link to Object Storage

### Why images aren't stored in the database

Image files are large binary objects. Storing them directly inside PostgreSQL would bloat the database, slow down backups, and slow down every query that touches the REPORTS/IMAGES tables even when the image itself isn't needed. Instead, CleanStreet AI follows the standard separation-of-concerns pattern:

- **PostgreSQL + PostGIS** → structured, queryable data (who, what, where, when, status)
- **Object Storage (Firebase Storage or Amazon S3)** → the actual image files

The database only ever holds a *reference* (`storage_url`) to where the file lives — never the file itself.

### How the upload flow works, step by step

1. The citizen (or cleaning team) captures/selects a photo in the app.
2. The app uploads the raw image file to Object Storage (Firebase Storage or S3), not to the backend database directly.
3. Object Storage returns a URL (or storage path/key) pointing to the newly uploaded file.
4. The backend receives this URL and creates a new row in the IMAGES table, setting `report_id`, `storage_url` (the URL just received), `image_type`, and `uploaded_at`.
5. From this point on, any part of the system that needs to display the image (citizen app, operator dashboard, AI service) reads `storage_url` from the IMAGES table and fetches the file directly from Object Storage using that reference — the backend database is never a bottleneck for actual image delivery.

### Why this matters for the AI service specifically

The AI service (waste detection and classification) also follows this same pattern: it reads the `storage_url` of a report's `before` image from the IMAGES table, fetches the image from Object Storage, runs detection/classification on it, and writes its results (severity, priority, category) back into the REPORTS table — not into IMAGES. This keeps IMAGES focused purely on "which photos exist and where," while REPORTS holds the analysis results derived from those photos.

---

## 5. Summary

- IMAGES is a dedicated table, not a column on REPORTS, because a report needs to hold multiple photos of multiple types across its lifecycle.
- Five fields fully describe an image record: `id`, `report_id`, `storage_url`, `image_type`, `uploaded_at`.
- The relationship to REPORTS is one-to-many, enforced by a foreign key.
- The actual image files live in external Object Storage (Firebase Storage or S3); the database only stores the link.
- This separation keeps the relational database fast and keeps image storage independently scalable, while still making every image fully traceable to its parent report and to the stage of the workflow it represents.