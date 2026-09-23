# STATUS_HISTORY (Audit Trail) Schema

## 1. Purpose

The `STATUS_HISTORY` table is used to keep a history of all status changes for a report.

It helps the system know what the status of a report was, when it changed, and how the report moved from one status to another.

---

## 2. STATUS_HISTORY Fields

| Field | Description | Required |
|---|---|---|
| `history_id` | A unique ID for each history record. | Yes |
| `report_id` | The ID of the report related to this status change. | Yes |
| `status` | The new status of the report after the change. | Yes |
| `changed_at` | The exact date and time when the status changed. | Yes |

### Main Required Fields

The most important fields for the status history are:

- `status`: stores the new status.
- `changed_at`: stores the date and time of the change.

The `report_id` connects the history record to the correct report, and `history_id` identifies each history record.

---

## 3. When Should a Log Entry Be Created?

A new record must be created in `STATUS_HISTORY` whenever the status of a report changes.

For example:

- `Open` → `In Progress`
- `In Progress` → `Resolved`
- `Resolved` → `Closed`

Each of these changes must create a new history record.

If the status does not change, a new status history record is not needed.

---

## 4. Example

For a report with ID `R001`, the history could look like this:

| history_id | report_id | status | changed_at |
|---|---|---|---|
| 1 | R001 | Open | 2026-09-23 10:00 |
| 2 | R001 | In Progress | 2026-09-23 10:30 |
| 3 | R001 | Resolved | 2026-09-23 12:00 |
| 4 | R001 | Closed | 2026-09-23 12:30 |

This gives a complete history of the report status.

---

## 5. Response-Time Analysis

The `changed_at` field can be used to calculate response time.

For example, if a report is created at 10:00 and changes to `In Progress` at 10:30, the response time is 30 minutes.

The status history allows the system to compare the time between status changes.

---

## 6. Resolution Analysis

The status history can also be used to calculate how long it takes to resolve a report.

For example, if a report changes to `In Progress` at 10:30 and changes to `Resolved` at 12:00, the time between these changes is 1 hour and 30 minutes.

This information can be used to analyze the time needed to resolve reports and the resolution rate.

---

## 7. Audit Trail

The `STATUS_HISTORY` table provides an audit trail for reports.

It keeps the history instead of only storing the current status. This makes it possible to see the status changes and the exact time of each change.

---

## 8. Summary

The `STATUS_HISTORY` table must record every status change of a report.

The main information that must be stored is:

- The report ID.
- The new status.
- The exact date and time of the change.
- A unique ID for each history record.

A new log entry must always be created when the report status changes. This history can then be used for response-time and resolution analysis.
