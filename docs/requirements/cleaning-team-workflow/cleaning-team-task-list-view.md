# Cleaning Team Functions — Task List View

**Status:** In Progress
**Priority:** Medium

Define what a cleaning team sees when they have multiple assigned tasks — how tasks are ordered or grouped (e.g., by priority score, by area), and what counts as an "open" vs. "completed" task from their view.

---

## 1. Task List Display

**Description:**
When a cleaning team member opens the app, they see a single consolidated list of all reports currently assigned to their team, rather than having to search or filter manually across the full report database.

**Acceptance Condition:**
The task list shows, for each assigned report: category, location (address/area name), priority level, time since assignment, and current status. The list refreshes automatically when a new task is assigned or an existing one is updated.

---

## 2. Task Ordering

**Description:**
Tasks are automatically ordered so that the most urgent and time-sensitive work appears first, without requiring the team to manually sort or prioritize.

**Acceptance Condition:**
Tasks are sorted by **priority score** first (highest priority at the top), and, for tasks with equal priority, by **assignment time** (oldest first). The team can switch the sort order to **group by area** (all tasks in the same zone shown together) to support efficient route planning, but priority-first is the default view.

---

## 3. Task Grouping by Area

**Description:**
The system offers an alternative grouped view so a team can batch nearby tasks together and reduce travel time between locations.

**Acceptance Condition:**
When "Group by area" is selected, tasks are clustered under their area/zone name, with a count of open tasks per area. Within each area group, tasks still follow priority-first ordering.

---

## 4. "Open" vs. "Completed" Definition

**Description:**
The system defines a clear, consistent boundary between a task that still requires action from the cleaning team and one that has been finished, so the team's active list only shows work still pending.

**Acceptance Condition:**
A task is considered **"Open"** (and remains in the active task list) while its status is **Assigned** or **In Progress**.
A task is considered **"Completed"** and is automatically removed from the active task list once the team marks it as **Resolved** (after uploading completion/"after" evidence, as required by the report lifecycle).
Completed tasks remain accessible in a separate "Completed" or "History" view but do not appear in the default active task list.

---

## 5. Multiple Active Assignments

**Description:**
When a team has more than one open task at the same time, the interface makes it clear how many tasks are pending and allows quick navigation between them.

**Acceptance Condition:**
The task list view displays a total count of open tasks at the top (e.g., "5 Open Tasks"). Each task in the list can be tapped to open its full details (photo, location, description) without leaving the list view (e.g., via expandable card or detail screen with a back action).

---

> **Note:** The priority score referenced above is the same score defined in the Operator Functions — Analytics & Monitoring requirements. This document defines how that score affects the cleaning team's own view, not how the score itself is calculated.
