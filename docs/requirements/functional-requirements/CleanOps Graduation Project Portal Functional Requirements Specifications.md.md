**CleanOps Graduation Project Portal** **Functional Requirements Specifications**

**Document Title:** Citizen Functions — Report Details & Tracking

**Package:** Functional Requirements

**Filed By:** Meray (Team Member)

**1\. Overview**

This document defines the complete functional specifications for the Citizen Module within the CleanOps platform. It details all requirements covering report location mapping, category selection, detail specification, submission, real-time tracking, push notifications, and completion verification.

**2\. Functional Requirements Breakdown**

**FR-CIT-01: Report Location Mapping**

- **Description:** The system shall allow the citizen to specify the precise geographical location of the issue using an interactive map interface (GPS auto-detection or manual pin placement).
- **Acceptance Criteria:**
    1. The system automatically fetches and displays the user's current GPS coordinates (latitude and longitude) upon user consent.
    2. The user can manually drag and adjust the map pin to select a different target location.
    3. The system converts coordinates into a human-readable address string (Reverse Geocoding).

**FR-CIT-02: Issue Category Selection**

- **Description:** The system shall require the citizen to classify the reported problem into predefined operational categories (e.g., Overflowing Bin, Illegal Dumping, Uncollected Household Waste, Damaged Infrastructure).
- **Acceptance Criteria:**
    1. The interface provides a clear, single-select dropdown or tile-based list of active categories.
    2. Submission is blocked if no category is selected, displaying a validation error message.

**FR-CIT-03: Report Description & Attachment**

- **Description:** The system shall allow the citizen to provide descriptive textual details and upload relevant visual evidence (photos/videos) of the issue.
- **Acceptance Criteria:**
    1. The user can enter a text description up to 500 characters long.
    2. The user can attach up to 3 images (JPEG/PNG format, max 5MB per file) via device camera or gallery upload.
    3. Uploaded media previews must be displayed before submission.

**FR-CIT-04: Report Review & Submission**

- **Description:** The system shall provide a pre-submission review screen displaying all captured report details and process the submission into the system database.
- **Acceptance Criteria:**
    1. A summary card displaying location, category, photos, and description is rendered before final confirmation.
    2. Upon pressing "Submit", the system generates a unique alphanumeric tracking ID (e.g., REP-2026-0089).
    3. Initial report status is set to Pending Review.
    4. The system returns an immediate confirmation dialog to the user upon successful database write.

**FR-CIT-05: Citizen Report History**

- **Description:** The system shall provide a centralized dashboard displaying all current and historical reports created by the authenticated citizen.
- **Acceptance Criteria:**
    1. Reports are listed in reverse chronological order (newest first).
    2. Each list item displays Ticket ID, Category, Submission Date, and Current Status Badge.
    3. Filtering controls are available by status (Pending, In Progress, Resolved, Rejected).

**FR-CIT-06: Real-Time Status Tracking**

- **Description:** The system shall display a detailed timeline/stepper for any selected report showing its lifecycle progression.
- **Acceptance Criteria:**
    1. The UI visualizes status stages: Submitted ➔ Assigned ➔ In Progress ➔ Resolved.
    2. Timestamps and assigned field worker details (if public) are shown for each transition.

**FR-CIT-07: Push & In-App Notifications**

- **Description:** The system shall send automated notifications to the citizen upon key lifecycle events of their submitted reports.
- **Acceptance Criteria:**
    1. Trigger events include: Status Change, Admin Request for Info, and Resolution.
    2. Notifications are delivered via Push Notifications and stored in the user's in-app notification center.

**FR-CIT-08: Completion Verification & Proof**

- **Description:** The system shall display visual proof of resolution uploaded by the cleanup field team once the work is marked completed.
- **Acceptance Criteria:**
    1. The report details view presents a side-by-side "Before & After" photo comparison upon resolution.
    2. Timestamp and resolution notes from the cleanup crew are visible.

**FR-CIT-09: Citizen Resolution Confirmation & Feedback**

- **Description:** The system shall enable the citizen to confirm the satisfactory completion of the report or reopen it if the issue persists.
- **Acceptance Criteria:**
    1. A "Confirm Resolution" and "Reopen Ticket" button are made available for 48 hours following status change to Resolved.
    2. Reopening requires entering a mandatory reason and attaching a new photo.
    3. Confirming allows the citizen to rate the service (1 to 5 stars).
