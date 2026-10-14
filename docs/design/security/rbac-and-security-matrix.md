# Security Architecture, RBAC Permissions Matrix & Storage Privacy

**Document:** `docs/design/security/rbac-and-security-matrix.md`\
**Project:** CleanOps\
**Status:** Design specification --- implementation must be verified
against the deployed schema, RLS policies, RPCs, backend routes, MCP
tools, and Storage policies.\
**Owner:** Ebraam Ibrahim\
**Last updated:** 14 October 2026

------------------------------------------------------------------------

## 1. Purpose and security principles

This document defines the minimum security contract for CleanOps across
the web portal, gateway/runtime, backend APIs, Supabase/Postgres,
Supabase Storage, and MCP tools. It covers role-based authorization,
private image/file handling, and audit logging.

CleanOps follows **Zero Trust**: every request is authenticated, every
sensitive action is authorized server-side, and access is denied unless
explicitly allowed. A hidden UI control is not a security boundary.

### Non-negotiable principles

1.  **Backend/database authority:** The server and database enforce
    permissions. Frontend checks are UX only.
2.  **Least privilege:** Grant only the actions and records required for
    the caller's role and relationship to the resource.
3.  **Deny by default:** Unlisted actions and unknown roles are denied.
4.  **Trusted identity:** Resolve user ID, role, and team membership
    from a validated server-side session/database record. Never trust
    client-supplied role, owner ID, team ID, or approval status.
5.  **Defense in depth:** Enforce authorization in backend handlers and,
    where applicable, database RLS/RPC and Storage policies. MCP tools
    must use the same authorization contract.
6.  **Private by default:** User-uploaded images and files are stored in
    private buckets; public object URLs are prohibited for private
    content.
7.  **Auditable mutations:** Sensitive changes produce a
    server-generated, append-only audit event.
8.  **Fail closed:** Missing identity, failed policy checks, invalid
    ownership, or unavailable authorization context must not fall back
    to broader access.

## 2. Trust boundaries and request flow

``` text
Browser / Mobile Client
        |
        | HTTPS + authenticated session
        v
Thin Gateway / API Runtime
        |
        | Validate session; derive actor and role
        | Apply authorization and input validation
        v
Supabase Postgres / RPC ---- Supabase Storage (private buckets)
        |
        v
Append-only audit events

Antigravity runtime / CleanOps MCP tools must call the same authorized
server-side operations; they must not bypass the authorization boundary.
```

### Enforcement responsibilities

  -----------------------------------------------------------------------
  Layer                   Required responsibility Must not do
  ----------------------- ----------------------- -----------------------
  Client UI               Hide/disable            Be the only permission
                          unavailable actions;    check; submit trusted
                          display only authorized role claims
                          data                    

  Gateway/backend         Authenticate, derive    Accept client-supplied
                          actor, authorize        actor/role as authority
                          action + resource,      
                          validate inputs,        
                          rate-limit sensitive    
                          endpoints, emit audit   
                          events                  

  Postgres/RLS            Restrict row            Assume every request
                          reads/writes by         passes through the UI
                          authenticated identity  
                          and policy; protect     
                          direct API access       

  RPCs                    Validate actor, role,   Expose privileged
                          resource relationship,  operations without
                          state transition, and   authorization checks
                          allowed fields inside   
                          the transaction         

  Storage                 Private buckets,        Use public buckets for
                          constrained             private user content
                          upload/download,        
                          short-lived signed URLs 

  MCP/agent tools         Reuse authorized        Use service credentials
                          backend operations and  to bypass user-level
                          caller context; audit   permissions
                          mutations               

  Service role            Server-side             Be embedded in
                          administrative jobs     frontend, mobile
                          only, with narrow code  bundle, logs, or
                          paths and secrets       agent-visible output
                          protection              
  -----------------------------------------------------------------------

**Important:** Supabase service-role credentials bypass normal RLS
protections. They must remain server-side. When a service-role client is
used, the backend must explicitly enforce the end user's authorization
before every operation.

## 3. Role model

The application has two internal human collaboration roles: **`lead`**
and **`member`**. **`instructor`** is a separate monitoring-only
identity. The requested **`citizen`** role is treated as an
external/field-facing identity, not as a third internal team role. It
must have no internal project-management privileges unless a separately
approved requirement explicitly grants them.

Roles are not interchangeable. Do not silently map unknown, legacy, or
missing roles to `member` or `lead`.

### Role definitions

-   **Lead:** Team Leader. Can manage project work and perform
    explicitly permitted review/approval actions. Lead actions remain
    subject to scope, state-transition rules, and audit requirements.
-   **Member:** Team Member. Can view authorized project information,
    work on assigned/owned tasks, update permitted task fields, and
    submit work. Cannot grant permissions or approve their own
    submission unless a documented policy explicitly permits it.
-   **Instructor:** Read-only, monitoring-only access to explicitly
    approved project progress and evidence. No mutations, including
    create, edit, assign, status changes, delete, review/approval,
    team/configuration, architecture, or permission changes.
-   **Citizen:** External user who may create or view only their own
    permitted service request/report and its associated status or
    response. Cannot view internal team workspaces, other citizens'
    records, internal comments, staff identities beyond what is
    intentionally disclosed, or project administration data. If no
    citizen-facing workflow exists, deny access until one is specified
    and implemented.

Authorization must consider both **role** and **resource relationship**
(for example, task assignment, record ownership, team membership, or
explicit sharing). A role alone must not grant access to every record.

## 4. RBAC permissions matrix

Legend: **A** = allowed within the caller's authorized scope and
server-side business rules; **O** = own/assigned records only; **R** =
read-only, approved scope; **---** = denied by default. All allowed
mutations require validation and audit logging where specified below.

  ------------------------------------------------------------------------------------------------------
  Capability                                       Lead          Member     Instructor           Citizen
  ------------------------------------ ---------------- --------------- -------------- -----------------
  Read internal                                       A   A, authorized    R, approved               ---
  project/phase/work-package data                            team scope          scope 

  Read task details                                   A  O / team scope    R, approved               ---
                                                              as needed          scope 

  Create internal tasks/subtasks                      A             ---            ---               ---

  Edit task title, description,                       A    O, permitted            ---               ---
  priority, dates                                           fields only                

  Assign/reassign task owner                          A             ---            ---               ---

  Change task lifecycle status                 A, valid        O, valid            ---               ---
                                            transitions     transitions                

  Submit task work/evidence             A, if acting as               O            ---               ---
                                                  owner                                

  Review submission / approve /              A, not own             ---            ---               ---
  request changes                         submission by                                
                                                default                                

  Cancel task                            A, with reason             ---            ---               ---
                                        and valid scope                                

  Read blockers and task discussions                  A  O / authorized    R, approved               ---
                                                             team scope          scope 

  Create/update own blocker                           A               O            ---               ---

  Read internal audit/activity log        A, authorized --- or narrowly    R, approved               ---
                                                  scope      scoped own     monitoring 
                                                               activity          scope 

  Manage team                             A, restricted             ---            ---               ---
  membership/invitations/roles           admin workflow                                

  Change system                              Explicitly             ---            ---               ---
  security/configuration/permissions         authorized                                
                                         administrative                                
                                          workflow only                                

  Read own citizen report/request                   ---             ---            ---                 O

  Create citizen report/request                     ---             ---            ---                 O

  Update/cancel citizen request                     ---             ---            ---   O, only allowed
                                                                                           states/fields

  Read other citizens' records                      ---             ---            ---               ---

  Read internal notes, staff-only                   ---             ---            ---               ---
  evidence, or team workspace                                                          

  Upload private image/file                   A, scoped       O, scoped     --- unless                O,
                                                                            explicitly   citizen-request
                                                                              approved        scope only

  Download private image/file             A, authorized  O / authorized      R only if O, own record and
                                                  scope           scope     explicitly     approved file
                                                                              approved             class

  Create signed URL                            A, after        O, after   R scope only   O, own approved
                                          authorization   authorization                      object only

  Read/modify another user's profile         A, minimum             ---            ---               ---
                                        required fields                                

  Grant/revoke roles or permissions          Dedicated,             ---            ---               ---
                                          audited admin                                
                                              flow only                                
  ------------------------------------------------------------------------------------------------------

### Required authorization details

-   **Field-level permissions:** Members may update only explicitly
    allowed task fields. Fields such as `owner_id`, `team_id`, approval
    state, risk flags, role, and audit metadata must not be writable
    through generic update endpoints.
-   **Workflow integrity:** Enforce legal task transitions in
    backend/RPC, not merely in the UI. Submission approval must verify
    reviewer authority, current state, and separation of duties.
-   **Self-approval:** A lead should not approve their own submission by
    default. If the project requires an exception, document it
    explicitly and audit it.
-   **Citizen scoping:** Every citizen request query must be constrained
    by the authenticated citizen's server-resolved identity. Never
    accept a `citizen_id` from the client as proof of ownership.
-   **Instructor read-only:** Enforce at API, database, RPC, MCP, and
    Storage layers. Do not rely on disabling buttons.
-   **No implicit escalation:** A member cannot become a lead by
    changing a profile field, JWT metadata, request body, URL parameter,
    or local storage.
-   **Role changes:** Only a dedicated, authorized administrative
    operation may change a role. Record actor, target, old role, new
    role, reason, and result.

## 5. Authentication and authorization decision procedure

For every protected request:

1.  Validate the session/token and its expiry, issuer, and audience as
    applicable.
2.  Resolve the actor's canonical user ID and current role from trusted
    server-side records.
3.  Resolve the requested resource from the database; do not authorize
    against client-supplied resource attributes.
4.  Check role, team/tenant scope, ownership/assignment, resource state,
    and requested fields.
5.  Reject unknown roles, missing relationships, stale/invalid state,
    and ambiguous authorization.
6.  Execute the minimum required operation, preferably transactionally
    for multi-step changes.
7.  Write an audit event for security-sensitive actions and failures
    according to the logging policy.
8.  Return only the minimum response fields the caller is permitted to
    see.

Use `401` for missing/invalid authentication and `403` for authenticated
but unauthorized requests where revealing resource existence is safe.
Use `404` where necessary to avoid leaking whether another user's
resource exists. Avoid detailed authorization errors that disclose
private records.

## 6. Private image and file storage lifecycle

### Storage requirements

-   Use private Supabase Storage buckets for citizen uploads, task
    evidence, and other private files.
-   Store object keys/paths and metadata in Postgres; do not treat a
    client-provided path as proof of ownership.
-   Use opaque, server-generated object names. Avoid names containing
    emails, phone numbers, citizen names, or other personal information.
-   Validate file size, extension, MIME type, and actual file signature
    where practical. Allowlist required formats; reject executable and
    unexpected formats.
-   Apply upload size limits, request rate limits, and per-user quotas.
    Consider malware scanning and image metadata stripping before making
    an uploaded file available to other users.
-   Do not log file contents, signed URL query strings, access tokens,
    or sensitive image metadata.
-   Keep private files private even when a record is deleted or
    archived; cleanup must follow the documented retention policy and be
    auditable.

### Lifecycle

1.  **Authorize upload:** Authenticate the actor and verify permission
    to attach a file to the target record.
2.  **Issue constrained upload permission:** Generate a short-lived
    upload capability or use a server-mediated upload. Restrict it to
    one intended object/path, expected content type/size where
    supported, and the relevant user/resource.
3.  **Validate and finalize:** Verify the uploaded object and metadata
    server-side before marking it as accepted/available. Unvalidated
    uploads must not become trusted evidence.
4.  **Persist linkage:** Store the object key, owning record, uploader
    ID, MIME type, size, checksum if available, upload timestamp,
    validation status, and retention classification. Enforce
    record-level authorization on metadata.
5.  **Authorize every read:** Check the caller's current permission to
    the parent record and file class before generating a download URL.
    Possession of an object key is not authorization.
6.  **Generate a short-lived signed URL:** Create it only after
    authorization, use the shortest practical expiry, and never persist
    or audit-log the full URL. Treat a signed URL as a bearer
    capability: anyone who obtains it may use it until expiry.
7.  **Revoke access:** Because a signed URL may remain usable until
    expiry, keep TTL short. For urgent revocation, remove or move the
    object, change access strategy, or use an authenticated proxy where
    immediate revocation is required.
8.  **Delete/retain:** On record deletion, apply the approved
    retention/legal-hold policy, remove the object when eligible, and
    record deletion outcome. Avoid orphaned objects with a scheduled
    reconciliation job.

### Suggested private object layout

``` text
citizen-uploads/{server-generated-citizen-id}/{opaque-object-id}
task-evidence/{server-generated-task-id}/{opaque-object-id}
```

Paths are organizational only, not an authorization mechanism. Storage
policies and server-side checks must independently verify identity and
relationship. Avoid exposing sequential IDs where they could facilitate
enumeration.

### Signed URL rules

-   Never create a signed URL before verifying access to the underlying
    record.
-   Never accept an arbitrary bucket/object path from the client and
    sign it without a database-backed authorization check.
-   Do not send signed URLs to unauthorized users, public analytics,
    error trackers, or audit logs.
-   Do not place signed URLs in long-lived database fields,
    notifications, or permanent chat history.
-   For sensitive evidence, prefer an authenticated download endpoint if
    immediate revocation, detailed access control, or stronger download
    auditing is required.
-   Test expiry, unauthorized access, cross-user access, path traversal
    attempts, and access after record permission changes.

## 7. Audit logging specification

Audit logs are a security control and must be generated by trusted
backend/database code, not by client-submitted event payloads.

### Minimum event schema

  -----------------------------------------------------------------------
  Field                               Requirement
  ----------------------------------- -----------------------------------
  `id`                                Server-generated unique event ID

  `occurred_at`                       Server/database timestamp in UTC

  `actor_user_id`                     Canonical authenticated actor; null
                                      only for explicitly supported
                                      anonymous/security events

  `actor_role`                        Role resolved at event time; never
                                      trusted from request body

  `action`                            Stable action name,
                                      e.g. `task.assign`,
                                      `submission.approve`,
                                      `file.download_url.create`

  `resource_type` / `resource_id`     Target resource, with privacy-safe
                                      identifiers

  `result`                            `success`, `denied`, or `failure`

  `reason_code`                       Safe, controlled code; do not store
                                      secrets or excessive personal data

  `request_id` / `correlation_id`     Links related gateway, backend,
                                      database, and MCP operations

  `source`                            `web`, `api`, `mcp`,
                                      `scheduled_job`, or another
                                      controlled source

  `ip_hash` / network context         Optional, minimized and
                                      retention-limited; avoid
                                      unnecessary raw IP retention

  `metadata`                          Allowlisted, redacted structured
                                      fields only; never credentials,
                                      tokens, signed URLs, or file
                                      contents
  -----------------------------------------------------------------------

### Events that must be logged

-   Login/session security events: success/failure, logout, session
    revocation, and suspicious authentication behavior where available.
-   Authorization denials for sensitive resources and repeated denied
    access attempts.
-   Role grants/revocations and invitation/membership changes.
-   Task creation, assignment, reassignment, lifecycle transitions,
    cancellation, and deletion.
-   Submission creation, resubmission, approval,
    rejection/request-changes, and any override.
-   Citizen report creation, update, cancellation, and staff access to
    citizen data.
-   File upload initiation/completion/rejection, download/signed URL
    issuance, deletion, and retention cleanup.
-   Changes to security configuration, RLS/policies, access rules, and
    administrative settings.
-   Sensitive export operations and privileged service-role actions.
-   Agent/MCP-initiated mutations, including the resolved actor and
    tool/action name.

Do not log every ordinary read by default unless needed for a sensitive
data class; for sensitive citizen records and evidence, define access
logging explicitly and consistently.

### Integrity, access, and retention

-   Application identities may insert audit events through controlled
    server/database functions but must not update or delete existing
    events.
-   Restrict audit-log reads to the lead and explicitly authorized
    monitoring/security functions; instructor access is read-only and
    limited to approved fields/scope.
-   Protect logs with RLS and least-privilege database grants. Avoid
    circular dependency where an audit failure silently permits a
    sensitive mutation.
-   For high-risk actions, fail closed if the required audit event
    cannot be persisted; for lower-risk events, use a documented durable
    retry/outbox mechanism.
-   Define a retention period based on project, privacy, and legal
    requirements. Do not retain logs indefinitely by default.
-   Redact secrets and personal data. Audit records should support
    investigation without duplicating full request bodies or private
    images.
-   Record both the attempted action and its outcome, while ensuring
    denied attempts do not leak private resource details to the caller.

## 8. Database, RLS, RPC, and MCP implementation checklist

-   [ ] Every exposed table has RLS enabled and policies reviewed for
    `SELECT`, `INSERT`, `UPDATE`, and `DELETE` independently.
-   [ ] Policies derive identity from the authenticated context and
    trusted membership records.
-   [ ] No policy trusts user-editable role metadata or client-supplied
    ownership fields.
-   [ ] Mutations validate allowed columns and state transitions;
    sensitive multi-row operations are transactional.
-   [ ] RPCs perform their own authorization checks, especially when
    using elevated privileges or `SECURITY DEFINER`.
-   [ ] `SECURITY DEFINER` functions set a safe `search_path`, use
    schema-qualified references, and have narrowly restricted `EXECUTE`
    grants.
-   [ ] Storage buckets are private; Storage policies restrict each
    operation and verify the actor/resource relationship.
-   [ ] Backend routes and MCP tools share the same authorization logic
    or call the same protected operations.
-   [ ] Service-role secrets exist only in trusted server-side secret
    storage and are never exposed to the client or model/tool output.
-   [ ] Generic update APIs cannot modify role, ownership, approval,
    audit, or security fields.
-   [ ] Instructor mutation attempts are denied at every applicable
    layer.
-   [ ] Citizen requests and files cannot be enumerated or accessed
    across users.
-   [ ] Audit events are server-generated, redacted, access-controlled,
    and append-only for application actors.
-   [ ] Rate limits and abuse controls cover authentication, uploads,
    signed URL issuance, and citizen submission endpoints.

## 9. Verification matrix

Run these tests against staging using separate accounts for each role.
Record the test date, build/migration version, actor role, request,
expected result, actual result, and evidence. Do not mark the security
task complete until the critical negative tests pass.

  -----------------------------------------------------------------------
  ID                      Test                    Expected result
  ----------------------- ----------------------- -----------------------
  RBAC-01                 Unauthenticated caller  Denied (`401` or safe
                          reads a protected task  equivalent)

  RBAC-02                 Member attempts to      Denied; no database
                          assign/reassign a task  change

  RBAC-03                 Member updates a task   Denied; no data leakage
                          they do not own or      
                          cannot access           

  RBAC-04                 Member attempts to      Denied; protected
                          modify `owner_id`,      fields unchanged
                          role, approval state,   
                          or audit metadata       

  RBAC-05                 Instructor attempts     Denied at each entry
                          every mutation class    point
                          through API/RPC/MCP     

  RBAC-06                 Lead attempts to        Denied by default or
                          approve their own       explicit documented
                          submission              exception

  RBAC-07                 Caller changes a        Authorization
                          role/owner ID in the    unchanged; forged value
                          request body or client  ignored/rejected
                          metadata                

  CIT-01                  Citizen A requests      Denied without
                          Citizen B's record by   revealing private
                          changing ID/path        details

  CIT-02                  Citizen attempts to     Denied
                          access internal tasks,  
                          comments, or audit logs 

  STO-01                  Anonymous caller        Denied
                          downloads a private     
                          object without a signed 
                          URL                     

  STO-02                  User requests a signed  Denied; no URL issued
                          URL for another user's  
                          object                  

  STO-03                  Authorized user obtains URL works only for the
                          a signed URL            intended object and
                                                  expires within
                                                  configured TTL

  STO-04                  Signed URL expires or   Access fails after
                          access is revoked       expiry; revocation
                          according to the chosen limitations are
                          design                  documented

  STO-05                  Upload uses a           Rejected or quarantined
                          disallowed type,        
                          oversized payload, or   
                          mismatched file         
                          signature               

  STO-06                  Client submits an       Denied unless
                          arbitrary object path   database-backed
                          to the signing endpoint authorization succeeds

  AUD-01                  Successful sensitive    One correlated audit
                          mutation occurs         event records actor,
                                                  action, resource, and
                                                  result

  AUD-02                  Sensitive mutation is   Denial event recorded
                          denied                  where policy requires;
                                                  no mutation occurs

  AUD-03                  Application actor       Denied
                          attempts to             
                          update/delete audit     
                          history                 

  AUD-04                  Audit metadata contains Redaction test passes;
                          a signed URL, token, or secret is not stored
                          secret                  

  MCP-01                  MCP tool attempts an    Denied by the same
                          action forbidden to the authorization policy as
                          invoking role           the API

  DB-01                   Direct PostgREST/table  RLS/grants prevent
                          access bypass attempt   unauthorized access

  DB-02                   Privileged RPC called   RPC denies the request
                          by unauthorized role    independently
  -----------------------------------------------------------------------

## 10. Definition of done

This deliverable is complete only when:

1.  The role matrix is reviewed and approved by the Team Leader,
    including the intended scope of `citizen`.
2.  The matrix matches the actual schema and every exposed API/RPC/MCP
    action; mismatches are recorded as implementation work, not silently
    assumed fixed.
3.  RLS and Storage policies are inspected and tested using real
    role-specific sessions.
4.  Signed URL expiry, ownership checks, private bucket configuration,
    and file validation are verified in staging.
5.  Audit schema, mutation hooks, redaction, access restrictions, and
    retention policy are implemented or have explicit tracked follow-up
    tasks.
6.  All critical negative tests pass and evidence is attached to the
    task.
7.  The document is committed at
    `docs/design/security/rbac-and-security-matrix.md`.

**Security sign-off rule:** A design document alone does not prove
enforcement. Mark implementation complete only after the code, policies,
and staging tests demonstrate the behavior above.
