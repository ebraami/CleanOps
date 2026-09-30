# CleanOps System & Architectural Context

> Permanent architectural reference for CleanOps Boss Agent.

## Core Architectural Invariants
1. **3-Tier Serverless Architecture (ADR-001)**:
   - **Frontend**: Static SPA (HTML/JS/CSS).
   - **API Layer**: Serverless Supabase Edge Functions (`/api`).
   - **Database**: PostgreSQL on Supabase + Private Storage Bucket (`reports-media`).
2. **Authority & Role Separation (GEMINI.md)**:
   - **Team Leader (`lead`)**: Project management, work packages, task creation, task assignments, ADR decisions.
   - **Team Member (`member`)**: Progress logs, blocker reports, deliverable submissions. Cannot create/reassign tasks.
3. **Agent Integration Topology**:
   - CleanOps Boss runs as `agy 1.2.14` CLI runtime on Azure VM.
   - CleanOps Gateway (`tools/cleanops_gateway.py`) listens on port 8080 and streams agent turns via SSE to the Portal.
   - MCP Server (`tools/cleanops_mcp.py`) exposes domain tools via stdio to `agy`.
4. **Zero Guessing Policy**:
   - Never guess task IDs, user IDs, or work package IDs.
   - Always query before mutating or assigning.
