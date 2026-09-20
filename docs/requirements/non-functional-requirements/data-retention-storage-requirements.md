# Data Retention & Storage Requirements

**Status:** In Progress
**Priority:** Medium

Define retention timing for stored data and storage limits for images (max photo size, deletion period).

---

## 1. Data Retention Period

**Description:**
The system retains report data and associated images for a defined period after a report is marked as resolved, allowing time for review, dispute handling, or quality auditing, after which the data is automatically deleted to protect user privacy and reduce storage load.

**Acceptance Condition:**
- Reports with status **"Resolved"** are retained for **90 days** after the resolution date. After this period, the report's images are automatically and permanently deleted from storage.
- Reports with status **"Open"** or **"In Progress"** are retained indefinitely until resolved (no automatic deletion).
- Core report metadata (category, location, timestamps, resolution status) may be retained beyond the 90-day image deletion period for analytics purposes, but without the associated photographic evidence.

---

## 2. Image Storage Limits

**Description:**
The system enforces a maximum file size for images uploaded by citizens and cleaning teams, ensuring efficient storage usage and consistent upload performance without compromising image clarity.

**Acceptance Condition:**
- The maximum accepted size per uploaded image is **5 MB**.
- Images exceeding this limit are automatically compressed client-side (or server-side) before being stored, without requiring the user to resize manually.
- If compression cannot bring the image below the 5 MB limit, the upload is rejected with a clear error message to the user.

---

> **Note:** The numeric thresholds above (90-day retention, 5 MB image limit) are initial working assumptions based on common practice for similar citizen-reporting systems, and can be adjusted based on actual storage costs and operational needs after launch.
