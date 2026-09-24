**Work Package Documentation: Operator Rejection / Rework Handling**

_Work Package: Cleaning-Team Workflow | Version: 2.0 (Aligned with Finalized Diagram)_

**1\. Overview & Objective**

This document specifies the standard procedure and state transitions for handling task rejections and rework within the Cleaning-Team Workflow. The objective is to maintain strict operational consistency across all project artifacts, ensuring that task status updates strictly utilize the authorized project state definitions without introducing unapproved custom states.

**2\. Authorized Project States**

In compliance with the finalized Cleaning-Team Workflow Diagram, all task transitions during rework handling must strictly utilize the following 5 standard project states:

| **State Identifier** | **Description & Usage in Rework Loop** |
| --- | --- |
| **UNDER\_REVIEW** | The task proof/evidence has been submitted and is currently being evaluated by the Team Leader / Operator. |
| **RETURNED\_FOR\_REWORK** | The submitted work was rejected due to quality issues or incomplete tasks. Replaces previous 'Needs Rework' label. |
| **IN\_PROGRESS** | The Cleaning Team is actively working on correcting the identified issues and fulfilling rework requirements. |
| **EVIDENCE\_SUBMITTED** | The Cleaning Team has completed the necessary rework and re-uploaded updated evidence/proof. Replaces previous 'Resubmitted' label. |
| **COMPLETED** | The rework evidence has been reviewed and approved by the Team Leader, officially closing the task. |

**3\. Rework Workflow Execution Steps**

**Step 1: Rejection & Feedback Issuance**

- **Initial Review:** Initial state is UNDER\_REVIEW upon first task submission.
- **Action:** If defects or incomplete items are identified, the Operator changes the state from UNDER\_REVIEW to RETURNED\_FOR\_REWORK.
- **Requirements:** Specific feedback, rejection reasons, and required corrections must be logged in the system notes.

**Step 2: Rework Execution**

- **Action:** Upon notification of rejection, the Cleaning Team updates the state from RETURNED\_FOR\_REWORK to IN\_PROGRESS.
- **Execution:** The team addresses all logged issues and performs necessary cleaning/corrections on site.

**Step 3: Rework Re-submission**

- **Action:** Once corrections are completed, the team uploads updated photographic/field evidence and transitions the state from IN\_PROGRESS to EVIDENCE\_SUBMITTED.
- **Queue:** The task automatically enters the verification queue for the Operator.

**Step 4: Final Evaluation & Closure**

- **Action:** The Operator re-evaluates the submission under EVIDENCE\_SUBMITTED (moving status to UNDER\_REVIEW during evaluation).
- **Outcome:** If approved, the state transitions to COMPLETED. If further rework is needed, the state transitions back to RETURNED\_FOR\_REWORK.

**4\. State Transition Matrix**

| **From State** | **To State** | **Trigger / Action** |
| --- | --- | --- |
| **UNDER\_REVIEW** | **RETURNED\_FOR\_REWORK** | Operator rejects submission with feedback |
| **RETURNED\_FOR\_REWORK** | **IN\_PROGRESS** | Cleaning Team begins working on requested fixes |
| **IN\_PROGRESS** | **EVIDENCE\_SUBMITTED** | Cleaning Team uploads new evidence |
| **EVIDENCE\_SUBMITTED** | **UNDER\_REVIEW** | Task re-enters review queue for Operator evaluation |
| **UNDER\_REVIEW** | **COMPLETED** | Operator approves rework evidence and closes task |
