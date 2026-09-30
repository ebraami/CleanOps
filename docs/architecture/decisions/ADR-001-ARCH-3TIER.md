# ADR-001-ARCH-3TIER: 3-Tier Serverless Architecture

- **Status**: `ACTIVE`
- **Category**: `architecture`
- **Impact Scope**: `frontend, backend, deployment`
- **Recorded By**: `system`
- **Recorded At**: `2026-09-28T17:09:22.903389+00:00`

---

## Context & Motivation
Eliminates VPS maintenance overhead, ensures zero-cost scaling, and isolates client execution completely from database credentials.

## Decision
CleanOps is architected into 3 tiers: Static SPA Frontend (InfinityFree/Static HTML/JS), Serverless Edge Function API (Supabase /api), and PostgreSQL Database + Storage. No continuous stateful application server is maintained for web clients.

## Architectural Impact & Invariants
- Applies across: frontend, backend, deployment
- All team members, autonomous agents, and system implementations must comply with this decision.
