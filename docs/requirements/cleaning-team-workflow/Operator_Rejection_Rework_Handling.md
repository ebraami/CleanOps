**Operator Rejection / Rework Handling**

_Cleaning-Team Perspective_

| **Project** | CleanStreet AI — Smart Citizen-Requested Street Cleaning and Waste Management Platform |
| --- | --- |
| **Work Package** | Cleaning-Team Workflow |
| **Primary Task Reference** | FR-3.7 |
| **Related Requirements** | FR-2.20, IPR-08, IPR-09, Completion Evidence Submission |
| **Document Type** | Functional Workflow / Rework Handling Requirement |

# 1. Purpose

This document defines the cleaning-team-side behavior when a submitted completion report is returned by the operator for further action or rework. The returned report must re-enter the existing cleaning workflow in a controlled, traceable, and repeatable way rather than being treated as a new report.

**Source alignment:** The existing cleaning-team workflow defines RETURNED\_FOR\_REWORK as a non-terminal state that returns the request to active work, while the Completion Evidence Submission document defines the evidence-submission flow that can be repeated after rejection.

# 2. Scope

This requirement covers the workflow after an operator returns a submitted report and before the cleaning team sends the corrected evidence back for review.

## In Scope

- Returning the existing report to the responsible cleaning team's active workflow.
- Clearly identifying that the report requires rework.
- Preserving the existing report identity and workflow history.
- Allowing the team to reopen the returned report and understand the available rework context.
- Performing the required corrective cleaning work.
- Repeating the existing completion-evidence submission process.
- Returning the report to the operator for another review cycle.
- Recording status transitions for traceability and auditability.

## Out of Scope

- The operator's approval/rejection decision itself.
- The detailed rules used by the operator to evaluate evidence.
- Citizen-side handling after resolution.
- Physical collection logistics, autonomous cleaning, or fleet-management behavior.

# 3. Trigger

The rework loop starts when the operator reviews the cleaning team's submitted completion evidence and determines that the cleaning work was not sufficiently completed or that the submitted evidence does not support successful completion.

# 4. Rework Workflow

| CLEANING TEAM   ↓ Submit Completion Evidence   UNDER\_REVIEW   ↓   Operator Decision   ↙ ↘   Approved Rejected   ↓ ↓   RESOLVED RETURNED\_FOR\_REWORK   ↓   Cleaning Team List   ↓   Rework Indicator   ↓   Open Report   ↓   Review Rework Context   ↓   Perform Rework   ↓   Capture New Evidence   ↓   Review & Confirm   ↓   Submit Again   ↓   UNDER\_REVIEW |
| --- |

# 5. Detailed Functional Behavior

## 5.1 Return the Existing Report

- The same report shall return to the responsible cleaning team.
- A new report shall not be created as a consequence of rejection.
- The existing report\_id shall remain associated with the request throughout the rework cycle.
- The request shall move from the review stage into the rework workflow.

| UNDER\_REVIEW → RETURNED\_FOR\_REWORK → IN\_PROGRESS |
| --- |

## 5.2 Rework Identification

A returned report must be distinguishable from ordinary active reports. The cleaning team's list should clearly indicate that the report requires rework. The exact UI component, badge, color, or button label is an implementation decision; the functional requirement is clear visibility of the rework state.

| **Report** | **Status** | **Action** |
| --- | --- | --- |
| R-1021 | In Progress | Continue Work |
| R-1022 | Rework Required | Review & Rework |
| R-1023 | Completed | — |

## 5.3 Rework Context

When the cleaning team opens a returned report, the system should make the available rework context visible alongside the existing report information. The team should be able to identify the report, see its current state, recognize that rework is required, and review the available information explaining why further action is required.

## 5.4 Perform Rework

The cleaning team performs the required corrective cleaning activity. During this stage, the request is active again and follows the existing IN\_PROGRESS behavior.

| RETURNED\_FOR\_REWORK → IN\_PROGRESS → Rework Completed |
| --- |

## 5.5 Updated Completion Evidence

After the rework is completed, the team repeats the existing completion-evidence submission process:

1. Open the report.
2. Capture or select an updated after-photo.
3. Upload the photo using the configured object-storage mechanism.
4. Review the evidence and the report association.
5. Confirm the submission.
6. Submit the evidence for operator review.

At least one after-photo is required by the existing completion-evidence requirement. The evidence remains associated with the existing report rather than creating a new report.

## 5.6 Resubmission

| Rework Completed → Evidence Submitted → UNDER\_REVIEW → Operator Review Again |
| --- |

Resubmission must not automatically resolve the report. The final resolution decision remains with the operator.

## 5.7 Repeatability

The rework loop is repeatable. If the operator rejects the resubmitted evidence again, the same report can enter RETURNED\_FOR\_REWORK again without creating a duplicate report.

| UNDER\_REVIEW → RETURNED\_FOR\_REWORK → IN\_PROGRESS → Rework → Evidence → UNDER\_REVIEW |
| --- |

# 6. Status Model

| **State** | **Meaning** |
| --- | --- |
| **UNDER\_REVIEW** | Completion evidence is awaiting operator decision. |
| **RETURNED\_FOR\_REWORK** | The operator has determined that further action is required. |
| **IN\_PROGRESS** | The cleaning team is actively performing the required work. |
| **COMPLETED** | Cleaning work has been completed and is ready for evidence submission. |
| **EVIDENCE\_SUBMITTED** | Completion evidence has been submitted for review. |
| **RESOLVED** | The operator has accepted the completion. |

# 7. Status History & Auditability

All status transitions in the rework loop shall remain traceable through the existing status-history mechanism.

| ASSIGNED → IN\_PROGRESS → COMPLETED → EVIDENCE\_SUBMITTED → UNDER\_REVIEW   → RETURNED\_FOR\_REWORK → IN\_PROGRESS → COMPLETED → EVIDENCE\_SUBMITTED   → UNDER\_REVIEW → RESOLVED |
| --- |

This preserves the history of the original attempt, the rejection, the rework, the resubmission, and the eventual resolution.

# 8. Data Integrity

- The rework cycle operates on the existing report; it does not create a duplicate report.
- The original report\_id remains associated with the request.
- The original citizen before-photo is not replaced.
- New after-evidence can be stored as additional IMAGES records associated with the same report.
- Status transitions remain recorded in STATUS\_HISTORY.

# 9. Functional Requirements

| **ID** | **Requirement** | **Statement** |
| --- | --- | --- |
| **FR-RW-01** | **Return to Cleaning Team** | When a report is rejected, the system shall make the existing report available to the responsible cleaning team for further action. |
| **FR-RW-02** | **Rework State** | The system shall represent the returned request as requiring rework before it returns to active cleaning work. |
| **FR-RW-03** | **Rework Visibility** | The cleaning team's report list shall clearly indicate that the returned report requires rework. |
| **FR-RW-04** | **Existing Report Preservation** | The system shall preserve the existing report\_id and shall not create a new report as a result of rejection. |
| **FR-RW-05** | **Rework Context** | The system shall provide the available information needed by the team to understand why further action is required. |
| **FR-RW-06** | **Rework Execution** | The cleaning team shall be able to reopen the returned report and perform the required corrective work. |
| **FR-RW-07** | **Updated Evidence** | After rework, the team shall be able to submit updated completion evidence using the existing submission flow. |
| **FR-RW-08** | **Resubmission** | After confirmation, the updated evidence shall be submitted to the operator for another review cycle. |
| **FR-RW-09** | **No Automatic Resolution** | Resubmission shall not automatically resolve the report; resolution remains dependent on operator review. |
| **FR-RW-10** | **Audit Trail** | Status transitions throughout the rework cycle shall remain recorded in the request's status history. |
| **FR-RW-11** | **Repeatable Rework** | The workflow shall support repeated return/rework/resubmission cycles when necessary. |

# 10. Acceptance Criteria

| **Acceptance Criterion** | **Expected Result** |
| --- | --- |
| **AC-01 — Returned Report Appears Again** | Given a submitted report is returned by the operator, the existing report becomes available to the responsible cleaning team again. |
| **AC-02 — Rework Is Clearly Identifiable** | Given a report has been returned, the cleaning team's list clearly identifies that it requires rework. |
| **AC-03 — No Duplicate Report** | Given a report is returned, the system continues using the existing report\_id. |
| **AC-04 — Team Can Perform Rework** | Given a returned report is opened, the cleaning team can perform the required corrective cleaning activity. |
| **AC-05 — Updated Evidence Can Be Submitted** | Given rework is completed, the team can repeat the existing completion-evidence submission process. |
| **AC-06 — Operator Receives Resubmission** | Given the team confirms updated evidence, the report becomes available to the operator for another review. |
| **AC-07 — No Automatic Resolution** | Given updated evidence is submitted, the report remains subject to operator review and is not automatically marked RESOLVED. |
| **AC-08 — History Is Preserved** | Given a report has completed a rejection/rework cycle, the previous states and transitions remain traceable. |
| **AC-09 — Rework Can Repeat** | Given a resubmitted report is rejected again, the same rework process can be initiated without creating a duplicate report. |

# 11. End-to-End Example

Initial submission:

| IN\_PROGRESS → COMPLETED → EVIDENCE\_SUBMITTED → UNDER\_REVIEW |
| --- |

Operator rejects the submission:

| UNDER\_REVIEW → RETURNED\_FOR\_REWORK |
| --- |

Cleaning team performs the rework:

| RETURNED\_FOR\_REWORK → IN\_PROGRESS → COMPLETED |
| --- |

Team resubmits updated evidence:

| COMPLETED → EVIDENCE\_SUBMITTED → UNDER\_REVIEW |
| --- |

Second operator decision:

| UNDER\_REVIEW → RESOLVED   or   UNDER\_REVIEW → RETURNED\_FOR\_REWORK (repeatable) |
| --- |

# 12. Traceability

| **Source / Requirement** | **Relationship to This Task** |
| --- | --- |
| **FR-3.7** | Primary reference explicitly named by the current task. |
| **FR-2.20** | Related operator rejection / return-for-rework requirement identified in the Completion Evidence document. |
| **IPR-08** | Defines return to the workflow for further action when cleaning/evidence is not satisfactory. |
| **IPR-09** | Defines recording status changes for auditability. |
| **Completion Evidence Submission** | Defines the evidence submission flow that is repeated after rework. |
| **IMAGES** | Stores completion evidence against the existing report\_id. |
| **STATUS\_HISTORY** | Maintains the request's status/audit trail. |

# 13. Implementation Boundary

This document defines the required functional behavior of the cleaning-team rework loop. It does not prescribe a specific UI design. Badge names, colors, button labels, notification mechanisms, and other presentation details may be selected during UI/implementation design provided that the functional behavior and acceptance criteria remain satisfied.

# 14. Final Workflow Summary

| Operator submits decision   ↓   UNDER\_REVIEW   ↙ ↘   Approved Rejected   ↓ ↓   RESOLVED RETURNED\_FOR\_REWORK   ↓   Cleaning Team List   ↓   Rework Identification   ↓   Open Report   ↓   Perform Rework   ↓   COMPLETED   ↓   Submit Updated Evidence   ↓   UNDER\_REVIEW   ↓   Operator Review Again |
| --- |

**_End of Document_**
