# ADR-002-AUTH-TOKENS: Invitation Code and Opaque Session Tokens

- **Status**: `ACTIVE`
- **Category**: `security`
- **Impact Scope**: `auth, sessions, api`
- **Recorded By**: `system`
- **Recorded At**: `2026-09-28T17:09:22.903389+00:00`

---

## Context & Motivation
Eliminates password management, credential leakage, and credential resets while guaranteeing server-side identity validation.

## Decision
Authentication uses single-role invitation codes (e.g. DEMO-OPS, DEMO-MEM1) mapped to users. Successful login issues an opaque 64-character session token stored in PostgreSQL sessions table. Session token is required for all authenticated endpoints.

## Architectural Impact & Invariants
- Applies across: auth, sessions, api
- All team members, autonomous agents, and system implementations must comply with this decision.
