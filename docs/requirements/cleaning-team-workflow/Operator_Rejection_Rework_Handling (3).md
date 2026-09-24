**Operator Rejection / Rework Handling**

# Reference

This workflow is governed by FR-3.7 and defines how the Cleaning Team handles reports returned by an operator for rework.

# Purpose

This process describes what happens when an operator reviews a submitted cleaning report and determines that additional corrections are required before approval.

# Rework Trigger

A rework cycle begins when an operator rejects a submitted report and requests changes. The operator must provide rejection reasons explaining the required corrections. These comments are stored with the report history.

# Returned Report Visibility

When a report is rejected, its status changes to RETURNED\_FOR\_REWORK. The report automatically reappears in the Cleaning Team work list and is visually identified through status, rework badge, and updated timestamp.

# Rejection Feedback

The Cleaning Team can view rejection reasons, operator comments, rejection date/time, and corrective actions. All activities are recorded in STATUS\_HISTORY.

# Rework Process

Open the returned report, review comments, perform corrections, update the report, complete missing evidence, and prepare for resubmission.

# Completion Evidence Requirements

Required after photographs, confirmation of corrective actions, and any additional mandatory evidence must be included before resubmission.

# Resubmission

Selecting Resubmit changes the status from RETURNED\_FOR\_REWORK to SUBMITTED and sends the report back to the operator review queue.

# Expected Outcome

The process provides a controlled rework loop that ensures reports are corrected, documented, and resubmitted according to FR-3.7.

# Status Transition

| Current Status | Action | New Status |
| --- | --- | --- |
| SUBMITTED | Operator requests changes | RETURNED\_FOR\_REWORK |
| RETURNED\_FOR\_REWORK | Cleaning Team resubmits corrected report | SUBMITTED |
| SUBMITTED | Operator approves report | APPROVED |
