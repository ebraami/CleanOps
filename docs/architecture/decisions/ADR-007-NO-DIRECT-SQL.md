# ADR-007-NO-DIRECT-SQL: Zero Arbitrary SQL Authority for AI Agents

- **Status**: `ACTIVE`
- **Category**: `security`
- **Impact Scope**: `database, security, agent`
- **Recorded By**: `system`
- **Recorded At**: `2026-09-28T17:09:22.903389+00:00`

---

## Context & Motivation
Guarantees database relational integrity and prevents prompt injection attacks from compromising database tables.

## Decision
The Boss Agent and external workers are forbidden from executing arbitrary SQL statements directly. All interactions must proceed through typed Edge Function RPC endpoints authenticated with x-bot-secret.

## Architectural Impact & Invariants
- Applies across: database, security, agent
- All team members, autonomous agents, and system implementations must comply with this decision.
