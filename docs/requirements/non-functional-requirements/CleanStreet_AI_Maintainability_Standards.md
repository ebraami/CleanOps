# Maintainability Standards — CleanStreet AI

This document defines the code and documentation standards all sub-teams (Mobile, Backend, AI, Dashboard) must follow so the codebase stays consistent, readable, and easy to hand off between team members.

---

## 1. Module Separation

**Mobile (Flutter):**
- Organize by feature, not by type: `lib/features/reporting/`, `lib/features/tracking/`, `lib/features/auth/` — each feature folder contains its own screens, widgets, and state management.
- Shared code (API client, models, theming, utilities) lives in `lib/core/` or `lib/shared/`, not duplicated per feature.
- No feature module directly imports another feature's internal files — cross-feature communication goes through shared services/models only.

**Backend (REST API):**
- Separate modules per domain: `auth`, `reports`, `assignments`, `teams`, `analytics`. Each owns its own routes, models, and business logic.
- No domain module contains another domain's business logic (e.g., assignment logic does not live inside the reports module).
- Shared logic (DB connection, auth middleware, validation helpers) lives in a common/shared layer.

**AI Service:**
- Detection, classification, and scoring are separate, independently callable components — not one monolithic script — matching the detect-then-classify pipeline design.
- Each model/component has its own input/output contract, independent of how the backend calls it.

**Dashboard:**
- Organized by view/feature: reports list, map view, analytics, team management — each as its own module, sharing a common API client and UI component library.

---

## 2. API Versioning Approach

- All backend endpoints are prefixed with a version: `/api/v1/...`.
- A breaking change (removing/renaming a field, changing a response shape) requires a new version (`/api/v2/...`) — never an in-place change to `v1`.
- Non-breaking changes (adding an optional field) can be added to the existing version without bumping it.
- Every endpoint change is documented with what changed and which version it applies to, so Mobile and Dashboard teams know when they need to update their integration.

---

## 3. Naming Conventions

**Dart / Flutter:**
- `lowerCamelCase` for variables and functions
- `PascalCase` for classes and widgets
- `snake_case` for file names (e.g., `report_status_screen.dart`)

**Backend:**
- `snake_case` for database columns and table names (matching the existing schema: `report_id`, `created_at`)
- `camelCase` for JSON field names in API requests/responses
- `PascalCase` for class/model names

**AI Service (Python):**
- `snake_case` for variables, functions, and file names
- `PascalCase` for class names
- Model files named by task and version (e.g., `waste_detector_v1.pt`)

**Database:**
- Table names plural, lowercase (`reports`, `images`, `assignments`) — matching the existing ER diagram
- Foreign keys named `<entity>_id` (e.g., `report_id`, `team_id`)

---

## 4. Documentation Requirements

**Every API endpoint must document:**
- HTTP method and path
- Required/optional request fields
- Example request and response
- Possible error responses

**Every AI model/component must document:**
- Input shape (e.g., image size, format)
- Output shape (e.g., bounding boxes, class labels, confidence scores)
- Dataset(s) used for training/validation
- Current performance metric (e.g., mAP, accuracy) against the Section 23 target

**Every database table must document:**
- Purpose (one line)
- Key columns and their meaning
- Relationships to other tables

**Every Flutter feature module must document:**
- What screens/flows it covers
- Which shared services/models it depends on

**General rule:** documentation lives next to the code it describes (README per module or inline docstrings/comments), not in a separate untracked file that goes stale.

---

*This document is a shared reference — all sub-teams check new code against it before merging, and any proposed change to these standards should be raised with the whole team rather than changed unilaterally.*
