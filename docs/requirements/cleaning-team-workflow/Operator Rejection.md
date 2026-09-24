**Operator Rejection / Rework Handling — CleanStreet AI**

**Purpose**

Not every completion-evidence submission will satisfy the operator on the first try. The proposal's operator workflow (Section 16.2) explicitly includes a branch where the operator can decline to mark a report "Resolved" and instead send it back for further action. This document defines that branch entirely from the _cleaning team's side_ — how a returned report reappears, what tells the team it needs rework, and exactly how they resubmit — completing the loop described in FR-3.7 ("handle work returned by an operator for further action").

This document assumes the Completion Evidence Submission requirement (Rev. 2) as its baseline: the same atomic transaction, the same "Awaiting Review" placeholder status, and the same IMAGES/STATUS\_HISTORY/ASSIGNMENTS behavior defined there.

**1\. Why This Loop Exists**

The whole point of requiring completion evidence (rather than letting a team self-report "done") is that an operator gets a real chance to verify the work before the citizen is told their problem is solved. If the evidence doesn't hold up — the area still looks uncleaned, the wrong location was documented, the photo is unclear — the system needs a way to send that work back without losing the report, without corrupting the audit trail, and without leaving the citizen or the team stuck in an ambiguous state. That's what this rejection/rework loop is for.

**2\. How the Returned Report Reappears**

When an operator rejects a submission (FR-2.20), the backend performs the following as a single transaction, mirroring the structure already defined for the approval path in the Completion Evidence Submission document:

The report's status changes from _"Awaiting Review"_ back to _"In Progress."_ ASSIGNMENTS.completed\_at — which was set the moment the team originally confirmed their submission — is _cleared (reset to null)_. This matters: if it were left in place, the record would falsely suggest the assignment was completed at that timestamp, when in fact the operator determined it wasn't. A new _STATUS\_HISTORY_ row is inserted recording this exact transition ("Awaiting Review" → "In Progress"), so the full history of the report — including this rejection — remains auditable.

Because the report's status is simply "In Progress" again, _no separate "rejected" queue or list is needed._ The report reappears in the exact same active-task list the cleaning team already uses for newly assigned work (the same list behind FR-3.1). This is a deliberate simplification: the team doesn't need to learn or check a second screen — a returned report and a fresh assignment both show up in the same place, because as far as the team's day-to-day view is concerned, both represent "work that still needs doing."

**3\. What Indicates It Needs Rework**

A returned report needs to look different to the team from a brand-new assignment — otherwise they can't tell the two apart, and any context from the rejection is lost. Three signals combine to make this clear:

_a) Prior submission history._ The team (or the app on their behalf) can check whether the report already has any after-type rows in IMAGES. A first-time assignment has none; a returned report has at least one — the rejected attempt. This is a reliable, data-backed way to distinguish "new work" from "rework," without needing a dedicated boolean flag.

_b) A notification specific to the rejection._ FR-3.6 already covers notifying the team when a report is newly assigned. This document extends that same notification mechanism to also fire on rejection — the team should not have to notice the status change by chance; they should be told directly, the same way they're told about a new assignment.

_c) A rejection reason, where available._ If the Operations Dashboard package captures a reason when the operator rejects a submission (e.g., a short note like "photo doesn't show the reported location" or "area still visibly dirty"), that reason should be surfaced to the team alongside the returned report — it tells them exactly what to fix instead of leaving them to guess.

_Important scope note:_ whether a rejection-reason field currently exists is owned by the Operations Dashboard requirements, not this document. If it doesn't exist yet, that's flagged here as a gap worth raising with whoever owns that package — this document does not assume a field that hasn't been confirmed.

**4\. How They Resubmit (FR-3.7)**

There is _no separate "resubmit" flow._ This is a deliberate design choice: rather than building and maintaining a second submission process just for rework, the team goes through the _exact same Completion Evidence Submission steps_ as a first-time submission:

Capture or select a new after-photo. Upload it to Object Storage (backend verifies the file exists). Review the new evidence on the confirmation screen. Confirm — which triggers the same atomic transaction as before:

- A new IMAGES row is created (report\_id, storage\_url, image\_type = after, uploaded\_at).
- The report's status moves from "In Progress" to "Awaiting Review" again.
- A new STATUS\_HISTORY row is inserted.
- ASSIGNMENTS.completed\_at is set again, to this new confirmation time.

Reusing the identical flow keeps the system simple: the team only ever needs to know one way to submit evidence, whether it's their first attempt or their third.

**What happens to the earlier, rejected photo?**

It is _not deleted._ The earlier after-type IMAGES row from the rejected attempt stays in the database permanently, preserving a complete audit trail of every attempt made on the report. However, per the Completion Evidence Submission document (Section 4), only the photo from the _approved_ submission is ever shown to the citizen once the report reaches "Resolved" — the citizen never sees a rejected attempt, only the one that ultimately succeeded.

**5\. Loop Termination**

The rejection → rework → resubmission cycle can repeat any number of times. Each cycle: Produces a new IMAGES row (rejected attempts accumulate; none are overwritten or removed). Produces two new STATUS\_HISTORY rows per cycle (one for entering "Awaiting Review," one for either "Resolved" or the next rejection back to "In Progress"). Ends only when the operator approves a submission, at which point the report moves to "Resolved" and permanently exits this loop.

_Open question, explicitly out of scope here:_ nothing in this requirement caps how many times a report can be rejected before some other action is taken (e.g., escalation to a supervisor after a certain number of rejections). That is an operator-workflow policy decision, not a cleaning-team requirement, and should be raised with whoever owns the Operations Dashboard package if the team wants such a limit.

**6\. Full Flow (Reference Diagram)**

Report: "In Progress" (newly assigned OR returned from rejection) ↓ Team checks: does this report already have an after-photo in IMAGES? → indicates rework ↓ Capture / Select After-Photo ↓ Upload to Object Storage ↓ Review Evidence ↓ Confirm Submission ↓ ── Transaction ────────────────────── │ New IMAGES row created │ │ Status → "Awaiting Review" │ │ STATUS\_HISTORY row inserted │ │ ASSIGNMENTS.completed\_at set │ ───────────────────────────────────── ↓ Operator Review /
Approved Rejected ↓ ↓ "Resolved" Status → "In Progress" completed\_at completed\_at cleared unchanged (reset to null) ↓ ↓ Citizen views STATUS\_HISTORY approved photo row inserted ↓ Loop back to top (team resubmits)

**7\. Summary**

A rejected report simply becomes "In Progress" again — no separate rejected-items list is needed, since it reappears in the team's normal active-task view. Rework is signaled to the team through (a) the presence of a prior after-photo in IMAGES, (b) a notification specific to the rejection, and (c) a rejection reason, if the Operations Dashboard package provides one. Resubmission reuses the exact same Completion Evidence Submission flow and transaction — no separate mechanism exists for rework versus a first attempt. Rejected photos are never deleted, preserving a full audit trail, but only the approved submission's photo is ever shown to the citizen. The loop has no built-in cap on rejection cycles; any such limit would be a separate policy decision owned by the Operations Dashboard requirements.
