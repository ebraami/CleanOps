# ADR-006-AUTONOMOUS-BOSS-AGENT: Persistent Autonomous Boss Agent Authority

- **Status**: `ACTIVE`
- **Category**: `architecture`
- **Impact Scope**: `ai, worker, reviews`
- **Recorded By**: `system`
- **Recorded At**: `2026-09-28T17:09:22.903389+00:00`

---

## Context & Motivation
Relieves human project leadership from manual operational review bottlenecks while ensuring deep cross-member architectural consistency.

## Decision
The Boss Agent runs 24/7 on Northflank as the primary reviewer and technical lead. It investigates submissions across task contracts, ADRs, database DDL, repository source code, and task dependencies before settling reviews.

## Architectural Impact & Invariants
- Applies across: ai, worker, reviews
- All team members, autonomous agents, and system implementations must comply with this decision.
