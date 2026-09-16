# Operator Assignment & Resolution

> **CleanOps — Smart Urban Cleaning & Waste Management System**  
> **Phase:** P01 — Project Foundation & Requirements  
> **Work Package:** Functional Requirements  
> **Scope:** Operator Functions — Assignment & Resolution

---

## 1. Purpose

This document defines the functional behavior required for operators to manage actionable cleaning reports from operational assessment through assignment, completion review, and resolution.

The capability establishes a controlled operational path for:

**Assess → Handle Duplicates → Assign → Monitor → Verify → Resolve**

The requirements describe system behavior and expected outcomes without prescribing implementation technology, interface design, database structure, or specific software architecture.

---

## 2. Scope

This capability covers:

- Viewing report severity and priority
- Reviewing duplicate or related reports
- Assigning cleaning teams
- Managing operational report status
- Reviewing completion evidence
- Resolving completed reports
- Returning reports for further action
- Maintaining operational traceability throughout these actions

---

## 3. Primary Actor

### Operator

An authorized operational user who manages actionable cleaning reports, assigns cleaning teams, monitors operational progress, reviews completion evidence, and determines whether a report can be resolved.

---

# 4. Functional Behavior

## 4.1 Severity & Priority Assessment

### Objective

Provide the operator with the information required to understand the urgency and operational importance of a report before taking action.

### Required behavior

The system shall allow an authorized operator to:

- View the report's current severity.
- View the report's current priority.
- View the report information relevant to understanding the priority.
- View relevant AI analysis results when they contribute to prioritization.
- Identify the report's current operational status.
- Access the information required to make an assignment or operational decision.

### Acceptance criteria

The capability is satisfied when an authorized operator can open an actionable report and determine its current severity and priority together with the relevant supporting report information.

---

## 4.2 Duplicate & Related Report Handling

### Objective

Prevent multiple reports describing the same real-world issue from unnecessarily generating duplicate operational work.

### Required behavior

The system shall allow an authorized operator to:

- Review reports identified as potentially duplicate or related.
- Examine the relationship between the reports.
- Confirm the appropriate handling of a duplicate report.
- Associate a duplicate with the corresponding existing case where applicable.
- Prevent unnecessary duplicate operational processing.
- Preserve the original reports and their relevant history.

### Acceptance criteria

The capability is satisfied when an authorized operator can review a potential duplicate relationship, make the appropriate operational decision, and the system preserves the relationship and report history without creating unnecessary duplicate work.

### Separation of responsibility

Duplicate detection or similarity analysis may be produced by AI or other system capabilities. This capability defines the **operator's handling of the resulting duplicate information**, not the implementation of duplicate-detection algorithms.

---

## 4.3 Cleaning Team Assignment

### Objective

Route an actionable report to the appropriate cleaning team for execution.

### Required behavior

The system shall allow an authorized operator to:

- View the information required to make an assignment.
- View available or eligible cleaning teams where applicable.
- Select a cleaning team.
- Assign the report to the selected team.
- Record the assignment against the report.
- Display the current assigned team to authorized users.
- Preserve assignment history when an assignment changes.

### Acceptance criteria

The capability is satisfied when an authorized operator can assign an eligible report to an appropriate cleaning team and the resulting assignment is persistently recorded and visible to authorized users.

---

## 4.4 Operational Status Management

### Objective

Maintain an accurate representation of where each report currently stands within the operational process.

### Required behavior

The system shall:

- Allow authorized operators to perform permitted status changes.
- Enforce the defined report lifecycle when changing status.
- Prevent invalid status transitions.
- Persist the resulting status.
- Make the current status available to authorized users.
- Preserve significant status changes for operational traceability.

### Acceptance criteria

The capability is satisfied when an authorized operator can perform a valid status transition and the system records and consistently reflects the resulting report state.

### Lifecycle relationship

The authoritative set of report states and transitions is defined by the **Report Lifecycle** requirements. This capability consumes and applies those rules rather than defining a separate lifecycle.

---

## 4.5 Completion Evidence Review

### Objective

Allow the operator to determine whether the reported cleaning work has been sufficiently completed before the case can be resolved.

### Required behavior

The system shall allow an authorized operator to:

- Access completion evidence submitted for a report.
- View the evidence together with the relevant report context.
- Evaluate the submitted evidence.
- Record an acceptance outcome when the evidence satisfies the required conditions.
- Record an outcome requiring further action when the evidence or completed work is insufficient.
- Preserve the evidence and review outcome.

### Acceptance criteria

The capability is satisfied when an authorized operator can review submitted completion evidence and record a clear outcome that determines the report's subsequent operational path.

### Evidence relationship

Completion evidence shall remain associated with the report and the corresponding cleaning action so that the resolution decision can be understood from the case history.

---

## 4.6 Report Resolution

### Objective

Formally conclude an operational case after the required cleaning work has been completed and accepted.

### Required behavior

The system shall allow an authorized operator to resolve a report only when the required resolution conditions have been satisfied.

The system shall:

- Confirm that the required cleaning action has been completed.
- Confirm that the required completion evidence has been accepted where applicable.
- Record the resolution.
- Preserve the assignment, completion, and review history.
- Reflect the resolved/closed state to authorized users.

### Acceptance criteria

The capability is satisfied when an eligible report that has completed the required operational and verification conditions can be resolved and the resolution is permanently represented in the report history.

### Resolution guardrail

Submission of completion evidence alone shall not automatically constitute resolution unless the defined verification conditions have been satisfied.

---

## 4.7 Further Action

### Objective

Provide a controlled path for reports that cannot yet be considered successfully resolved.

### Required behavior

The system shall allow an authorized operator to:

- Return an eligible report for further action.
- Record the reason that additional action is required.
- Provide relevant instructions or comments where applicable.
- Return the report to the appropriate operational stage.
- Preserve the previous work and review history.
- Keep the report active and traceable until successful resolution.

### Acceptance criteria

The capability is satisfied when an authorized operator can return insufficiently completed work for further action, the reason is preserved, and the report continues through the appropriate operational lifecycle.

---

# 5. End-to-End Operational Flow

```text
                    ACTIONABLE REPORT
                           │
                           ▼
                ┌──────────────────────┐
                │ Review Severity &    │
                │ Priority             │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Check Duplicate /    │
                │ Related Reports      │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Assign Cleaning Team │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Manage Operational   │
                │ Status               │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Cleaning Completed   │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Review Completion    │
                │ Evidence             │
                └───────┬───────┬──────┘
                        │       │
                 Accepted       │ Further Action
                        │       │
                        ▼       ▼
                 ┌──────────┐  ┌─────────────────┐
                 │ Resolve  │  │ Return for      │
                 │ Report   │  │ Further Action  │
                 └────┬─────┘  └────────┬────────┘
                      │                 │
                      ▼                 │
                   CLOSED ◄────────────┘
```

The exact state names and permitted transitions are governed by the **Report Lifecycle** requirements.

---

# 6. Business Rules

### Assignment

- Only authorized operators may assign or reassign cleaning teams.
- An assignment must be associated with the relevant report.
- Assignment changes must remain traceable.

### Duplicate handling

- A confirmed duplicate must not unnecessarily generate an independent cleaning operation for the same underlying issue.
- Duplicate relationships must not erase the original report history.

### Status

- Status changes must follow the defined report lifecycle.
- Invalid state transitions must not be accepted.
- The system must maintain one authoritative current state for each report.

### Verification

- Completion evidence must be reviewed according to the defined verification process.
- Insufficient completion must be capable of being returned for further action.
- Review outcomes must remain associated with the report.

### Resolution

- A report must not be resolved before the required completion and verification conditions are satisfied.
- Resolution must preserve the operational history required to understand how the case was completed.

---

# 7. Edge & Exception Behavior

| Condition | Required behavior |
|---|---|
| No suitable cleaning team is available | The report remains actionable and the system must not silently assign an unsuitable team. |
| Report already has an assignment | The system must prevent accidental conflicting assignment or require an explicit authorized reassignment. |
| Potential duplicate identified | The operator can review and determine the appropriate duplicate handling without losing report history. |
| Completion evidence is insufficient | The operator can return the report for further action with the review outcome preserved. |
| Report is already resolved | The system must prevent an ordinary duplicate resolution action. |
| Invalid status transition | The transition must be rejected and the existing valid state preserved. |
| Required completion condition is missing | Resolution must not be permitted. |
| Operational action fails to persist | The system must not represent the action as successfully completed when the resulting state has not been recorded. |

---

# 8. Information Traceability

The following operational relationships must remain understandable throughout the report's history:

```text
Report
  │
  ├── Severity / Priority
  │
  ├── Duplicate / Related Relationships
  │
  ├── Assignment
  │     └── Cleaning Team
  │
  ├── Status History
  │
  ├── Cleaning Action
  │     └── Completion Evidence
  │
  ├── Verification Outcome
  │
  └── Resolution / Further Action
```

An operator or authorized reviewer should be able to understand the sequence of operational decisions without relying on information that has been silently overwritten or discarded.

---

# 9. Interfaces With Other Requirements

This capability interacts with other CleanOps requirements as follows:

| Related area | Relationship |
|---|---|
| **AI Requirements** | Provides AI-derived analysis and potential duplicate/related-report information used during operational decisions. |
| **Data Requirements** | Defines the information that must be available for reports, assignments, evidence, statuses, and operational history. |
| **Security Requirements** | Defines authorization and protection requirements for operator actions and report information. |
| **Cleaning-Team Workflow** | Defines the work performed by the cleaning team after assignment. |
| **Report Lifecycle** | Defines the authoritative report states and permitted transitions used by operator actions. |
| **Analytics Requirements** | May use assignment, status, resolution, and historical operational data for monitoring and reporting. |

This document defines the operator behavior required to use these capabilities; it does not duplicate their implementation or detailed requirements.

---

# 10. Acceptance Coverage

The complete capability is covered when the system supports all of the following:

- [x] Operator can view severity and priority.
- [x] Operator can review duplicate or related reports.
- [x] Operator can handle confirmed duplicate reports.
- [x] Operator can assign a cleaning team.
- [x] Operator can manage valid operational status transitions.
- [x] Operator can review completion evidence.
- [x] Operator can accept satisfactory completion.
- [x] Operator can return insufficient work for further action.
- [x] Operator can resolve an eligible report.
- [x] Assignment and resolution actions remain traceable.
- [x] Invalid or premature operational actions are prevented.
- [x] Operator behavior remains consistent with the Report Lifecycle.

---

# 11. Definition of Done

This capability is complete when the Functional Requirements deliverable:

1. Defines the complete operator assignment and resolution behavior.
2. Covers severity, priority, duplicate handling, assignment, status, evidence review, resolution, and further action.
3. Defines observable acceptance conditions for each capability.
4. Defines expected behavior for relevant edge and exception conditions.
5. Establishes traceability between report, assignment, cleaning action, evidence, review, and resolution.
6. Maintains clear boundaries with AI, Data, Security, Cleaning-Team Workflow, Report Lifecycle, and Analytics requirements.
7. Contains no implementation-specific dependency that would restrict architectural decisions.
8. Can be used as a direct reference for subsequent system design, implementation, and testing.

---

## 12. Requirement Quality Principles

The requirements in this document follow these principles:

- **Observable:** behavior can be verified through system outcomes.
- **Unambiguous:** each capability has a defined purpose and expected result.
- **Traceable:** operational decisions remain connected to the report history.
- **Consistent:** behavior follows the defined report lifecycle.
- **Technology-neutral:** requirements describe system behavior rather than implementation.
- **Testable:** each capability has a concrete acceptance condition.
- **Non-destructive:** operational actions do not silently remove historical context.
