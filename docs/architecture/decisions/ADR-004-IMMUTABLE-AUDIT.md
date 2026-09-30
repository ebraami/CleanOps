# ADR-004-IMMUTABLE-AUDIT: Non-Destructive Task Lifecycle and Audit Logging

- **Status**: `ACTIVE`
- **Category**: `workflow`
- **Impact Scope**: `tasks, activity, audit`
- **Recorded By**: `system`
- **Recorded At**: `2026-09-28T17:09:22.903389+00:00`

---

## Context & Motivation
Provides complete accountability and academic verification for graduation project grading.

## Decision
Phases, work packages, tasks, and submissions are never hard-deleted. State transitions follow strict lifecycle (todo -> in_progress -> blocked -> submitted -> done/cancelled). Every state change writes an immutable row to the activity table.

## Architectural Impact & Invariants
- Applies across: tasks, activity, audit
- All team members, autonomous agents, and system implementations must comply with this decision.
