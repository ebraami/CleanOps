# Task-List View — Requirements Specification
### CleanStreet AI — Operations Dashboard, Cleaning-Team View

---

## 1. Purpose

This document specifies what a cleaning team member sees when they have multiple assigned tasks in the CleanStreet AI operations dashboard: how the list is ordered and grouped, and what distinguishes an "open" task from a "completed" one. It extends Section 10 (Key Features and Requirements) and Section 11.3 (Priority Prediction) of the graduation project proposal into implementable view logic.

---

## 2. Task-List Ordering

### 2.1 Primary sort: Priority Score

Within a team member's assignment list, tasks are sorted **descending by priority score** by default. The priority score is the rule-weighted baseline defined in Section 12 of the proposal, combining:

| Factor | Contribution |
|---|---|
| Severity estimate (from image analysis / operator confirmation) | Higher severity → higher score |
| Repeat-report count at the same location | More repeats → higher score |
| Report age | Older unresolved reports gain weight over time |
| Location density (hotspot proximity) | Reports inside a known hotspot are weighted up |

### 2.2 Secondary sort (tie-break)

When two tasks have equal or near-equal priority scores (within a defined tolerance, e.g. ±2 points), the tie-break order is:
1. Older report timestamp first (oldest wins)
2. Shorter distance from the team's current/last location

### 2.3 Alternate groupings

The default view is priority-first, but the operator can switch the same list to:

- **By area** — tasks clustered by geographic zone or hotspot, priority-sorted within each cluster. Supports efficient routing when a team is working one district at a time.
- **By category** — grouped by waste category (e.g. illegal dumping, overflowing bin, litter), useful when a team has category-specific equipment.
- **By due/age** — oldest unresolved report first, regardless of score, as an override view to catch anything at risk of breaching a response-time target.

Switching grouping never changes the underlying priority score — it only changes how tasks are bucketed and displayed.

### 2.4 Pinning / manual override

A supervisor can manually pin a task to the top of a team's list (e.g. urgent escalation). Pinned tasks always display first, above the priority-sorted list, with a visible "pinned" indicator so the score-based logic isn't mistaken for having failed.

---

## 3. Status Model: Open vs. Completed

The task list is split into two top-level views: **Open** and **Completed**, mirroring the citizen-facing status states from Section 6 (Stages 4–5) and Section 22 (success criteria).

### 3.1 "Open" — states included

A task counts as open, and appears in the active task list, in any of these states:

| Status | Meaning | Who sets it |
|---|---|---|
| **Assigned** | Task has been routed to this team/operator but work hasn't started | System / supervisor assignment |
| **Acknowledged** | Team member has confirmed receipt | Operator |
| **In Progress** | Cleaning work has started | Operator |
| **Blocked** | Work paused (e.g. access issue, needs equipment, citizen report unclear) | Operator, with a required reason field |

Blocked tasks remain in the Open list but are visually flagged (e.g. amber marker) so they don't silently sit at the bottom of a priority sort.

### 3.2 "Completed" — states included

A task moves to Completed once:

| Status | Meaning | Who sets it |
|---|---|---|
| **Resolved — Pending Verification** | Operator has finished work and uploaded after-photo evidence, but citizen/system confirmation hasn't yet run | Operator |
| **Verified / Closed** | After-photo evidence accepted and citizen notified of resolution (Section 6, Stage 5) | System (automatic) or supervisor |
| **Rejected / Invalid** | Report was found to be invalid, duplicate, or outside jurisdiction on inspection | Operator, with required reason field |

Completed tasks drop out of the active priority-sorted list immediately upon status change, but remain visible in a separate, filterable Completed tab (searchable by date, area, or operator) for accountability and the audit logging requirement in Section 16.

### 3.3 State transition rules

- A task can only move from Open → Completed, never skip Assigned directly to Verified/Closed without passing through In Progress and Resolved-Pending-Verification (or Rejected, which can be set at any open state).
- Completion requires at least one after-photo (or an explicit reason if photo capture isn't possible), consistent with the "completion evidence" requirement in Sections 9–10.
- Every status change is timestamped and attributed to an operator ID for the audit log.

---

## 4. Summary of the Default View

For a team member opening the dashboard:

1. **Open tab** (default landing view), sorted by priority score descending, pinned items first, blocked items flagged.
2. **Completed tab**, most recently completed first, filterable by date/area.
3. A toggle to switch the Open tab's grouping to By Area, By Category, or By Age without altering scores.

This keeps the highest-impact work at the top by default while giving operators the flexibility to work by geography or category when that better fits their route or equipment for the day.
