**Functional Specification Document (FSD)**

**Operator Rejection & Rework Handling Workflow | Requirement FR-3.7**

| **Document Title:** Operator Rejection / Rework Handling | **Requirement Reference:** FR-3.7 |
| --- | --- |
| **Target User:** Cleaning Team / Field Workers | **Workflow Scope:** Cleaning Team Rework Loop |

**1\. Overview & Objective**

This document defines the operational and system specification for the rework workflow on the cleaning-team side when an operator sends a report back for further action or correction. It details how returned tasks are identified, displayed, updated, and resubmitted, fulfilling Requirement FR-3.7.

**2\. Rework Workflow Lifecycle (FR-3.7)**

**Step 1: Rejection Trigger & System State Update**

- **Status Update:** When an operator rejects or requests changes on a submitted cleaning report, the system immediately changes the report status from Submitted / Under Review to Needs Rework (or Returned).
- **Notification Dispatch:** An automated push notification and in-app priority alert are dispatched to the assigned cleaning team/personnel.

**Step 2: Task Listing & Visual Indicators**

The returned report reappears prominently in the Cleaning Team's active job list with explicit visual indicators:

- **Priority Placement:** Returned tasks automatically float to the top of the 'My Tasks' / 'Active Jobs' dashboard, categorized with High Priority.
- **Status Badge:** Highlighted with a distinct status tag (e.g., Orange/Amber Badge: 'Needs Rework').
- **Operator Feedback Banner:** A prominent feedback banner attached to the task card displays specific rejection reasons, missing checklist items, operator comments, and rejection timestamp.
- **Visual Warning Cues:** An explicit warning symbol (⚠️) and highlighted border appear next to the task title to immediately differentiate it from regular pending tasks.

**Step 3: Cleaning Team Correction & Editing**

Upon opening the task details, the cleaning team performs the following operations:

- **Instructions Review:** Review exact operator instructions (e.g., 'Section B cleaning incomplete - upload new photo proof').
- **On-Site Execution:** Field personnel perform required corrective tasks on-site.
- **Data Revision:** The team updates mandatory fields, replaces/adds post-cleaning images, or updates status logs. Previous submission data remains readable for context.

**Step 4: Resubmission & System Response**

- **Dynamic Button:** The standard 'Submit' button dynamically changes to 'Resubmit Report' for returned tasks.
- **Validation Check:** The system verifies that all operator-requested corrections and required evidence have been properly provided before allowing submission.
- **State Transition:** Tapping 'Resubmit Report' updates the state to Resubmitted (or Under Review), moves the task back to the operator queue, and logs the action in the system audit trail.

**3\. State Transition Matrix (FR-3.7)**

| **Initial State** | **Trigger Action** | **New State** | **Cleaning Team UI View** |
| --- | --- | --- | --- |
| Submitted | Operator rejects report with feedback | Needs Rework | Priority alert badge ('Needs Rework'), operator notes banner, edit access enabled |
| Needs Rework | Cleaning team updates data & taps 'Resubmit' | Resubmitted | Task locked for editing, status updated to 'Pending Operator Review' |
