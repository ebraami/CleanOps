# Operator Functions — Report Management & AI Results

Define the functionality for operator login, report list and map views, filtering, and viewing AI analysis, detected waste/materials, and report categories.

---

## 1. Operator Login

**Description:**
Operators authenticate using a registered email/username and password to access the CleanOps operations dashboard. Only authorized cleaning-team accounts can log in; citizens' accounts are separate and cannot access this dashboard.

**Acceptance Condition:**
- A valid operator successfully logs in and is redirected to the main dashboard.
- Invalid credentials show a clear error message without revealing whether the email or password was incorrect.
- After 3 failed attempts, the account is temporarily locked for a defined period.
- The session persists until the operator logs out or the session expires after a period of inactivity.

---

## 2. Report List View

**Description:**
Operators can view all submitted citizen reports in a list format, showing key information per report: report ID, category, status, priority, submission date/time, and location summary.

**Acceptance Condition:**
- All reports assigned to or visible to the operator load correctly in list form.
- Each report row displays at minimum: ID, category, status, priority level, and timestamp.
- Clicking/tapping a report opens its full detail view (including photo, description, and AI analysis).
- The list updates to reflect new incoming reports without requiring a full page reload (or with a clear manual refresh action).

---

## 3. Map View

**Description:**
Operators can view all reports plotted on an interactive map based on their GPS coordinates, allowing spatial understanding of where waste problems are concentrated.

**Acceptance Condition:**
- Each report appears as a marker on the map at its correct GPS location.
- Markers are visually distinguished by status and/or priority (e.g., color-coded).
- Clicking a marker shows a summary popup (category, priority, status) with an option to open the full report.
- The map supports standard zoom/pan interactions and correctly re-centers or clusters markers in dense areas.

---

## 4. Filtering

**Description:**
Operators can filter the report list and/or map view by category (waste type), status (new/in progress/resolved), priority (high/medium/low), and date range.

**Acceptance Condition:**
- Selecting one or more filters immediately updates the displayed reports (list and map) to match the selected criteria.
- Multiple filters can be applied simultaneously (combined, not exclusive).
- If no reports match the selected filters, a clear "no matching reports" message is shown.
- Filters can be cleared/reset to return to the full unfiltered view.

---

## 5. Viewing AI Analysis (Detected Waste/Materials & Report Categories)

**Description:**
For each report, operators can view the AI-generated analysis results: detected waste items (with bounding boxes on the image where applicable), classified material/category (e.g., plastic, glass, paper), and the model's confidence score. This supports — but does not replace — the operator's own judgment on report validity.

**Acceptance Condition:**
- Each report's detail view displays the AI's detected waste category/categories and confidence score.
- Where object detection is used, the annotated image (with bounding boxes) is viewable by the operator.
- If AI analysis failed or is unavailable for a report, this is clearly indicated (e.g., "Analysis unavailable") rather than showing blank or misleading data.
- Operators are able to manually override or flag incorrect AI classifications if needed.
