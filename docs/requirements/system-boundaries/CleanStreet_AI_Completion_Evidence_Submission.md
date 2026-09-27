# Completion Evidence Submission — CleanStreet AI (Rev. 2)

## Revision Notes (this version)

1. Removed the duplicate content — this is now a single, unified document with FR references restored throughout.
2. The IMAGES row is now created at confirmation (Step 6), not at upload — in the same transaction as the status change and the STATUS_HISTORY entry.
3. Added Section 3, "Report Status After Submission," defining the post-submission state, the STATUS_HISTORY entry, and how `ASSIGNMENTS.completed_at` is handled on approval vs. rejection.
4. Removed the optional Notes field — there is no column for it in the current IMAGES schema, and adding one is outside this document's scope. If the team decides notes are needed, that should go through the Images Entity Schema change request, not be assumed here.
5. Clarified which after-photo the citizen sees following a rejection-and-resubmission cycle (Section 4).
6. Added an explicit backend authorization check: the submitting user must belong to the team in `ASSIGNMENTS.team_id` for that report (Step 1).

This document does not assume the IMAGES schema addendum (`uploaded_by`, `confirmed_at`, submission link) has been adopted yet — where this doc depends on it, that dependency is flagged explicitly rather than assumed.

---

## Purpose

Once a cleaning team finishes work on an assigned report, the system needs proof that the cleanup actually happened before the report can be closed. This document defines exactly how that proof — the "completion evidence" — is captured, submitted, stored, and connected to the rest of the system, so that both the operator and the citizen can trust that a report marked "Resolved" really was resolved.

This is the cleaning-team side of a chain that starts with FR-3.5 (upload completion evidence) and ends with FR-2.19/FR-2.20 (operator approves or rejects it) and FR-1.16 (citizen views it).

---

## 1. Why This Step Exists

Without a required evidence step, a cleaning team could mark a task "done" with nothing to back it up, and there would be no way for an operator — or the citizen who originally reported the problem — to verify the work was actually completed. The proposal's operator workflow (Section 16.2) explicitly includes a branch where the operator can reject unverified work and send it back, and that branch only makes sense if evidence was required in the first place.

---

## 2. Full Submission Flow, Step by Step

**Step 1 — Open the assigned report (with authorization check).**
Before anything else, the backend verifies that the requesting user's team matches `ASSIGNMENTS.team_id` for this report. A team member cannot open, upload to, or submit evidence for a report their team is not assigned to — this request is rejected outright if the check fails.
The report must also be in an active state ("Assigned" or "In Progress"); a report already past submission or already "Resolved" must not accept new completion evidence.

**Step 2 — Capture or select the after-photo.**
This is a photo taken at the cleanup site, showing the area now that the waste has been cleared. At least one after-photo is required — the flow cannot proceed to review without it.

**Step 3 — Upload the photo to Object Storage.**
The photo is uploaded via the app using a signed URL, and the backend verifies the file actually exists in Object Storage before allowing the flow to continue. No IMAGES row is created at this point — only the file itself exists in storage so far.

**Step 4 — Review the evidence.**
The system shows a confirmation screen with the uploaded photo(s) and the report they'll be attached to. No notes field is presented — the requirement does not currently define a storage location for team notes.

**Step 5 — Confirm submission.**
The team member explicitly confirms. Nothing happens in the database until this point — Steps 3–4 only involve the file and the review UI, never a database write.

**Step 6 — Atomic transaction on confirmation.**
On confirmation, the backend performs the following as a single transaction — either all of it succeeds, or none of it does:
- Creates the IMAGES row(s) for each confirmed after-photo: `report_id`, `storage_url` (from Step 3), `image_type = after`, `uploaded_at`.
- Updates the report's status (see Section 3 below).
- Inserts a new STATUS_HISTORY row recording this transition.
- Sets `ASSIGNMENTS.completed_at` to the confirmation timestamp.

**Step 7 — Operator review.**
The report becomes visible to the operator with the completion evidence attached, awaiting a decision (FR-2.18). See Section 3 for what happens next on approval or rejection.

---

## 3. Report Status After Submission

Confirming completion evidence does **not** immediately move the report to "Resolved" — that decision still belongs to the operator (FR-2.19/FR-2.20). Instead, the transaction in Step 6 moves the report into a distinct **awaiting-review** state, referred to here as **"Awaiting Review"** — the exact label is pending the team's unified status-list decision; this document assumes one value exists in that list for this purpose and should be updated to match once finalized.

**On operator approval (FR-2.19):**
- Report status changes from "Awaiting Review" to "Resolved."
- A new STATUS_HISTORY row records this transition.
- `ASSIGNMENTS.completed_at` (already set in Step 6) is left as-is — it now correctly reflects when the accepted work was finished.

**On operator rejection (FR-2.20):**
- Report status changes from "Awaiting Review" back to "In Progress" (rework required).
- A new STATUS_HISTORY row records this transition.
- `ASSIGNMENTS.completed_at` is cleared (reset to null) — the assignment is not actually complete, so this field should not hold a stale timestamp from the rejected attempt.
- The team resubmits by repeating Steps 2–6 in full, including a fresh confirmation transaction.

---

## 4. Which After-Photo the Citizen Sees

A report can end up with more than one `after`-type image if a submission was rejected and resubmitted. Once the report reaches "Resolved," the citizen (FR-1.16) is shown the after-photo(s) from the **submission that was actually approved** — i.e., the most recent confirmed submission, not any earlier rejected attempt.

- If the IMAGES schema addendum's `confirmed_at` field has been adopted, this is simply the image row(s) with the latest `confirmed_at`.
- Until that addendum is adopted, the interim rule is: the image row(s) with the latest `uploaded_at` among those tied to the submission that led to "Resolved."

Earlier, rejected after-photos remain in IMAGES for audit purposes but are not surfaced to the citizen.

---

## 5. Required Fields and Rules

| Field | Required? | Rule |
|---|---|---|
| After-photo | **Required** | At least one photo must be provided; the flow cannot reach confirmation without it |
| `report_id` | Required (system-set) | Inferred from the report currently open; never manually entered |
| `storage_url` | Required (system-generated) | Obtained from Object Storage at upload (Step 3), written to IMAGES only at confirmation (Step 6) |
| `image_type` | Required (system-set) | Always `after`; not a choice presented to the team |
| `uploaded_at` | Required (system-generated) | Server timestamp, set when the IMAGES row is created in Step 6 |
| Confirmation | **Required** | The team must explicitly confirm before the transaction in Step 6 runs |
| Team authorization | **Required (backend check)** | Requesting user's team must match `ASSIGNMENTS.team_id` for the report, checked before Step 1 proceeds |

Notes are not included as a field in this version — see Revision Notes, item 4.

### Can a team submit more than one after-photo?

Yes. The Images Entity Schema supports multiple images of the same `image_type` per report, so a team can attach more than one after-photo in a single submission. The requirement is "at least one," not "exactly one."

---

## 6. Connection to the Images Entity Schema

This submission step produces `after`-type row(s) in the IMAGES table, written at confirmation (Step 6), not at upload. It does **not** create a new report and does **not** overwrite the citizen's original `before` photo — it adds additional image record(s) linked to the same `report_id`, distinguished by `image_type`.

```
REPORT (report_id = R123)
  │
  ├── IMAGES
  │     ├── image_type = before   → citizen's original report photo
  │     ├── image_type = after    → rejected submission (kept for audit, not shown to citizen)
  │     └── image_type = after    → approved submission (shown to citizen once Resolved)
```

This relies on the existing one-to-many relationship between REPORTS and IMAGES. Fields beyond the current schema (`uploaded_by`, `confirmed_at`, a submission/assignment link) are covered by the separate Images Entity Schema addendum and are not assumed here except where explicitly flagged in Section 4.

---

## 7. Boundary With Other Requirements

- **Operator approval/rejection** (FR-2.19/FR-2.20) is owned by the Operations Dashboard package; this document only covers what happens up to and including the transaction in Step 6.
- Rejection triggers a full repeat of Steps 2–6 by the cleaning team — this is why the flow is defined as a reusable step, not a one-time action.

---

## 8. Full Flow (Reference Diagram)

```
Assigned / In Progress Report
            ↓
  Verify team_id matches ASSIGNMENTS
            ↓
       Open Report
            ↓
 Capture / Select After-Photo
            ↓
  Upload Photo to Object Storage
    (backend verifies file exists)
            ↓
      Review Evidence
            ↓
    Confirm Submission
            ↓
 ── Transaction (Step 6) ──────────────
 │ Create IMAGES row(s)               │
 │ Status → "Awaiting Review"         │
 │ STATUS_HISTORY row inserted        │
 │ ASSIGNMENTS.completed_at set       │
 ────────────────────────────────────
            ↓
   Send to Operator Review
            ↓
      Operator Decision
        /            \
   Approved        Rejected
      ↓                ↓
  Resolved      "In Progress"
  completed_at    completed_at
  unchanged        cleared (null)
      ↓                ↓
Citizen Views    Team Resubmits
Approved Photo    (Steps 2–6 repeat)
```

---

## 9. Summary

- Completion evidence submission is the mechanism by which a cleaning team proves cleanup work was done.
- The IMAGES row, the report's status change, the STATUS_HISTORY entry, and `ASSIGNMENTS.completed_at` are all written together in one transaction, triggered only at confirmation — never earlier.
- Submission moves the report to an awaiting-review state, not directly to "Resolved"; the operator's decision determines whether it becomes "Resolved" or returns to "In Progress" with `completed_at` cleared.
- The citizen sees the after-photo from the approved submission only; rejected attempts remain in IMAGES for audit but are not surfaced.
- A backend check ensures only a member of the assigned team can submit evidence for a given report.