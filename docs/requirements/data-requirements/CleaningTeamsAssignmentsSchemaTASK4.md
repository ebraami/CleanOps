# Cleaning Teams & Assignments Schema

Define the requirements for the CLEANING_TEAMS and ASSIGNMENTS tables — team identity/area, and how a report is linked to a team with assignment and completion timestamps.

---

## 1. CLEANING_TEAMS Table

Stores the identity and coverage area of each cleaning team/operator group that can be assigned reports.

| Field | Type | Description | Constraints |
|---|---|---|---|
| `team_id` | UUID / Integer (PK) | Unique identifier for the cleaning team. | Primary Key, auto-generated |
| `team_name` | String | Display name of the team (e.g., "Zone 3 Cleaning Crew"). | Required |
| `coverage_area` | String / GeoJSON polygon | The geographic zone or district the team is responsible for. | Required |
| `contact_phone` | String | Primary contact number for the team lead. | Optional |
| `contact_email` | String | Contact email for notifications/escalations. | Optional |
| `status` | Enum (`active`, `inactive`, `suspended`) | Whether the team is currently available to receive new assignments. | Required, default: `active` |
| `member_count` | Integer | Number of members in the team (for capacity planning). | Optional |
| `created_at` | Timestamp | When the team record was created. | Required, auto-set |
| `updated_at` | Timestamp | Last time the team's details were modified. | Required, auto-updated |

---

## 2. ASSIGNMENTS Table

Stores the link between a report and the cleaning team responsible for it, along with the lifecycle timestamps of that assignment.

| Field | Type | Description | Constraints |
|---|---|---|---|
| `assignment_id` | UUID / Integer (PK) | Unique identifier for the assignment record. | Primary Key, auto-generated |
| `report_id` | UUID / Integer (FK) | The report this assignment refers to. | Required, Foreign Key → `REPORTS.report_id` |
| `team_id` | UUID / Integer (FK) | The cleaning team assigned to this report. | Required, Foreign Key → `CLEANING_TEAMS.team_id` |
| `assigned_by` | UUID / Integer (FK) | The operator who made the assignment. | Required, Foreign Key → `OPERATORS.operator_id` |
| `assigned_at` | Timestamp | The moment the report was assigned to the team. This is the trigger point referenced by the notification flow. | Required, auto-set on creation |
| `status` | Enum (`assigned`, `in_progress`, `completed`, `reassigned`, `cancelled`) | Current state of this specific assignment. | Required, default: `assigned` |
| `started_at` | Timestamp | When the team marked the work as started (optional, if tracked). | Optional |
| `completed_at` | Timestamp | When the team marked the assignment as completed. | Optional (set on completion) |
| `completion_notes` | String | Optional notes or evidence reference left by the team on completion. | Optional |
| `completion_image_url` | String | Reference to the "before/after" completion evidence image, if uploaded. | Optional |

---

## 3. Relationship to REPORTS

- **One REPORT → many ASSIGNMENTS (one active at a time):** A single report can have multiple assignment records over its lifetime (e.g., if reassigned to a different team), but only one assignment should be in `assigned` or `in_progress` status at any given time for a given report. Historical/cancelled assignments remain in the table for audit purposes.
- **One CLEANING_TEAM → many ASSIGNMENTS:** A team can be linked to many assignments over time (its full workload history).
- **REPORTS table is not modified structurally by this schema** — the link is maintained entirely through `ASSIGNMENTS.report_id`, keeping report data and assignment/workflow data separated. The report's own `status` field (e.g., "new," "assigned," "resolved") is expected to be kept in sync with the corresponding assignment's status via the backend logic, not duplicated as separate source-of-truth data.

**Entity relationship summary:**
```
REPORTS (1) ────< ASSIGNMENTS (many) >──── (1) CLEANING_TEAMS
                        │
                        └──── (many) >──── (1) OPERATORS  (assigned_by)
```

---

## 4. Notes

- `assigned_at` is the timestamp referenced by the notification-timeliness requirement (push notification to the team must be sent within the defined delay window from this point).
- Keeping `ASSIGNMENTS` as a separate table (rather than storing team/assignment fields directly on `REPORTS`) allows a full history of reassignments and completion records to be preserved, which supports the analytics and hotspot-detection features described in the project proposal.
