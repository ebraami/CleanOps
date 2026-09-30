# ADR-003-STORAGE-PRIVATE: Private Storage Bucket with Time-Limited Signed URLs

- **Status**: `ACTIVE`
- **Category**: `security`
- **Impact Scope**: `storage, submissions, files`
- **Recorded By**: `system`
- **Recorded At**: `2026-09-28T17:09:22.903389+00:00`

---

## Context & Motivation
Protects student privacy and graduation project intellectual property from unauthorized public web crawling.

## Decision
Student deliverable files must be uploaded to the private "submissions" Supabase bucket. Public read access is prohibited. Deliverable files are inspected via time-limited signed URLs (300-900 seconds) created on demand.

## Architectural Impact & Invariants
- Applies across: storage, submissions, files
- All team members, autonomous agents, and system implementations must comply with this decision.
