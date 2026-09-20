# Citizen Functions — Report Details & Tracking

### CleanStreet AI — Citizen/User Module Functional Specification

**Section scope:** All citizen-facing functions spanning account access (registration, login, session management, password reset) and the full report lifecycle (creation, mandatory evidence, tracking, and resolution confirmation) — the complete Citizen/User Workflow (Section 16.1 / Figure 6) built on the `USERS`, `REPORTS`, `IMAGES`, `CATEGORIES`, and `STATUS_HISTORY` tables (Section 15.2).

---

## Summary Table

| **#FunctionDescriptionAcceptance ConditionSource** |                              |                                                                                                                                                         |                                                                                                                   |                                                                              |
| -------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 1                                                  | **Citizen Registration**     | Allows a new citizen to create an account and access the CleanStreet AI system.                                                                         | A citizen without an account can register successfully and then access the system.                                | Explicit — Scope (Sec. 9), Workflow step 2                                   |
| 2                                                  | **Citizen Login**            | Allows registered citizens to authenticate and access the citizen dashboard.                                                                            | Valid credentials allow access to the application; invalid credentials are rejected.                              | Explicit — Scope (Sec. 9), Workflow step 3                                   |
| 3                                                  | **Session Management**       | Maintains the authenticated citizen's access while using the application and controls access to citizen features.                                       | An authenticated citizen can use protected features, while an unauthenticated user cannot access them.            | Inferred — standard auth requirement, not detailed in workflow/scope         |
| 4                                                  | **Password Reset**           | Allows a citizen who cannot access their account to recover access through the authentication mechanism.                                                | The citizen can complete the reset process and subsequently authenticate with the new password.                   | Inferred — standard auth requirement, not detailed in workflow/scope         |
| 5                                                  | **Create Waste Report**      | Allows citizens to submit a report about accumulated waste, illegal dumping, or an unclean public area.                                                 | A report is successfully created when all required report information is provided and valid.                      | Explicit — Scope (Sec. 9–10), Workflow step 4                                |
| 6                                                  | **Mandatory Image Upload**   | Requires the citizen to provide photographic evidence of the reported waste problem.                                                                    | The system must not allow the report to be submitted without the required image evidence.                         | Explicit — Scope (Sec. 9), Sec. 6 ("Report submission with photo")           |
| 7                                                  | **Capture Location**         | Allows the system to capture the report's GPS/location information so the reported problem can be identified geographically.                            | The report cannot be submitted until valid location information is available.                                     | Explicit — Scope (Sec. 9, "GPS and location capture")                        |
| 8                                                  | **Select Report Category**   | Allows the citizen to specify the category/type of the reported waste or cleanliness problem.                                                           | A valid category is associated with the submitted report and can be viewed later.                                 | Explicit — Scope (Sec. 9, "Report categorisation")                           |
| 9                                                  | **Add Report Description**   | Allows the citizen to provide additional information describing the reported problem.                                                                   | The provided description is stored with the report and displayed when its details are viewed.                     | Explicit — Sec. 6 ("optional description"), `REPORTS.description`            |
| 10                                                 | **Review & Submit Report**   | Allows the citizen to review the image, location, category, and description before submitting the report.                                               | The citizen can review the entered information and submit the report only when the required information is valid. | Explicit — Workflow step 6 ("Review and submit the report")                  |
| 11                                                 | **View Report Details**      | Allows the citizen to view information associated with a previously submitted report, including its image, location, category, description, and status. | Selecting a report displays its stored details correctly.                                                         | Inferred from Sec. 10 ("status viewing... history")                          |
| 12                                                 | **Track Report Status**      | Allows the citizen to follow the progress of a submitted report as it moves through the operational workflow.                                           | The citizen can see the current status and receive updates as the request is processed.                           | Explicit — Scope (Sec. 9, "Status tracking, Notifications"), Workflow step 8 |
| 13                                                 | **View Completion Evidence** | Allows the citizen to view evidence uploaded by the cleaning team after the reported problem has been addressed.                                        | Completion evidence is displayed to the citizen when available.                                                   | Explicit — Scope (Sec. 9, "Completion evidence"), Workflow step 9            |
| 14                                                 | **Confirm Resolution**       | Allows the citizen to confirm that the reported issue has been resolved after reviewing the completion evidence.                                        | The citizen can confirm the resolution after completion evidence is available.                                    | Explicit — Workflow step 9 ("Rate/Confirm Resolution")                       |
| 15                                                 | **Report History**           | Allows the citizen to access previously submitted reports and their current/previous information.                                                       | Previously submitted reports are retrievable by the authenticated citizen.                                        | Explicit — Sec. 10 ("history of previously submitted reports")               |

---

## Why Session Management and Password Reset Are Included Despite Not Being Scoped

The proposal's Section 9 (In Scope) explicitly lists *registration and login*, and Section 10 lists *status viewing, notifications, and report history* as citizen-app features — but it does not separately describe session handling or password recovery as workflow steps, and Figure 6 doesn't show them as distinct boxes.

They are included here anyway for one reason: **login is meaningless without them.** Any authenticated system needs (a) a way to keep a citizen logged in across requests and expire that access safely, and (b) a way to recover access when a password is forgotten — otherwise "Login" (Function 2) is an unfinished feature, not an optional add-on. They are presented as **standard authentication requirements that support the explicitly scoped Login function**, not as features independently drawn from the proposal's workflow diagrams. If asked to justify their inclusion, cite this reasoning rather than a specific proposal section — there isn't one.

---

## Detailed Acceptance Criteria

Each summary row expands into testable conditions below, so "delivered" can be checked function-by-function.

### 1. Citizen Registration

- New citizen registers with name, email/phone, and password; a `USERS` row is created with role `citizen`.
- Registration fails with a clear error if the email/phone is already in use.
- Password must meet a minimum complexity rule; non-conforming input is rejected before account creation.
- On success, the citizen is either logged in directly or routed to login, per the chosen verification flow.
- If email/phone verification is enabled, the account stays "pending" and cannot fully access the system until verified.

### 2. Citizen Login

- Correct credentials grant access to the citizen dashboard.
- Incorrect credentials return one generic error (does not reveal whether the email or password was wrong).
- Repeated failed attempts (e.g., 5) trigger a temporary lockout/throttle with a recovery message.
- Successful login issues a session per Function 3.

### 3. Session Management

- A valid session/token is required for every protected action (creating a report, viewing history, tracking status, viewing completion evidence).
- Requests without a valid session are rejected and redirected to login.
- Sessions expire after a defined inactivity period or absolute lifetime; expiry forces re-authentication.
- Logging out invalidates the session server-side, not just on-device.

### 4. Password Reset

- Citizen requests a reset via registered email/phone; a time-limited, single-use reset link/code is sent.
- The system's response is identical whether or not the account exists, to prevent account enumeration.
- The reset token cannot be reused after being consumed, and expired tokens are rejected with a clear message.
- New password must meet the same complexity rule as registration.
- All existing sessions are invalidated once the reset succeeds, and the citizen can immediately log in with the new password.

### 5. Create Waste Report

- Citizen can start a new report from the dashboard, producing a draft `REPORTS` record.
- Submission requires: category, image, and location as hard prerequisites (Functions 6–8); description is optional (Function 9).
- On successful submission, the report is stored with `current_status = "Submitted"`, a `created_at` timestamp, and a unique id shown to the citizen as a tracking reference.
- The report is queued for AI-assisted analysis (waste detection, classification, severity scoring) without blocking the citizen's confirmation screen.

### 6. Mandatory Image Upload

- Submission is blocked with a specific validation message if no image is attached.
- Citizen can capture via camera or select from gallery; accepted formats are JPEG/PNG with an enforced max file size (e.g., 10 MB).
- Uploaded files are validated as genuine images (not by extension alone) before acceptance.
- On success, the image is stored in Object Storage and linked via an `IMAGES` row (`report_id`, `storage_url`, `image_type = "citizen_submission"`).
- Failed uploads (network/format errors) show a specific error and allow retry without losing other entered fields.

### 7. Capture Location

- The app captures device GPS coordinates automatically when creating a report, or allows manual map-pin placement if GPS is unavailable/denied.
- Submission is blocked if no valid latitude/longitude is available.
- Captured coordinates are stored in `REPORTS.latitude` / `REPORTS.longitude` and are visible on the report detail and (for operators) the map view.
- If location permission is denied, the citizen is shown a clear explanation and a manual-entry fallback rather than a silent failure.

### 8. Select Report Category

- Citizen selects one category from a fixed, predefined list (`CATEGORIES` table, e.g., illegal dumping, overflowing bin, littering, unclean public area).
- Submission is blocked if no category is selected.
- The selected `category_id` is stored on the report and displayed wherever report details are shown.

### 9. Add Report Description

- Citizen may optionally enter free-text description (e.g., up to a defined character limit, such as 500 characters).
- If provided, the description is stored on the `REPORTS` record and shown in report details; if omitted, the field is simply blank (does not block submission).
- Description text is sanitized/escaped to prevent injection when rendered in the operator dashboard.

### 10. Review & Submit Report

- Before final submission, the citizen sees a summary screen showing the image, location (map or address), category, and description together.
- The citizen can go back and edit any field from the review screen before submitting.
- Submit is only enabled once all mandatory fields (image, location, category) are valid; otherwise the button is disabled with an inline explanation of what's missing.
- Successful submission shows a confirmation state ("Report Successfully Submitted") with the tracking id.

### 11. View Report Details

- Selecting any report from history or dashboard opens a detail view showing image, location, category, description, and current status, matching the stored `REPORTS`/`IMAGES` data exactly.
- A citizen can only open the details of their own reports; attempting to access another citizen's report id is rejected (403/not found), not silently redirected.

### 12. Track Report Status

- The report detail view shows the current status (e.g., Submitted → Under Review → Assigned → In Progress → Resolved), sourced from `STATUS_HISTORY`.
- Each status change is timestamped and visible to the citizen in chronological order.
- The citizen optionally receives a push/in-app notification when status changes, without needing to manually refresh.

### 13. View Completion Evidence

- Once the cleaning team uploads completion evidence, a second `IMAGES` row (`image_type = "completion_evidence"`) is linked to the same report.
- The completion evidence becomes visible to the citizen in the report detail view only after the operator marks the relevant step complete.
- If no completion evidence exists yet, the section is hidden or shows a "pending" placeholder rather than a broken/empty state.

### 14. Confirm Resolution

- Once completion evidence is available, the citizen is presented with a confirm/rate action (e.g., "Confirm Resolved" or an optional satisfaction rating).
- Confirming resolution updates the report status accordingly and is recorded with a timestamp.
- Confirmation is optional but available for a limited window after evidence is posted; if the citizen does not respond, the report can still be closed by the operator without being blocked indefinitely on citizen input.

### 15. Report History

- The authenticated citizen can view a list of all reports they have submitted, ordered by most recent first.
- Each history entry shows at minimum: tracking id, category, thumbnail image, current status, and submission date.
- The list supports basic filtering/sorting (e.g., by status) if the UI provides it, and is scoped strictly to the logged-in citizen's own reports.

---

## Cross-Function Notes

**Dependencies:** Functions 6 (image), 7 (location), and 8 (category) are hard gates on Function 10 (Review & Submit) — none of them can be skipped, since image + location are the required inputs to the AI analysis pipeline (waste detection, classification, severity scoring) that runs immediately after submission.

**Citizen vs. operator boundary:** The citizen's role stops at reviewing outcomes — Functions 12–14 (Track Status, View Completion Evidence, Confirm Resolution) are read-and-acknowledge actions. Decisions about priority, team assignment, and whether cleaning was actually done correctly belong to the operator workflow (Figure 7), not the citizen. This spec deliberately does not give the citizen any function that alters report priority, assignment, or operational status beyond confirming resolution.

**Status lifecycle:** Function 12 assumes a defined status set (e.g., Submitted, Under Review, Assigned, In Progress, Resolved) persisted in `STATUS_HISTORY`; this enumeration should be confirmed against the operator workflow (Figure 7) so citizen-visible statuses match what operators actually set.

**Security & privacy tie-in:** Functions 1–4 (account access) and 6–7 (image/location capture) directly implement the protections listed in Section 17 — authentication, access control, and protection of location/image data, since both may contain identifiable people, vehicles, or addresses.

**Workflow mapping:**

| **Function(s)Workflow step (Figure 6)Primary table(s)** |                                                            |                                                |
| ------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------- |
| 1–4                                                     | Steps 1–3: open app, register/login, reach home dashboard  | `USERS`                                        |
| 5–10                                                    | Steps 4–6: create report, provide details, review & submit | `REPORTS`, `IMAGES`, `CATEGORIES`              |
| 11, 15                                                  | Dashboard/report list access                               | `REPORTS`, `IMAGES`                            |
| 12                                                      | Step 8: track report progress, receive notifications       | `STATUS_HISTORY`                               |
| 13–14                                                   | Step 9: view completion evidence, confirm resolution       | `IMAGES` (completion-evidence type), `REPORTS` |

*End of section.*