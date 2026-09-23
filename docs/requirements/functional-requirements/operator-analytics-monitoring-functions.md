# Operator Functions — Analytics & Monitoring

**Status:** In Progress
**Priority:** Medium

Define the functionality for monitoring hotspots, recurring reports, area burden, team workload, open tasks, SLA ageing, and operational analytics.

---

## 1. Hotspot Detection

**Description:**
The system automatically identifies locations with a high frequency of repeated reports within a defined time period, displaying them visually on the operations map as areas requiring urgent attention.

**Acceptance Condition:**
A location is automatically flagged as a "Hotspot" when it receives 5 or more reports within a 30-day period. Hotspots are displayed on the map with a distinct marker/color, along with a report count.

---

## 2. Recurring Reports

**Description:**
The system flags multiple reports submitted about the same location or issue as potential duplicates and suggests them to the operator for review, instead of merging them automatically. This keeps the final decision on grouping reports in the hands of a human operator.

**Acceptance Condition:**
Reports within a 50-meter radius submitted within 7 days of each other are flagged and suggested to the operator as potential duplicates, with a visible "recurrence count" indicator. The operator reviews the suggestion and manually confirms whether to merge them under one primary report. No automatic merging or grouping of reports occurs without operator confirmation.

---

## 3. Area Burden

**Description:**
The system calculates and displays the load (number of open reports) per geographic area, helping supervisors distribute cleaning teams fairly.

**Acceptance Condition:**
The dashboard displays a ranked list of areas by number of open reports, updating automatically whenever a report is created or closed.

---

## 4. Team Workload

**Description:**
The system displays the number of tasks currently assigned to each cleaning team, allowing supervisors to balance new report assignments.

**Acceptance Condition:**
The dashboard shows, per team: number of open tasks, number of tasks completed today, and team availability status, updated in real time as task status changes.

---

## 5. Open Tasks

**Description:**
The system displays a unified list of all unresolved reports, sorted by priority, serving as a quick reference for the operations team.

**Acceptance Condition:**
The "Open Tasks" list shows all reports with status (Open / In Progress), automatically sorted with the oldest and highest-priority reports appearing first. Closed reports are automatically excluded.

---

## 6. SLA Ageing

**Description:**
The system tracks the elapsed time since each report was received and visually flags reports approaching or exceeding the allowed response time (SLA).

**Acceptance Condition:**
A report is marked yellow (warning) after remaining open for more than 24 hours, and red (overdue) after 48 hours. A time counter is displayed next to each report.

---

> **Note:** The numeric thresholds above (5 reports, 24/48 hours, etc.) are initial working assumptions and can be adjusted based on real usage data after launch.
