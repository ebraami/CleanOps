#!/usr/bin/env python3
"""
CleanOps Durable Project Memory Synchronizer.
Synchronizes Architecture Decision Records (ADRs) and current project state from Supabase
into curated Git-versioned Markdown files under docs/architecture/decisions/ and docs/agent-memory/.

Zero guessing policy. Strict isolation of approved memory files.
"""

import sys
import os
import json
import subprocess
from datetime import datetime, timezone

# Ensure project root is on PYTHONPATH
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.cleanops_mcp import _supabase_request

DECISIONS_DIR = os.path.join(PROJECT_ROOT, "docs", "architecture", "decisions")
MEMORY_DIR = os.path.join(PROJECT_ROOT, "docs", "agent-memory")

def ensure_directories():
    os.makedirs(DECISIONS_DIR, exist_ok=True)
    os.makedirs(MEMORY_DIR, exist_ok=True)

def sync_adrs():
    print("[1/3] Syncing Architecture Decision Records...")
    records = _supabase_request("project_decisions", params={"select": "*", "order": "created_at.asc"})
    if isinstance(records, dict) and "error" in records:
        print(f"Error fetching decisions: {records['error']}")
        return []

    index_lines = [
        "# CleanOps Architecture Decision Records (ADRs)",
        "",
        "> Authoritative architectural and operational decisions for the CleanOps system.",
        "",
        "| Key | Title | Category | Status | Recorded By | Date |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for rec in records:
        key = rec.get("decision_key") or f"DEC-{rec.get('id')}"
        title = rec.get("title", "Untitled Decision")
        cat = rec.get("category", "general")
        status = rec.get("status", "active")
        decision = rec.get("decision", "")
        why = rec.get("context_why", "")
        scope = rec.get("impact_scope", [])
        recorded_by = rec.get("recorded_by", "system")
        created_at = rec.get("created_at", "")

        filename = f"{key}.md"
        filepath = os.path.join(DECISIONS_DIR, filename)

        scope_str = ", ".join(scope) if isinstance(scope, list) else str(scope)

        md_content = f"""# {key}: {title}

- **Status**: `{status.upper()}`
- **Category**: `{cat}`
- **Impact Scope**: `{scope_str}`
- **Recorded By**: `{recorded_by}`
- **Recorded At**: `{created_at}`

---

## Context & Motivation
{why}

## Decision
{decision}

## Architectural Impact & Invariants
- Applies across: {scope_str}
- All team members, autonomous agents, and system implementations must comply with this decision.
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        date_short = created_at[:10] if created_at else ""
        index_lines.append(f"| [{key}]({filename}) | {title} | `{cat}` | `{status}` | {recorded_by} | {date_short} |")

    readme_path = os.path.join(DECISIONS_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines) + "\n")

    print(f"  -> Exported {len(records)} ADRs to docs/architecture/decisions/")
    return records

def sync_project_state():
    print("[2/3] Syncing Project State & Workload Summary...")
    phases = _supabase_request("phases", params={"select": "*", "order": "created_at.asc"})
    wps = _supabase_request("work_packages", params={"select": "*", "order": "created_at.asc"})
    tasks = _supabase_request("tasks", params={"select": "*", "order": "created_at.asc"})
    users = _supabase_request("users", params={"select": "id,name,role"})

    if isinstance(phases, dict) and "error" in phases:
        print(f"Error fetching phases: {phases['error']}")
        return

    active_phase = next((p for p in phases if not p.get("closed_at")), phases[0] if phases else {})
    status_counts = {}
    overdue_count = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    in_progress_tasks = []
    blocked_tasks = []

    user_map = {u["id"]: u["name"] for u in users} if isinstance(users, list) else {}

    if isinstance(tasks, list):
        for t in tasks:
            st = t.get("status", "todo")
            status_counts[st] = status_counts.get(st, 0) + 1
            deadline = t.get("deadline")
            if deadline and deadline < now_iso and st not in ("done", "cancelled"):
                overdue_count += 1
            if st == "in_progress":
                in_progress_tasks.append(t)
            elif st == "blocked":
                blocked_tasks.append(t)

    # 1. project-state.md
    state_md = f"""# CleanOps Current Project State

> Auto-generated durable memory snapshot.
> Last synchronized: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

## Active Phase
- **Phase ID**: `{active_phase.get('id', 'N/A')}`
- **Code / Name**: **{active_phase.get('code', '')} - {active_phase.get('name', 'N/A')}**
- **Deadline**: `{active_phase.get('deadline', 'N/A')}`
- **Status**: `{'OPEN' if not active_phase.get('closed_at') else 'CLOSED'}`

## Task Delivery Metrics
- **Total Tasks**: {len(tasks) if isinstance(tasks, list) else 0}
- **Completed (Done)**: {status_counts.get('done', 0)}
- **In Progress**: {status_counts.get('in_progress', 0)}
- **To-Do**: {status_counts.get('todo', 0)}
- **Blocked**: {status_counts.get('blocked', 0)}
- **Cancelled**: {status_counts.get('cancelled', 0)}
- **Overdue Count**: {overdue_count}

## Work Packages
| ID | Name | Priority | Phase |
| :--- | :--- | :--- | :--- |
"""
    if isinstance(wps, list):
        for wp in wps:
            state_md += f"| `{wp.get('id')}` | {wp.get('name')} | `{wp.get('priority')}` | `{wp.get('phase_id')}` |\n"

    with open(os.path.join(MEMORY_DIR, "project-state.md"), "w", encoding="utf-8") as f:
        f.write(state_md)

    # 2. active-work.md
    active_md = f"""# CleanOps Active Work & Operational Context

> Snapshot of currently active engineering tasks and blockers.
> Last synchronized: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

## In-Progress Tasks ({len(in_progress_tasks)})
| Task ID | Title | Priority | Assignee | Deadline |
| :--- | :--- | :--- | :--- | :--- |
"""
    for t in in_progress_tasks:
        owner = user_map.get(t.get("owner_id"), t.get("owner_id") or "Unassigned")
        active_md += f"| `{t.get('id')}` | {t.get('title')} | `{t.get('priority')}` | {owner} | {t.get('deadline') or 'None'} |\n"

    active_md += f"\n## Blockers ({len(blocked_tasks)})\n"
    if blocked_tasks:
        for t in blocked_tasks:
            active_md += f"- **Task `{t.get('id')}` ({t.get('title')})**: {t.get('blocker_reason', 'Unspecified reason')}\n"
    else:
        active_md += "No tasks are currently marked as blocked.\n"

    with open(os.path.join(MEMORY_DIR, "active-work.md"), "w", encoding="utf-8") as f:
        f.write(active_md)

    # 3. system-context.md
    context_md = """# CleanOps System & Architectural Context

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
"""
    with open(os.path.join(MEMORY_DIR, "system-context.md"), "w", encoding="utf-8") as f:
        f.write(context_md)

    # 4. disaster-recovery.md
    dr_md = """# CleanOps Disaster Recovery Runbook

> Step-by-step restoration runbook if the Azure VM is lost or migrated.

## Prerequisites
- Clean Ubuntu 22.04 or 24.04 VM (or local Linux machine).
- SSH access with sudo privileges.
- GitHub access to `https://github.com/ebraami/CleanOps.git`.
- `SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_URL` from secure password vault.

## Step-by-Step Restoration Procedure
1. **Clone Repository**:
   ```bash
   sudo git clone https://github.com/ebraami/CleanOps.git /cleanops
   sudo chown -R $USER:$USER /cleanops
   cd /cleanops
   ```

2. **Restore Secrets**:
   ```bash
   cp /cleanops/.env.example /cleanops/.env
   chmod 600 /cleanops/.env
   # Edit /cleanops/.env and insert the real SUPABASE_SERVICE_ROLE_KEY
   ```

3. **Install Antigravity CLI**:
   ```bash
   curl -fsSL https://antigravity.google/install.sh | bash
   agy  # Authenticate with Google account
   ```

4. **Deploy Systemd Services & MCP Config**:
   ```bash
   mkdir -p ~/.config/systemd/user ~/.gemini/config
   cp /cleanops/deploy/systemd/* ~/.config/systemd/user/
   cp /cleanops/deploy/mcp/mcp_config.json.template ~/.gemini/config/mcp_config.json
   systemctl --user daemon-reload
   systemctl --user enable --now cleanops-gateway.service antigravity-cli-daemon.service
   ```

5. **(Optional) Restore Conversation History Snapshot**:
   If an offsite encrypted snapshot is available:
   ```bash
   /cleanops/scripts/restore_session_state.sh /path/to/cleanops_session_backup.tar.gz.enc
   ```

6. **Verify Recovery**:
   ```bash
   curl -s http://127.0.0.1:8080/health
   python3 /cleanops/scripts/sync_project_memory.py
   agy -p "Verify system status and active phase"
   ```
"""
    with open(os.path.join(MEMORY_DIR, "disaster-recovery.md"), "w", encoding="utf-8") as f:
        f.write(dr_md)

    print("  -> Exported project-state.md, active-work.md, system-context.md, disaster-recovery.md")

def safe_git_commit():
    """
    STRICT COMMIT SCOPE:
    Only stages and commits approved durable memory and architecture files.
    NEVER touches uncommitted code or working tree changes.
    """
    print("[3/3] Checking Git status for designated memory files...")
    
    allowed_paths = [
        "docs/architecture/decisions",
        "docs/agent-memory"
    ]
    
    # Check if there are changes in allowed paths
    status = subprocess.run(["git", "status", "--porcelain", "--"] + allowed_paths,
                            cwd=PROJECT_ROOT, capture_output=True, text=True)
    
    if not status.stdout.strip():
        print("  -> No memory changes to commit. Working tree clean for memory files.")
        return

    print("  -> Staging designated memory files...")
    subprocess.run(["git", "add", "--"] + allowed_paths, cwd=PROJECT_ROOT, check=True)
    
    # Commit
    commit_msg = f"chore(memory): sync durable agent memory and ADRs ({datetime.now(timezone.utc).strftime('%Y-%m-%d')}) [skip ci]"
    res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=PROJECT_ROOT, capture_output=True, text=True)
    print("  -> Git commit completed:", res.stdout.strip().split("\n")[0])

if __name__ == "__main__":
    ensure_directories()
    sync_adrs()
    sync_project_state()
    if "--commit" in sys.argv:
        safe_git_commit()
    print("Durable project memory sync complete.")
