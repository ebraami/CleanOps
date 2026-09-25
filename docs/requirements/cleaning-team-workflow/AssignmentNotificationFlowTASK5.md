# Task Assignment & Notification Flow — CleanStreet AI

## Purpose

Before a cleaning team can act on a report, two things have to happen: an operator has to decide who should handle it, and the team has to actually find out about it and see everything they need to start work. This document defines that entire handoff — from the operator's assignment action on the dashboard to the report showing up, fully detailed, in the cleaning team's task list, with a notification confirming it. It connects **FR-2.16** (operator assigns a report) on one end to **FR-3.1** (team receives assigned task), **FR-3.2/FR-3.3** (team views assignment details), and **FR-3.6** (team receives notification) on the other.

---

## 1. Why This Flow Matters

A report sitting in the "Submitted" or "Analyzed" state is just data — nobody is responsible for it yet. The moment an operator assigns it to a team, that changes: the report now has an owner, a deadline pressure implied by its priority score, and a team that needs to know it exists without having to constantly refresh a dashboard and check. Getting this handoff right means the team never misses a new assignment and always has what they need the first time they open it, without back-and-forth with the operator.

---

## 2. The Trigger

The entire flow begins with a single, deliberate, operator-initiated action: the operator selects a cleaning team for a specific report and confirms the assignment (**FR-2.16**). This is never automatic — the system does not assign reports to teams on its own, by geography, by workload, or by any other rule, unless a future phase explicitly adds that capability. For now, a human operator makes this decision every time, typically informed by the report's location, category, and priority score, plus whatever they know about each team's current workload (**FR-2.24**) and area (from `CLEANING_TEAMS.area`).

---

## 3. Step-by-Step Flow

**Step 1 — Operator confirms assignment.**
On the Operations Dashboard, the operator opens a report (in "Submitted" or "Analyzed" status), selects one of the available cleaning teams from a list, and confirms the assignment action.

**Step 2 — Backend transaction.**
The moment the operator confirms, the backend performs the following together, as a single transaction — either the whole thing succeeds, or none of it does, so the system never ends up in a half-assigned state:

- A new row is created in `ASSIGNMENTS`: `report_id` (the report being assigned), `team_id` (the chosen team), `assigned_at` (the current server timestamp).
- The report's `current_status` in `REPORTS` is updated to `"Assigned"`.
- A new row is inserted into `STATUS_HISTORY`, recording the transition into `"Assigned"` along with the timestamp — preserving the audit trail required elsewhere in the proposal (Section 15.2, Section 17).

**Step 3 — The report appears in the team's task list.**
This step requires no extra mechanism of its own. Because the report's `current_status` is now `"Assigned"` and a matching row now exists in `ASSIGNMENTS` linking it to a specific `team_id`, the cleaning team's task list (**FR-3.1**) — which is simply a query for reports where `ASSIGNMENTS.team_id` matches the logged-in team and status is active (`"Assigned"` or `"In Progress"`) — naturally includes this report the next time it loads. There is no separate "push the report to the team" step; the database state itself is what makes the report visible.

**Step 4 — The team opens the assignment and sees full details.**
When a team member taps into the newly assigned report (**FR-3.2/FR-3.3**), they see everything needed to actually go do the work, with no further steps or requests required:

| Data | Source | Purpose |
|---|---|---|
| Photo(s) | `IMAGES` (`image_type = before`) | Shows what the citizen originally reported |
| Location | `REPORTS.latitude` / `longitude` | Lets the team navigate to the exact site, map-viewable |
| Category | `REPORTS.category_id` → `CATEGORIES` | Tells the team what kind of waste/issue to expect |
| Description | `REPORTS.description` (if provided) | Any extra context the citizen added |
| Priority score | `REPORTS.priority_score` | Lets the team judge how urgent this is relative to their other open tasks |

All of this data already existed on the report before assignment — nothing new is generated at assignment time except the `ASSIGNMENTS` row and the status change itself. Assignment simply grants the team visibility into a report that was already fully described.

**Step 5 — Notification is sent.**
In parallel with (or immediately following) Step 2, the backend triggers a push notification to the assigned team (**FR-3.6**), referencing the specific report so the team doesn't have to notice the change by checking the app manually. This reuses the exact same Firebase Cloud Messaging mechanism already used for citizen notifications (**FR-1.15/FR-8.1**) — the only difference is the recipient: the team's account/device rather than the citizen's.

---

## 4. What Changes, in One Transaction

To make the atomicity explicit, here is exactly what Step 2 writes, together, as a single unit of work:

| Table | Change |
|---|---|
| `ASSIGNMENTS` | New row inserted: `report_id`, `team_id`, `assigned_at` |
| `REPORTS` | `current_status` updated to `"Assigned"` |
| `STATUS_HISTORY` | New row inserted: `status = "Assigned"`, with timestamp |

If any part of this transaction fails (e.g., a database error), none of it should be applied — the operator should see an error and be able to retry, rather than ending up with, say, an `ASSIGNMENTS` row but no status update, which would leave the report in an inconsistent state neither the team nor the operator can make sense of.

---

## 5. What This Flow Does Not Cover

To keep this document's scope clear:

- How the operator chooses a team (workload balancing, area matching, manual judgment) is an Operations Dashboard concern, not defined here.
- What happens after the team starts work (status → "In Progress," eventual completion evidence submission) is covered by the separate *Completion Evidence Submission* and *Operator Rejection/Rework Handling* documents.
- Automatic/AI-assisted assignment is explicitly out of scope for the current phase — this flow assumes a human operator makes the choice every time.

---

## 6. Full Flow (Reference Diagram)

```
Report status: "Submitted" or "Analyzed"
                    ↓
   Operator selects a cleaning team
                    ↓
      Operator confirms assignment
                    ↓
  ── Transaction ──────────────────────
  │ ASSIGNMENTS: new row               │
  │   (report_id, team_id, assigned_at)│
  │ REPORTS: current_status →          │
  │   "Assigned"                       │
  │ STATUS_HISTORY: new row            │
  │   (status = "Assigned")            │
  ─────────────────────────────────────
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
Report appears in team's   Push notification
   active task list         sent to the team
   (query on team_id +          (FR-3.6)
    active status)
                    ↓
      Team opens the report and
   sees photo, location, category,
      description, priority score
                    ↓
      Team begins work (separate
        requirement: In-Progress
           Update Requirements)
```

---

## 7. Summary

- Assignment is always a deliberate, operator-initiated action — never automatic in the current phase.
- One transaction handles everything: creating the `ASSIGNMENTS` row, updating the report's status to `"Assigned"`, and logging the change in `STATUS_HISTORY`.
- The team's task list requires no separate delivery mechanism — it's simply a live query against the updated database state.
- The team sees the report's full existing details (photo, location, category, description, priority) immediately upon opening it — nothing new needs to be generated or fetched at this point.
- A push notification, using the same mechanism as citizen notifications, ensures the team is actively alerted rather than needing to notice the change themselves.
