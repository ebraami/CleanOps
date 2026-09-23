# Completion Evidence Submission — CleanStreet AI

## Purpose

Once a cleaning team finishes work on an assigned report, the system needs proof that the cleanup actually happened before the report can be closed. This document defines exactly how that proof — the "completion evidence" — is captured, submitted, stored, and connected to the rest of the system, so that both the operator and the citizen can trust that a report marked "Resolved" really was resolved.

This is the cleaning-team side of a chain that starts with FR-3.5 (upload completion evidence) and ends with FR-2.19/FR-2.20 (operator approves or rejects it) and FR-1.16 (citizen views it).

---

## 1. Why This Step Exists

Without a required evidence step, a cleaning team could mark a task "done" with nothing to back it up, and there would be no way for an operator — or the citizen who originally reported the problem — to verify the work was actually completed. The proposal's operator workflow (Section 16.2) explicitly includes a branch where the operator can reject unverified work and send it back, and that branch only makes sense if evidence was required in the first place. This submission step is what makes that verification possible.

---

## 2. Full Submission Flow, Step by Step

1. **Team opens the assigned report.** The report must be in an active, assigned state (e.g., "Assigned" or "In Progress") — a report that hasn't been assigned to this team, or one that's already "Resolved," should not accept new completion evidence.
2. **Team captures or selects the after-photo.** This is a photo taken at the cleanup site, showing the area now that the waste has been cleared.
3. **The photo is uploaded to Object Storage**, using the exact same mechanism as the citizen's original report photo (Firebase Storage or S3) — not sent to or stored in the relational database directly.
4. **Object Storage returns a URL** pointing to the newly uploaded file.
5. **The backend creates a new row in the IMAGES table**, populated as follows:
   - `report_id` → the report currently being closed out (attached automatically by the system, never typed in by the team)
   - `storage_url` → the URL just returned by Object Storage
   - `image_type` → set to `after` automatically; this is not a choice the cleaning team makes
   - `uploaded_at` → the current server timestamp
6. **The team is shown a review/confirmation screen** displaying the photo and which report it will be attached to, along with an optional notes field.
7. **The team explicitly confirms submission.** Nothing is sent to the operator until this confirmation happens — this prevents a photo from being half-uploaded or accidentally attached to the wrong report.
8. **On confirmation, the report becomes visible to the operator** with the completion evidence attached and awaiting review, per FR-2.18. The report's status itself does not automatically become "Resolved" at this point — that decision stays with the operator (FR-2.19/FR-2.20).

---

## 3. Required Fields and Rules

| Field | Required? | Rule |
|---|---|---|
| After-photo | **Required** | At least one photo must be attached; submission is blocked without it — the same hard rule the proposal applies to the citizen's original report photo |
| `report_id` | Required (system-attached) | Always inferred from the report the team currently has open; never manually entered, which prevents evidence from being mistakenly attached to the wrong report |
| `image_type` | Required (system-set) | Always set to `after` by the backend; the cleaning team is never presented with a choice here, since a wrong selection would corrupt the before/after distinction the Images Entity Schema depends on |
| Confirmation step | **Required** | The team must explicitly confirm before anything is sent to the operator; this is a deliberate checkpoint, not a formality |
| Notes | Optional | Free-text field for context (e.g., "additional debris found and removed," "access was limited on the north side") — helps the operator's review but does not block submission if left empty |

### Can a team submit more than one after-photo?

Yes. The Images Entity Schema supports multiple images of the same `image_type` per report, so a cleaning team can attach more than one after-photo (e.g., different angles of the same site) in a single submission if that's useful evidence. Nothing in this requirement limits it to exactly one photo — only that at least one is required.

---

## 4. Connection to the Images Entity Schema

This submission step is the concrete event that produces an `after`-type row in the IMAGES table, as defined in the Data Requirements package:

- It does **not** create a new report and does **not** overwrite the citizen's original `before` photo.
- It adds a **second (or additional) image record**, linked to the exact same `report_id`, distinguished purely by `image_type = after`.
- The one-to-many relationship between REPORTS and IMAGES (one report, multiple images) is what makes this possible — a report naturally accumulates a `before` image at submission and one or more `after` images at completion, without needing separate tables or extra columns.

Once this row exists in IMAGES:
- **FR-1.16** (citizen views completion photo) reads this exact record to display the after-photo to the citizen once the report reaches "Resolved."
- **FR-2.18** (operator reviews completion evidence) reads this exact record to show the operator what the team submitted, before deciding to approve or reject it.

In other words, this is a single upload event feeding two different downstream consumers (citizen and operator) — there is only ever one copy of the evidence, referenced from two places.
# Completion Evidence Submission — CleanStreet AI

## Purpose

Once a cleaning team finishes work on an assigned report, the system requires completion evidence before the report can be closed.

This document defines how the cleaning team captures, submits, stores, and associates completion evidence with the existing report. The submitted evidence is then available for operator review and, after resolution, for the citizen to view.

This document covers the cleaning-team side of the process, from uploading the completion evidence to submitting it for operator review.

---

## 1. Why This Step Exists

The system requires evidence of completed cleaning work before an operator can approve the report as resolved.

The completion evidence allows the operator to review the result of the cleaning work and either approve the report or return it to the cleaning team for further action.

Therefore, the cleaning team must provide an after-photo before the completion evidence can be submitted.

---

## 2. Full Submission Flow

### Step 1 — Open the Assigned Report

The cleaning team member opens a report assigned to their team.

The report must be in an active state such as:

* `Assigned`
* `In Progress`

A report that is already `Resolved` must not accept new completion evidence.

---

### Step 2 — Capture or Select the After-Photo

The cleaning team captures or selects an after-photo showing the result of the completed cleaning work.

At least one after-photo is required.

The submission cannot continue without an after-photo.

---

### Step 3 — Upload the Photo

The selected photo is uploaded to Object Storage using the project's configured storage solution, such as:

* Firebase Storage
* Amazon S3

The image file itself is not stored directly inside the relational database.

---

### Step 4 — Receive the Storage Reference

After a successful upload, Object Storage returns a storage reference/URL for the uploaded image.

This value is used as the `storage_url` when creating the corresponding image record.

---

### Step 5 — Create the IMAGES Record

The backend creates a new record in the `IMAGES` table.

The record contains:

| Field         | Value                                       |
| ------------- | ------------------------------------------- |
| `report_id`   | Automatically taken from the current report |
| `storage_url` | Reference returned by Object Storage        |
| `image_type`  | Automatically set to `after`                |
| `uploaded_at` | Current server timestamp                    |

The cleaning team does not manually enter or select these system-managed values.

---

### Step 6 — Review the Evidence

Before submitting the evidence, the system displays a confirmation screen.

The cleaning team member can review:

* The uploaded after-photo
* The report the photo will be attached to
* Optional notes

This allows the team member to verify the evidence before submitting it.

---

### Step 7 — Confirm Submission

The cleaning team member must explicitly confirm the submission.

The system must not send the completion evidence to the operator until confirmation is completed.

This confirmation acts as a checkpoint to prevent accidental or incomplete submissions.

---

### Step 8 — Send for Operator Review

After confirmation, the completion evidence becomes available to the operator for review.

The report does **not** automatically become `Resolved` at this stage.

The operator remains responsible for deciding whether the submitted evidence is sufficient to resolve the report.

---

## 3. Required Fields and Rules

| Field         | Required?                       | Rule                                                                          |
| ------------- | ------------------------------- | ----------------------------------------------------------------------------- |
| After-photo   | **Required**                    | At least one after-photo must be submitted. Submission is blocked without it. |
| `report_id`   | **Required / System-set**       | Automatically obtained from the report currently being handled by the team.   |
| `storage_url` | **Required / System-generated** | Contains the reference to the uploaded image in Object Storage.               |
| `image_type`  | **Required / System-set**       | Automatically set to `after`. The team cannot change it.                      |
| `uploaded_at` | **Required / System-generated** | Automatically recorded using the server timestamp.                            |
| Confirmation  | **Required**                    | The team member must explicitly confirm the submission.                       |
| Notes         | **Optional**                    | Allows the team to provide additional context about the completed work.       |

### Can a Team Submit More Than One After-Photo?

Yes.

A report can contain multiple image records, including multiple images with:

```text
image_type = after
```

This allows the cleaning team to provide multiple views of the completed work when necessary.

At least one after-photo is required, but the requirement does not limit the submission to exactly one photo.

---

## 4. Connection to the Images Entity Schema

The completion evidence process uses the existing **IMAGES Entity Schema** defined in the Data Requirements package.

The submission:

* Does **not** create a new report.
* Does **not** replace the citizen's original photo.
* Adds a new image record linked to the existing `report_id`.
* Identifies the image as an `after` image using `image_type`.

The relationship can be represented as:

```text
REPORT
  │
  │ report_id = R123
  │
  ├── IMAGES
  │     ├── image_type = before
  │     │   └── Citizen's original report photo
  │     │
  │     ├── image_type = after
  │     │   └── Cleaning team's completion photo
  │     │
  │     └── image_type = after
  │         └── Additional completion photo
```

This uses the existing one-to-many relationship between `REPORTS` and `IMAGES`.

No additional table or separate completion-photo schema is required.

---

## 5. Downstream Consumers

Once the after-photo has been successfully submitted, it can be used by different parts of the system.

### Operator Dashboard

The operator uses the submitted completion evidence to review the cleaning result before deciding whether to approve or reject the work.

### Citizen Application

After the report reaches `Resolved`, the citizen can view the completion photo associated with their report.

Both use the same logical image record stored in `IMAGES`; they are simply different consumers of the completion evidence.

---

## 6. Boundary With Other Requirements

This document covers the **cleaning team's submission of completion evidence**.

The following actions belong to other workflow requirements:

### Operator Approval

The operator reviews the submitted evidence and can approve the completed work, resulting in the report becoming `Resolved`.

### Operator Rejection / Rework

If the evidence is not sufficient, the operator can return the report for further action.

The report then becomes available to the cleaning team again, and the team repeats the completion process after the required rework has been completed.

Therefore, this submission flow is reusable and can occur again after a rejected submission.

---

## 7. Final Flow

```text
Assigned / In Progress Report
            ↓
     Open Report
            ↓
 Capture / Select After-Photo
            ↓
       Upload Photo
            ↓
   Store in Object Storage
            ↓
 Create IMAGES Record
 image_type = "after"
            ↓
      Review Evidence
            ↓
    Confirm Submission
            ↓
   Send to Operator Review
            ↓
       Operator Decision
          /       \
         /         \
    Approved       Rejected
       ↓              ↓
   Resolved      Rework Required
       ↓              ↓
 Citizen Views    Team Works Again
 Completion Photo       ↓
                   Submit Again
```

## 8. Summary

Completion Evidence Submission defines how the cleaning team proves that an assigned cleaning task has been completed.

The process requires at least one after-photo, automatically associates the image with the correct `report_id`, sets `image_type = after`, stores the image in Object Storage, and requires explicit confirmation before submission.

The after-photo is stored as an additional `IMAGES` record linked to the existing report. The original citizen photo remains unchanged.

The submitted evidence is then available for operator review. The operator's approval or rejection is handled by the separate operator workflow, while the citizen can view the completion evidence after the report reaches `Resolved`.


## 5. What Happens After Submission (Boundary With Other Requirements)

This document covers only the act of submitting the evidence. What happens next is defined elsewhere and is worth noting so the boundary is clear:

- The **operator's decision** to approve (→ "Resolved," FR-2.19) or reject and return for rework (FR-2.20) is a separate requirement, owned by the Operations Dashboard package.
- If rejected, the report returns to the cleaning team's active list, and the team would go through this same submission flow again once the rework is done — this repeatability is exactly why the flow is defined as a reusable step rather than a one-time action.

---

## 6. Summary

- Completion evidence submission is the mechanism by which a cleaning team proves cleanup work was done.
- It requires at least one after-photo, is always tied to the correct report and marked `image_type = after` automatically, and requires an explicit confirmation step before being sent onward.
- It produces a real row in the IMAGES table, using the same one-to-many structure already defined for before-photos — no schema changes needed, just a second entry per report.
- The evidence, once submitted, is read by both the citizen app and the operator dashboard from that same IMAGES record, while the actual resolve/reject decision remains a separate operator-owned step.
