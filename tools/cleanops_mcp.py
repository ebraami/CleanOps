#!/usr/bin/env python3
"""
CleanOps MCP Server (Model Context Protocol).
Provides CleanOps domain tools to the real Antigravity agent runtime:
- cleanops_get_project_health
- cleanops_get_workload
- cleanops_list_tasks
- cleanops_get_task_details
- cleanops_create_task (RBAC enforced)
- cleanops_assign_task (RBAC enforced)
- cleanops_get_project_decisions
- cleanops_get_project_requirements

Zero external runtime dependencies. Runs with standard library Python 3.10+.
"""

import sys
import os
import json
import secrets
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

def _load_env_file():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env_file()

if not os.environ.get("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://taeisngdqywpnmzbjotk.supabase.co"
if not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
    sys.stderr.write("[ERROR] SUPABASE_SERVICE_ROLE_KEY is not set in environment or /cleanops/.env\n")

def _supabase_request(endpoint: str, method: str = "GET", body: dict = None, params: dict = None):
    base_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    url = f"{base_url}/rest/v1/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if method in ("POST", "PATCH"):
        headers["Prefer"] = "return=representation"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return {"error": f"HTTP {e.code}: {err_body}"}
    except Exception as e:
        return {"error": str(e)}

# ---------------------------------------------------------------------------
# RBAC Validation
# ---------------------------------------------------------------------------
def _check_user_role(caller_user_id: str) -> dict:
    if not caller_user_id:
        return {"ok": False, "error": "Missing caller_user_id. Cannot authenticate operation."}
    users = _supabase_request("users", params={"id": f"eq.{caller_user_id}", "select": "id,name,role"})
    if isinstance(users, dict) and "error" in users:
        return {"ok": False, "error": f"Database error verifying caller: {users['error']}"}
    if not users or not isinstance(users, list) or len(users) == 0:
        return {"ok": False, "error": f"Caller user ID '{caller_user_id}' does not exist in project users."}
    user = users[0]
    return {"ok": True, "role": user.get("role", "member"), "name": user.get("name", "")}

# ---------------------------------------------------------------------------
# CleanOps Domain Tools Implementation
# ---------------------------------------------------------------------------

def tool_get_project_health(args: dict) -> dict:
    phases = _supabase_request("phases", params={"select": "id,code,name,deadline,closed_at"})
    wps = _supabase_request("work_packages", params={"select": "id,name,phase_id,priority"})
    tasks = _supabase_request("tasks", params={"select": "id,title,status,deadline,owner_id,work_package_id"})
    blockers = _supabase_request("blockers", params={"status": "eq.open", "select": "id,task_id,description"})

    if isinstance(phases, dict) and "error" in phases:
        return {"error": f"Could not load phases: {phases['error']}"}
    if isinstance(tasks, dict) and "error" in tasks:
        return {"error": f"Could not load tasks: {tasks['error']}"}

    status_counts = {"todo": 0, "in_progress": 0, "submitted": 0, "done": 0, "blocked": 0, "cancelled": 0}
    overdue_count = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    task_list = tasks if isinstance(tasks, list) else []
    for t in task_list:
        st = t.get("status", "todo")
        status_counts[st] = status_counts.get(st, 0) + 1
        dl = t.get("deadline")
        if dl and dl < now_iso and st not in ("done", "cancelled"):
            overdue_count += 1

    open_phases = [p for p in (phases if isinstance(phases, list) else []) if not p.get("closed_at")]

    return {
        "status": "healthy" if status_counts.get("blocked", 0) == 0 and overdue_count == 0 else "needs_attention",
        "active_phase": open_phases[0] if open_phases else None,
        "total_phases": len(phases) if isinstance(phases, list) else 0,
        "total_work_packages": len(wps) if isinstance(wps, list) else 0,
        "work_packages": wps if isinstance(wps, list) else [],
        "tasks_summary": {
            "total": len(task_list),
            "status_counts": status_counts,
            "overdue_tasks_count": overdue_count
        },
        "open_blockers_count": len(blockers) if isinstance(blockers, list) else 0,
        "open_blockers": blockers if isinstance(blockers, list) else []
    }

def tool_get_workload(args: dict) -> dict:
    target_user_id = args.get("user_id")
    users_params = {"select": "id,name,role"}
    if target_user_id:
        users_params["id"] = f"eq.{target_user_id}"
    
    users = _supabase_request("users", params=users_params)
    tasks = _supabase_request("tasks", params={"select": "id,title,status,deadline,owner_id,work_package_id"})

    if isinstance(users, dict) and "error" in users:
        return {"error": users["error"]}
    if isinstance(tasks, dict) and "error" in tasks:
        return {"error": tasks["error"]}

    user_list = users if isinstance(users, list) else []
    task_list = tasks if isinstance(tasks, list) else []

    workloads = []
    for u in user_list:
        uid = u.get("id")
        user_tasks = [t for t in task_list if t.get("owner_id") == uid]
        active = [t for t in user_tasks if t.get("status") in ("todo", "in_progress", "submitted")]
        in_prog = [t for t in user_tasks if t.get("status") == "in_progress"]
        delivered = [t for t in user_tasks if t.get("status") == "done"]
        
        # Overload rule: > 3 active in_progress tasks
        is_overloaded = len(in_prog) >= 3

        workloads.append({
            "user_id": uid,
            "name": u.get("name"),
            "role": u.get("role"),
            "active_tasks_count": len(active),
            "in_progress_count": len(in_prog),
            "delivered_count": len(delivered),
            "is_overloaded": is_overloaded,
            "tasks": active
        })

    return {
        "member_count": len(workloads),
        "workloads": workloads
    }

def tool_list_tasks(args: dict) -> dict:
    params = {"select": "id,title,status,priority,deadline,owner_id,work_package_id,progress,created_at"}
    if args.get("status"):
        params["status"] = f"eq.{args['status']}"
    if args.get("owner_id"):
        params["owner_id"] = f"eq.{args['owner_id']}"
    if args.get("work_package_id"):
        params["work_package_id"] = f"eq.{args['work_package_id']}"
    
    res = _supabase_request("tasks", params=params)
    if isinstance(res, dict) and "error" in res:
        return {"error": res["error"]}

    task_list = res if isinstance(res, list) else []
    query = (args.get("query") or "").strip().lower()
    if query:
        task_list = [t for t in task_list if query in t.get("title", "").lower() or query in t.get("id", "").lower()]

    return {"count": len(task_list), "tasks": task_list}

def tool_get_task_details(args: dict) -> dict:
    task_id = args.get("task_id")
    if not task_id:
        return {"error": "Missing task_id"}
    
    tasks = _supabase_request("tasks", params={"id": f"eq.{task_id}", "select": "*"})
    if isinstance(tasks, dict) and "error" in tasks:
        return {"error": tasks["error"]}
    if not tasks or not isinstance(tasks, list):
        return {"error": f"Task '{task_id}' not found."}
    
    task = tasks[0]
    submissions = _supabase_request("submissions", params={"task_id": f"eq.{task_id}", "select": "*", "order": "at.desc"})
    blockers = _supabase_request("blockers", params={"task_id": f"eq.{task_id}", "select": "*"})

    return {
        "task": task,
        "submissions": submissions if isinstance(submissions, list) else [],
        "blockers": blockers if isinstance(blockers, list) else []
    }

def tool_create_task(args: dict) -> dict:
    caller_id = args.get("caller_user_id")
    auth = _check_user_role(caller_id)
    if not auth["ok"]:
        return {"ok": False, "error": auth["error"]}
    
    # RBAC: only lead, ops, or coord can create tasks
    if auth["role"] not in ("lead", "ops", "coord"):
        return {
            "ok": False,
            "error": f"Permission denied: User '{auth['name']}' has role '{auth['role']}'. Only Team Leader (lead) or Coordinator can create tasks."
        }

    title = (args.get("title") or "").strip()
    if not title:
        return {"ok": False, "error": "Missing required field: title"}
    
    wp_id = args.get("work_package_id")
    if not wp_id:
        # Default to first active work package
        wps = _supabase_request("work_packages", params={"select": "id,name", "limit": "1"})
        if isinstance(wps, list) and len(wps) > 0:
            wp_id = wps[0]["id"]
        else:
            return {"ok": False, "error": "No work packages exist in project. Cannot file task."}

    owner_id = args.get("owner_id")
    if not owner_id:
        owner_id = caller_id

    # Verify owner exists
    owner_check = _supabase_request("users", params={"id": f"eq.{owner_id}", "select": "id,name"})
    if not owner_check or not isinstance(owner_check, list) or len(owner_check) == 0:
        return {"ok": False, "error": f"Assigned owner '{owner_id}' does not exist in project users."}

    # Generate task id: T_<6 hex>
    new_id = f"T_{secrets.token_hex(3)}"
    now_iso = datetime.now(timezone.utc).isoformat()

    payload = {
        "id": new_id,
        "work_package_id": wp_id,
        "title": title,
        "description": args.get("description", ""),
        "deliverable": args.get("deliverable", ""),
        "owner_id": owner_id,
        "created_by": caller_id,
        "status": "todo",
        "priority": args.get("priority", "medium"),
        "deadline": args.get("deadline"),
        "progress": 0,
        "created_at": now_iso,
        "updated_at": now_iso
    }

    res = _supabase_request("tasks", method="POST", body=payload)
    if isinstance(res, dict) and "error" in res:
        return {"ok": False, "error": f"Database insertion failed: {res['error']}"}

    created = res[0] if isinstance(res, list) and len(res) > 0 else payload
    return {
        "ok": True,
        "task_id": new_id,
        "title": title,
        "owner_id": owner_id,
        "work_package_id": wp_id,
        "message": f"Task '{title}' ({new_id}) successfully created and assigned to {owner_id}."
    }

def tool_assign_task(args: dict) -> dict:
    caller_id = args.get("caller_user_id")
    auth = _check_user_role(caller_id)
    if not auth["ok"]:
        return {"ok": False, "error": auth["error"]}

    # RBAC: only lead, ops, or coord can assign/reassign tasks
    if auth["role"] not in ("lead", "ops", "coord"):
        return {
            "ok": False,
            "error": f"Permission denied: User '{auth['name']}' has role '{auth['role']}'. Only Team Leader (lead) can assign tasks."
        }

    task_id = args.get("task_id")
    if not task_id:
        return {"ok": False, "error": "Missing task_id"}

    owner_id = args.get("owner_id")
    if not owner_id:
        return {"ok": False, "error": "Missing owner_id"}

    # Verify task exists
    tasks = _supabase_request("tasks", params={"id": f"eq.{task_id}", "select": "id,title,owner_id"})
    if isinstance(tasks, dict) and "error" in tasks:
        return {"ok": False, "error": tasks["error"]}
    if not tasks or not isinstance(tasks, list) or len(tasks) == 0:
        return {"ok": False, "error": f"Task '{task_id}' does not exist in database."}

    # Verify owner exists
    users = _supabase_request("users", params={"id": f"eq.{owner_id}", "select": "id,name,role"})
    if isinstance(users, dict) and "error" in users:
        return {"ok": False, "error": users["error"]}
    if not users or not isinstance(users, list) or len(users) == 0:
        return {"ok": False, "error": f"Target user '{owner_id}' does not exist in project users."}

    target_user = users[0]
    task = tasks[0]

    now_iso = datetime.now(timezone.utc).isoformat()
    patch_res = _supabase_request(
        "tasks",
        method="PATCH",
        params={"id": f"eq.{task_id}"},
        body={"owner_id": owner_id, "updated_at": now_iso}
    )
    if isinstance(patch_res, dict) and "error" in patch_res:
        return {"ok": False, "error": f"Database update failed: {patch_res['error']}"}

    return {
        "ok": True,
        "task_id": task_id,
        "title": task.get("title"),
        "previous_owner_id": task.get("owner_id"),
        "new_owner_id": owner_id,
        "new_owner_name": target_user.get("name"),
        "message": f"Task '{task.get('title')}' ({task_id}) successfully assigned to {target_user.get('name')} ({owner_id})."
    }

def tool_get_project_decisions(args: dict) -> dict:
    params = {"select": "decision_key,title,category,status,decision,context_why,impact_scope,recorded_by,created_at"}
    if args.get("category"):
        params["category"] = f"eq.{args['category']}"
    if args.get("status"):
        params["status"] = f"eq.{args['status']}"
    else:
        params["status"] = "eq.active"

    res = _supabase_request("project_decisions", params=params)
    if isinstance(res, dict) and "error" in res:
        return {"error": res["error"]}
    return {"count": len(res) if isinstance(res, list) else 0, "decisions": res}

def tool_get_project_requirements(args: dict) -> dict:
    params = {"select": "req_key,title,statement,rationale,work_package_id,status,version,tags"}
    if args.get("work_package_id"):
        params["work_package_id"] = f"eq.{args['work_package_id']}"
    if args.get("status"):
        params["status"] = f"eq.{args['status']}"

    res = _supabase_request("project_requirements", params=params)
    if isinstance(res, dict) and "error" in res:
        return {"error": res["error"]}
    return {"count": len(res) if isinstance(res, list) else 0, "requirements": res}

# ---------------------------------------------------------------------------
# Tool Schemas for MCP tools/list
# ---------------------------------------------------------------------------

MCP_TOOLS = [
    {
        "name": "cleanops_get_project_health",
        "description": "Retrieve CleanOps project health, active phase, work packages, task breakdown by status, overdue tasks, and open blockers.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "cleanops_get_workload",
        "description": "Retrieve team member workload, active task count, in-progress tasks, and overload indicators (>3 active tasks).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Optional user ID (e.g. U_MEM, U_TL) to inspect specific member workload."
                }
            },
            "required": []
        }
    },
    {
        "name": "cleanops_list_tasks",
        "description": "Query CleanOps tasks by status, owner_id, work_package_id, or title substring query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["todo", "in_progress", "submitted", "done", "blocked", "cancelled"]},
                "owner_id": {"type": "string", "description": "Filter by assigned member user ID"},
                "work_package_id": {"type": "string", "description": "Filter by work package ID"},
                "query": {"type": "string", "description": "Search term matching title or task ID"}
            },
            "required": []
        }
    },
    {
        "name": "cleanops_get_task_details",
        "description": "Get complete task information including deliverables, submissions, review status, and blockers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "The exact task ID (e.g. T_1a8c49)"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "cleanops_create_task",
        "description": "Create a new CleanOps task under a work package. Requires caller_user_id with Team Leader ('lead') role.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "caller_user_id": {"type": "string", "description": "User ID of the caller (must be 'lead' or 'ops')"},
                "title": {"type": "string", "description": "Clear title of the task"},
                "work_package_id": {"type": "string", "description": "Target work package ID"},
                "owner_id": {"type": "string", "description": "User ID of assigned team member"},
                "deadline": {"type": "string", "description": "ISO timestamp deadline (e.g. 2026-10-15T18:00:00Z)"},
                "description": {"type": "string", "description": "Detailed task description"},
                "deliverable": {"type": "string", "description": "Deliverable specification"}
            },
            "required": ["caller_user_id", "title"]
        }
    },
    {
        "name": "cleanops_assign_task",
        "description": "Assign or reassign an existing CleanOps task to a team member. Requires caller_user_id with Team Leader ('lead') role.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "caller_user_id": {"type": "string", "description": "User ID of the caller performing the assignment"},
                "task_id": {"type": "string", "description": "Exact task ID to assign"},
                "owner_id": {"type": "string", "description": "Target user ID of the team member receiving the task"}
            },
            "required": ["caller_user_id", "task_id", "owner_id"]
        }
    },
    {
        "name": "cleanops_get_project_decisions",
        "description": "Retrieve project Architecture Decision Records (ADRs) and structural policies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by ADR category"},
                "status": {"type": "string", "description": "Filter by status (default 'active')"}
            },
            "required": []
        }
    },
    {
        "name": "cleanops_get_project_requirements",
        "description": "Retrieve authoritative project requirements and acceptance criteria.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "work_package_id": {"type": "string", "description": "Filter by work package ID"},
                "status": {"type": "string", "description": "Filter by status"}
            },
            "required": []
        }
    }
]

DISPATCH = {
    "cleanops_get_project_health": tool_get_project_health,
    "cleanops_get_workload": tool_get_workload,
    "cleanops_list_tasks": tool_list_tasks,
    "cleanops_get_task_details": tool_get_task_details,
    "cleanops_create_task": tool_create_task,
    "cleanops_assign_task": tool_assign_task,
    "cleanops_get_project_decisions": tool_get_project_decisions,
    "cleanops_get_project_requirements": tool_get_project_requirements,
}

# ---------------------------------------------------------------------------
# MCP JSON-RPC 2.0 Protocol Engine
# ---------------------------------------------------------------------------

def run_server():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}

        # 1. Antigravity discovery negotiation
        if method == "server/discover":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": "Method not found"}
            }
        # 2. Standard MCP initialize
        elif method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "cleanops-mcp",
                        "version": "1.0.0"
                    }
                }
            }
        # 3. Initialized notification
        elif method == "notifications/initialized":
            continue
        # 4. Tools list
        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": MCP_TOOLS}
            }
        # 5. Tool execution
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}
            fn = DISPATCH.get(tool_name)
            if not fn:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: Tool '{tool_name}' not found."}],
                        "isError": True
                    }
                }
            else:
                try:
                    result_data = fn(tool_args)
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(result_data, indent=2)}],
                            "isError": False
                        }
                    }
                except Exception as e:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": f"Execution error: {str(e)}"}],
                            "isError": True
                        }
                    }
        # 6. Ping
        elif method == "ping":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
        # 7. Fallback for unrecognized methods
        else:
            if req_id is not None:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method '{method}' not found"}
                }
            else:
                continue

        out_str = json.dumps(resp) + "\n"
        sys.stdout.write(out_str)
        sys.stdout.flush()

if __name__ == "__main__":
    run_server()
