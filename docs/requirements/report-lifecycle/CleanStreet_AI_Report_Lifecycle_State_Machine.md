# Report Lifecycle — State Transition Model (CleanOps)

## Purpose

This document defines the complete state machine governing a CleanOps report from creation to closure: the nine states a report can occupy, every allowed transition between them (forward and backward), the condition that must hold for each transition to fire, who (which actor/system component) is permitted to trigger it, and what database side effects accompany it.

This specification finalizes and supersedes the provisional status naming used in earlier requirement documents (Completion Evidence Submission, Operator Rejection/Rework Handling, Task Assignment & Notification Flow, and the Functional Requirements section). See Section 6 for the terminology mapping.

---

## 1. States

| # | State | Meaning |
|---|---|---|
| 1 | **Sent** | Citizen has submitted the report; it exists in REPORTS but has not yet been analyzed. |
| 2 | **AI Compiled** | The AI service has finished detection, classification, severity scoring, and priority scoring, and written the results back to the report. |
| 3 | **Operator Reviewed** | An operator has opened the report and viewed its AI-compiled results (detected waste, category, severity, priority, any duplicate suggestions). |
| 4 | **Set** | An operator has assigned the report to a specific cleaning team. |
| 5 | **In Progress** | The assigned cleaning team has started work on the report. |
| 6 | **Cleaned** | The cleaning team has submitted completion evidence (after-photo) and is awaiting operator review. |
| 7 | **Validated** | An operator has reviewed the completion evidence and approved it as satisfactory. |
| 8 | **Closed** | The report is fully closed out; the citizen can view the completion evidence and, optionally, rate the resolution. This is a terminal state. |
| 9 | **Rejected/Duplicate** | The report has been identified as invalid or as a confirmed duplicate of another report and will not proceed further. This is a terminal state. |

---

## 2. State Diagram (Reference)

```
Sent
  │
  ▼ (AI service completes analysis)
AI Compiled
  │
  ▼ (operator opens the report)
Operator Reviewed ───────────────► Rejected/Duplicate   [terminal]
  │
  ▼ (operator assigns a team)
Set
  │
  ▼ (team starts work)
In Progress
  │
  ▼ (team submits completion evidence)
Cleaned ──────────────┐
  │                   │ (operator rejects evidence — rework needed)
  ▼ (operator approves)
Validated             │
  │                   │
  ▼ (system closes)   │
Closed [terminal]      ▼
                 In Progress  (loop back)
```

---

## 3. Transitions, Triggers, Validation Conditions, and Permissions

### 3.1 Sent → AI Compiled

- **Trigger:** The AI service finishes processing the report's submitted image (detection, classification, severity, priority).
- **Validation condition:** The report must have at least one `before`-type image in IMAGES (enforced at creation, per the citizen reporting requirements) before AI processing can run at all.
- **Who can trigger it:** System only (AI Service, invoked automatically by the backend immediately after a report is saved — FR-4.3). No human actor can force or skip this transition.
- **Side effects:** REPORTS updated with detection results, category confirmation, `severity_score`, `priority_score`; new STATUS_HISTORY row.

### 3.2 AI Compiled → Operator Reviewed

- **Trigger:** An operator opens the report on the Operations Dashboard for the first time after AI compilation.
- **Validation condition:** The report must be in `AI Compiled` status; opening an already-reviewed report does not re-trigger this transition.
- **Who can trigger it:** Operator only (by the act of viewing the report's AI-analysis details, FR-2.8–2.12).
- **Side effects:** New STATUS_HISTORY row. No change to REPORTS data fields beyond `current_status`.

### 3.3 Operator Reviewed → Set

- **Trigger:** The operator selects a cleaning team and confirms assignment.
- **Validation condition:** A valid, existing `team_id` must be selected from CLEANING_TEAMS.
- **Who can trigger it:** Operator only (FR-2.16).
- **Side effects:** New ASSIGNMENTS row (`report_id`, `team_id`, `assigned_at`); REPORTS `current_status` → `Set`; new STATUS_HISTORY row. (This is the same transaction defined in the Task Assignment & Notification Flow document, with the status name updated from the earlier placeholder "Assigned" to "Set.")

### 3.4 Operator Reviewed → Rejected/Duplicate

- **Trigger:** The operator confirms the report as a duplicate of an existing report (FR-2.14) or otherwise determines it is invalid (e.g., no genuine waste visible, inappropriate content).
- **Validation condition:** For a duplicate determination, a suggested duplicate link must already exist (produced by FR-4.7's automated check) and the operator must explicitly confirm it — the system never makes this transition on its own.
- **Who can trigger it:** Operator only.
- **Side effects:** REPORTS `current_status` → `Rejected/Duplicate`; new STATUS_HISTORY row; if applicable, a link is recorded to the report it duplicates. This is a terminal state — no further transitions are defined out of it.

### 3.5 Set → In Progress

- **Trigger:** A member of the assigned cleaning team marks the task as started.
- **Validation condition:** The requesting user's team must match `ASSIGNMENTS.team_id` for this report (the same backend authorization check defined in the Completion Evidence Submission document, applied here at the start of work as well, not only at submission).
- **Who can trigger it:** Cleaning team (assigned team only).
- **Side effects:** REPORTS `current_status` → `In Progress`; new STATUS_HISTORY row.

### 3.6 In Progress → Cleaned

- **Trigger:** The cleaning team confirms submission of completion evidence (the atomic transaction defined in the Completion Evidence Submission document).
- **Validation condition:** At least one `after`-type image must be attached and confirmed; the requesting user's team must match `ASSIGNMENTS.team_id`.
- **Who can trigger it:** Cleaning team (assigned team only).
- **Side effects:** New IMAGES row (`image_type = after`); REPORTS `current_status` → `Cleaned`; new STATUS_HISTORY row; `ASSIGNMENTS.completed_at` set to the confirmation timestamp. (This finalizes what earlier documents called the "Awaiting Review" placeholder status — see Section 6.)

### 3.7 Cleaned → Validated

- **Trigger:** The operator reviews the submitted completion evidence and approves it (FR-2.19).
- **Validation condition:** The report must currently be in `Cleaned` status with at least one `after`-type image present.
- **Who can trigger it:** Operator only.
- **Side effects:** REPORTS `current_status` → `Validated`; new STATUS_HISTORY row. `ASSIGNMENTS.completed_at` (already set in the prior transition) is left unchanged.

### 3.8 Cleaned → In Progress (backward transition — rework)

- **Trigger:** The operator reviews the submitted completion evidence and rejects it as insufficient (FR-2.20).
- **Validation condition:** The report must currently be in `Cleaned` status.
- **Who can trigger it:** Operator only.
- **Side effects:** REPORTS `current_status` → `In Progress`; new STATUS_HISTORY row; `ASSIGNMENTS.completed_at` is cleared (reset to null), since the work is not actually complete. The cleaning team is notified and must repeat the evidence-submission flow (back to transition 3.6) once rework is done. This loop (3.6 → 3.7/3.8) can repeat indefinitely; this specification places no cap on the number of cycles.

### 3.9 Validated → Closed

- **Trigger:** Automatic, immediately following validation.
- **Validation condition:** The report must be in `Validated` status.
- **Who can trigger it:** System only — no human action is required or permitted to force this transition independently of validation; it exists as a distinct audit step primarily to separate "operator approved the work" (Validated) from "the report is administratively finalized and visible to the citizen as complete" (Closed).
- **Side effects:** REPORTS `current_status` → `Closed`; new STATUS_HISTORY row; the citizen is notified (FR-1.15) and can now view the completion evidence (FR-1.16) and optionally rate the resolution (FR-1.17). This is a terminal state.

---

## 4. Summary Table — Allowed Transitions and Permissions

| From | To | Trigger Actor | Direction |
|---|---|---|---|
| Sent | AI Compiled | System (AI Service) | Forward |
| AI Compiled | Operator Reviewed | Operator | Forward |
| Operator Reviewed | Set | Operator | Forward |
| Operator Reviewed | Rejected/Duplicate | Operator | Forward (terminal) |
| Set | In Progress | Cleaning Team | Forward |
| In Progress | Cleaned | Cleaning Team | Forward |
| Cleaned | Validated | Operator | Forward |
| Cleaned | In Progress | Operator | **Backward** (rework) |
| Validated | Closed | System | Forward (terminal) |

**No other transitions are defined.** Specifically:
- A citizen can never trigger any state transition directly — only the initial creation of the report (which produces `Sent`).
- No state can be skipped (e.g., `Set` cannot move directly to `Cleaned` without passing through `In Progress`).
- `Closed` and `Rejected/Duplicate` are both terminal — no transitions are defined out of either.

---

## 5. Influencer Permissions — By Actor

| Actor | Transitions They Can Trigger |
|---|---|
| **Citizen** | None directly (only causes `Sent` to exist, via report creation) |
| **System (AI Service / Backend)** | Sent → AI Compiled; Validated → Closed |
| **Operator** | AI Compiled → Operator Reviewed; Operator Reviewed → Set; Operator Reviewed → Rejected/Duplicate; Cleaned → Validated; Cleaned → In Progress |
| **Cleaning Team** | Set → In Progress; In Progress → Cleaned |

Every operator- or cleaning-team-triggered transition is additionally gated by the relevant backend authorization check already defined elsewhere in the requirements (e.g., a cleaning team member can only affect a report their team is actually assigned to, per `ASSIGNMENTS.team_id`).

---

## 6. Terminology Mapping (Reconciliation With Earlier Documents)

This is the first document to define the full, finalized nine-state model. Earlier requirement documents were written before this model existed and used provisional or five-state terminology. The mapping below reconciles them:

| Earlier term (where used) | Finalized state in this model |
|---|---|
| "Submitted" (Functional Requirements, FR-1.14) | **Sent** |
| "Analyzed" (Functional Requirements, FR-1.14) | **AI Compiled** |
| "Assigned" (Functional Requirements, Task Assignment & Notification Flow) | **Set** |
| "In Progress" | **In Progress** (unchanged) |
| "Awaiting Review" (placeholder, Completion Evidence Submission Rev. 2) | **Cleaned** |
| "Resolved" (Functional Requirements, Completion Evidence Submission, Operator Rejection/Rework Handling) | Split into **Validated** (operator approval) and **Closed** (final, citizen-visible state) |
| *(not previously modeled)* | **Operator Reviewed** — new intermediate state, not previously named |
| *(not previously modeled)* | **Rejected/Duplicate** — new terminal state, not previously named |

**Recommendation:** the Functional Requirements document and the three cleaning-team-workflow documents referenced above should be updated to use this finalized terminology, since they currently reference a five-state model or a placeholder name that this document now supersedes. This specification does not itself edit those documents — that update is a separate, explicit action for whoever owns each file.

---

## 7. Summary

- The report lifecycle has nine states: Sent, AI Compiled, Operator Reviewed, Set, In Progress, Cleaned, Validated, Closed, Rejected/Duplicate.
- Exactly one backward transition exists in the entire model: Cleaned → In Progress, representing the operator rejecting completion evidence and sending work back for rework.
- Two terminal states exist: Closed (successful completion) and Rejected/Duplicate (invalid or duplicate report, never proceeds further).
- Every transition has exactly one designated actor type permitted to trigger it — citizens never trigger transitions directly, and every operator/team-triggered transition carries its own validation condition.
- This document finalizes naming that earlier documents left as placeholders or used inconsistently; those documents should be updated to match.
