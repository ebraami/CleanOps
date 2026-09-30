# ADR-005-NOTIFICATIONS-OUTBOX: Asynchronous Telegram Outbox Pattern

- **Status**: `ACTIVE`
- **Category**: `workflow`
- **Impact Scope**: `notifications, telegram, worker`
- **Recorded By**: `system`
- **Recorded At**: `2026-09-28T17:09:22.903389+00:00`

---

## Context & Motivation
Decouples web client mutation latency from Telegram API network delays and guarantees delivery during transient outages.

## Decision
Notifications for task assignments, deadlines, reviews, and status changes are written to a durable outbox table and delivered asynchronously by the Northflank worker to Telegram. Delivered messages older than 24h are auto-expired.

## Architectural Impact & Invariants
- Applies across: notifications, telegram, worker
- All team members, autonomous agents, and system implementations must comply with this decision.
