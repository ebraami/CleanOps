# End-to-End Test Strategy & Checkpoint #1 Verification Matrix

**Document:** `docs/design/qa/e2e-test-scenarios-and-gate-criteria.md`\
**Project:** CleanOps\
**Package:** Cybersecurity, RBAC & Quality Verification Matrix\
**Status:** Design-readiness test strategy; execution evidence must be
attached before gate approval.\
**Owner:** Ebraam Ibrahim\
**Last updated:** 14 October 2026

------------------------------------------------------------------------

## 1. Purpose

This document defines the end-to-end (E2E) test strategy, repeatable
test fixtures, defect severity rules, verification matrix, and formal
quality gate for **Checkpoint #1 --- Design Readiness**.

The goal is to establish that the proposed design is complete,
internally consistent, security-aware, testable, and ready to proceed
into implementation. Passing this checkpoint does **not** claim that the
application is production-ready or that unimplemented behavior has been
tested. Design-level evidence and implementation-level evidence must be
clearly distinguished.

## 2. Scope

### In scope

-   Requirements traceability and acceptance criteria.
-   Authentication and authorization assumptions.
-   Role-based access control for `lead`, `member`, `instructor`, and
    `citizen`.
-   Task/work-package lifecycle and submission/review workflows.
-   API, database, RPC, RLS, Storage, and MCP trust boundaries.
-   Private image/file upload, access, signed URL, and deletion
    lifecycle.
-   Audit logging, error handling, and security-event traceability.
-   UI/API contract consistency, validation, negative cases, and
    regression planning.
-   Test data, reproducibility, defect triage, evidence, and gate
    decision.

### Out of scope for Checkpoint #1

-   Claiming successful E2E execution before a runnable
    build/environment exists.
-   Production penetration testing or formal third-party security
    certification.
-   Load/performance certification without agreed traffic targets and a
    representative environment.
-   Destructive tests against production data.
-   Treating screenshots or a passing UI-only flow as proof of backend
    authorization.
-   Treating a design review as proof that RLS, RPC, Storage, or backend
    controls are implemented.

## 3. Test strategy

### 3.1 Test levels

  -----------------------------------------------------------------------------
  Level               Objective          Examples          Evidence
  ------------------- ------------------ ----------------- --------------------
  Design review       Verify             RBAC matrix, API  Reviewed documents
                      requirements,      contracts, threat and open-issue list
                      boundaries,        assumptions       
                      states, and                          
                      responsibilities                     
                      are defined                          

  Unit/component      Verify isolated    Validators, state Test report and
                      logic and UI       transitions, form assertions
                      states             errors            

  API/integration     Verify contracts   Authentication,   Request/response
                      and server-side    field-level       results and database
                      rules              permissions, RPC  assertions
                                         behavior          

  Database/security   Verify direct      RLS, grants,      Role-specific test
                      access and policy  privileged RPCs,  results and policy
                      enforcement        ownership checks  inspection

  Storage integration Verify private     Upload            Bucket/policy
                      object lifecycle   constraints,      evidence and
                                         object ownership, controlled test
                                         signed URL expiry results

  E2E                 Verify realistic   Member submits    Run ID,
                      workflows across   work; lead        environment/build,
                      UI, API, DB, and   reviews;          screenshots/logs,
                      Storage            instructor        assertions
                                         observes only     

  Regression          Ensure fixes do    Repeat critical   Automated/manual
                      not reopen         RBAC and workflow regression report
                      previously         cases             
                      verified behavior                    
  -----------------------------------------------------------------------------

### 3.2 Test design principles

1.  **Risk-based:** Prioritize authorization bypass, cross-user data
    exposure, unauthorized state changes, and evidence/file disclosure.
2.  **Positive and negative coverage:** Every sensitive permission has
    at least one allowed case and one denied case.
3.  **Server-authoritative:** Confirm outcomes through API/database
    state, not UI appearance alone.
4.  **Role separation:** Use separate accounts for each role; never
    simulate roles by editing browser storage.
5.  **Traceability:** Every test maps to a requirement, acceptance
    criterion, or identified risk.
6.  **Repeatability:** Seed known fixtures, use deterministic IDs where
    safe, record environment/build, and clean up test data.
7.  **Privacy-safe evidence:** Redact credentials, tokens, signed URL
    query strings, and personal data.
8.  **Fail closed:** Missing role, unknown role, missing relationship,
    and authorization-service errors must not grant access.
9.  **No false passes:** A skipped, blocked, or unexecuted test is not a
    pass.
10. **Separation of concerns:** Checkpoint #1 proves design readiness;
    later execution gates prove implementation behavior.

## 4. Entry criteria and environment

### Entry criteria

-   [ ] Approved scope, requirements, and acceptance criteria are
    available.
-   [ ] Current role definitions and permissions matrix are available.
-   [ ] Core workflows and state transitions are documented.
-   [ ] API/RPC contracts and data ownership relationships are
    documented or explicitly tracked as gaps.
-   [ ] Storage buckets, object visibility, upload/download approach,
    and signed URL policy are specified.
-   [ ] Audit events and redaction requirements are specified.
-   [ ] Known dependencies, assumptions, and unresolved decisions are
    listed.
-   [ ] A test environment and test accounts are available before
    implementation-level E2E execution.

### Environment record

Record the following for every test run:

  -----------------------------------------------------------------------
  Field                               Required value
  ----------------------------------- -----------------------------------
  Run ID                              Unique identifier for the run

  Environment                         Local / staging / other approved
                                      non-production environment

  Build/version                       Commit SHA, build ID, or release
                                      identifier

  Database                            Migration/version identifier

  Browser/device                      Browser and version; device where
                                      relevant

  Test date/time                      UTC timestamp

  Tester                              Responsible tester

  Fixture version                     Seed-data version or fixture commit

  Result                              Pass / Fail / Blocked / Not Run

  Evidence location                   Approved evidence link or artifact
                                      path
  -----------------------------------------------------------------------

Do not include production secrets or real citizen personal data in test
fixtures.

## 5. Test data fixtures

Use synthetic data only. Create fixtures through a controlled seed
script or documented setup process, not by manually altering role claims
in the client.

### 5.1 Identity fixtures

  -------------------------------------------------------------------------
  Fixture ID          Role              Relationship /    Intended use
                                        setup             
  ------------------- ----------------- ----------------- -----------------
  `U-LEAD-01`         `lead`            Lead in Team      Authorized
                                        Alpha             management and
                                                          review

  `U-MEMBER-01`       `member`          Assigned to Task  Allowed task work
                                        A in Team Alpha   and submission

  `U-MEMBER-02`       `member`          Same team; not    Scope and
                                        assigned to Task  assignment checks
                                        A                 

  `U-MEMBER-03`       `member`          Member of Team    Cross-team
                                        Beta, if          isolation
                                        multi-team        
                                        isolation applies 

  `U-INSTRUCTOR-01`   `instructor`      Approved          Read-only checks
                                        monitoring scope  

  `U-CITIZEN-01`      `citizen`         Owns Citizen      Own-record access
                                        Request A         

  `U-CITIZEN-02`      `citizen`         Owns Citizen      Cross-citizen
                                        Request B         isolation

  `U-NO-ROLE-01`      No valid role     Authenticated     Fail-closed
                                        identity with     behavior
                                        missing/invalid   
                                        role mapping      

  `U-ANON-01`         Anonymous         No authenticated  Authentication
                                        session           boundary
  -------------------------------------------------------------------------

### 5.2 Resource fixtures

  -------------------------------------------------------------------------------
  Fixture ID          Resource              Initial state     Relationship
  ------------------- --------------------- ----------------- -------------------
  `TASK-A`            Internal task         `assigned`        Assigned to
                                                              `U-MEMBER-01`, Team
                                                              Alpha

  `TASK-B`            Internal task         `in_progress`     Assigned to
                                                              `U-MEMBER-02`, Team
                                                              Alpha

  `TASK-C`            Internal task         `assigned`        Team Beta, if
                                                              applicable

  `SUB-A`             Submission            `submitted`       Created by
                                                              `U-MEMBER-01` for
                                                              `TASK-A`

  `SUB-OWN`           Submission            `submitted`       Created by
                                                              `U-LEAD-01` for
                                                              self-approval
                                                              negative test

  `CIT-REQ-A`         Citizen request       `open`            Owned by
                                                              `U-CITIZEN-01`

  `CIT-REQ-B`         Citizen request       `open`            Owned by
                                                              `U-CITIZEN-02`

  `FILE-A`            Private evidence      `validated`       Linked to `TASK-A`
                      object                                  or `CIT-REQ-A`

  `FILE-QUARANTINE`   Invalid/unvalidated   `pending`         Must not be exposed
                      object                                  as trusted evidence

  `AUDIT-A`           Audit event           Existing          Used for
                                            immutable record  tamper-resistance
                                                              tests
  -------------------------------------------------------------------------------

Use generated UUIDs or equivalent non-guessable IDs where supported.
These fixture labels are aliases for test setup, not literal production
IDs or required database columns.

### 5.3 Special payload fixtures

-   Valid small image within configured size/type limits.
-   Disallowed extension and executable-like payload.
-   MIME type/signature mismatch.
-   Oversized upload.
-   Missing required fields and malformed identifiers.
-   Unauthorized `owner_id`, `team_id`, `role`, approval state, or audit
    fields in mutation payloads.
-   Expired session/token and expired signed URL.
-   Object key belonging to a different user.
-   Strings containing HTML/script-like content to verify safe rendering
    and validation.
-   Requests with duplicate/idempotency key where supported.
-   Invalid state transition and stale-version/concurrent update
    attempt.

## 6. End-to-end scenarios

### E2E-01 --- Authentication boundary

**Precondition:** An anonymous session and a valid test account are
available.

**Steps:** 1. Request a protected task without a session. 2. Sign in as
`U-MEMBER-01`. 3. Request an authorized task. 4. Expire/revoke the
session and repeat the protected request.

**Expected:** Anonymous and expired sessions are denied; valid sessions
can access only permitted resources. No protected content appears in the
unauthenticated response.

### E2E-02 --- Member completes assigned task workflow

**Precondition:** `TASK-A` is assigned to `U-MEMBER-01`.

**Steps:** 1. Open Task A. 2. Update permitted fields or status
according to the documented workflow. 3. Submit required work/evidence.
4. Refresh and query the authoritative state.

**Expected:** Allowed changes persist; restricted fields remain
unchanged; submission and status transitions follow documented rules;
audit events exist for required mutations.

### E2E-03 --- Member cannot manage another task

**Precondition:** `TASK-B` belongs to another member.

**Steps:** 1. Attempt to open Task B directly by ID. 2. Attempt a
permitted-looking update through the API. 3. Attempt to change
assignment, team, approval, or security fields. 4. Inspect authoritative
database state.

**Expected:** Access follows the approved team/assignment policy;
unauthorized actions are denied; no unauthorized state or field changes
occur.

### E2E-04 --- Lead reviews a submission

**Precondition:** `SUB-A` is submitted and assigned to a valid task.

**Steps:** 1. Sign in as `U-LEAD-01`. 2. Open the submission. 3. Approve
or request changes using a valid transition. 4. Repeat with an
invalid/stale transition. 5. Review audit events.

**Expected:** Authorized review succeeds; invalid transitions fail; the
final state is consistent; required audit events identify actor, action,
resource, and result.

### E2E-05 --- Self-approval separation of duties

**Precondition:** `SUB-OWN` was created by the lead account.

**Steps:** 1. Attempt to approve the lead's own submission. 2. Repeat
through any alternate API/RPC/MCP path.

**Expected:** Denied by default unless a formally approved exception is
documented and enforced consistently.

### E2E-06 --- Instructor is monitoring-only

**Precondition:** Instructor has an approved monitoring scope.

**Steps:** 1. Read an approved progress view. 2. Attempt task creation,
editing, assignment, status change, review, deletion, role management,
file upload, and privileged RPC/MCP mutation. 3. Verify data remains
unchanged.

**Expected:** Approved reads succeed; every mutation is denied at all
applicable layers; no hidden UI control is treated as sufficient
enforcement.

### E2E-07 --- Citizen can access only their own request

**Precondition:** Citizen A owns `CIT-REQ-A`; Citizen B owns
`CIT-REQ-B`.

**Steps:** 1. Citizen A creates or reads their request. 2. Citizen A
substitutes Citizen B's request ID in URL, body, and API parameters. 3.
Citizen A attempts to list internal tasks, staff-only comments, or audit
events.

**Expected:** Own allowed workflow succeeds; cross-citizen and internal
access is denied without leaking protected details.

### E2E-08 --- Private file upload and validation

**Precondition:** An authorized user may attach evidence to a target
record.

**Steps:** 1. Upload a valid image to the authorized record. 2. Attempt
oversized, disallowed, and signature-mismatched uploads. 3. Attempt to
attach a file to a record outside the user's scope. 4. Check object
visibility and validation status.

**Expected:** Valid files follow the acceptance flow; invalid files are
rejected or quarantined; unauthorized linkage is denied; private objects
are not publicly accessible.

### E2E-09 --- Signed URL authorization and expiry

**Precondition:** `FILE-A` is private and linked to an authorized
record.

**Steps:** 1. Request a signed URL as an authorized user. 2. Request the
same URL as an unauthorized user. 3. Verify the authorized URL reaches
only the intended object. 4. Verify access after expiry. 5. Attempt to
sign an arbitrary object path and inspect logs for URL leakage.

**Expected:** URL issuance requires current authorization; unauthorized
requests receive no URL; expiry is enforced; object/path substitution
fails; full signed URLs are not logged or persisted.

### E2E-10 --- Audit event integrity and redaction

**Precondition:** Audit storage and required event hooks are configured.

**Steps:** 1. Perform an authorized sensitive mutation. 2. Perform a
denied sensitive mutation. 3. Attempt to update/delete an existing audit
event. 4. Submit a request containing a token or signed URL in a field
that should be redacted. 5. Inspect stored events and access
permissions.

**Expected:** Required events are server-generated and correlated;
tampering is denied; secrets and signed URL query strings are absent;
audit access follows least privilege.

### E2E-11 --- Direct database/API bypass

**Precondition:** Test accounts can call exposed data APIs with their
own sessions.

**Steps:** 1. Attempt unauthorized `SELECT`, `INSERT`, `UPDATE`, and
`DELETE` against protected data. 2. Call sensitive RPCs directly. 3.
Test missing role mapping and cross-team identifiers.

**Expected:** RLS, grants, and RPC checks deny unauthorized operations
even when the UI is bypassed.

### E2E-12 --- MCP/agent authorization parity

**Precondition:** An MCP tool or agent action is available in the test
environment.

**Steps:** 1. Invoke an allowed operation with a member identity. 2.
Invoke a forbidden assignment or approval operation with the same
identity. 3. Repeat with instructor and citizen identities where
applicable. 4. Compare outcomes with direct API behavior and audit
events.

**Expected:** MCP cannot elevate privileges or bypass user-level checks;
authorization results match the same policy used by the backend; actor
and source are auditable.

### E2E-13 --- Concurrency, stale state, and idempotency

**Precondition:** The workflow supports versioning or has documented
concurrency semantics.

**Steps:** 1. Submit two conflicting updates to the same task. 2. Repeat
a submission or mutation using the same idempotency key if supported. 3.
Attempt an invalid transition from a stale state.

**Expected:** No silent overwrite or duplicate side effect occurs;
conflicts are returned safely; idempotency behavior matches the
contract. If unsupported, record it as an explicit design gap rather
than a pass.

### E2E-14 --- Error handling and information leakage

**Precondition:** Controlled invalid requests can be made in a
non-production environment.

**Steps:** 1. Trigger validation, authorization, missing-resource, and
simulated dependency errors. 2. Inspect client responses and server
logs. 3. Check for stack traces, secrets, private object paths, or other
users' data.

**Expected:** Responses are useful but privacy-safe; logs are redacted;
failures do not grant access or expose implementation secrets.

## 7. Verification matrix and traceability

Map every row to the corresponding requirements/design section and
capture evidence. Add project-specific requirement IDs when the
authoritative requirements register is available.

  ---------------------------------------------------------------------------------------------
  ID             Verification item      Method             Pass criterion        Priority
  -------------- ---------------------- ------------------ --------------------- --------------
  V-01           Scope and acceptance   Document review    Every in-scope        High
                 criteria                                  feature has           
                                                           observable acceptance 
                                                           criteria              

  V-02           Role definitions       Document/schema    All four roles and    Critical
                                        review             unknown-role behavior 
                                                           are unambiguous       

  V-03           Permission matrix      Review + negative  Each sensitive action Critical
                                        tests              has allow/deny rules  
                                                           and scope conditions  

  V-04           Resource               Data model + API   Trusted relationship  Critical
                 ownership/assignment   review             is defined and        
                                                           checked server-side   

  V-05           Workflow/state machine State-transition   Valid/invalid         High
                                        review             transitions and       
                                                           reviewer separation   
                                                           are specified         

  V-06           Authentication         API contract +     Invalid/expired       Critical
                                        tests              sessions are denied   

  V-07           RLS and grants         SQL/policy         Direct access cannot  Critical
                                        review + direct    bypass intended scope 
                                        API tests                                

  V-08           Privileged RPCs        Function/grant     Authorization is      Critical
                                        review             checked inside        
                                                           privileged operations 

  V-09           MCP authorization      Tool/API           Agent tools cannot    Critical
                 parity                 comparison         exceed caller         
                                                           permissions           

  V-10           Private storage        Bucket/policy      Private files have no Critical
                                        inspection         unintended public     
                                                           access                

  V-11           Signed URLs            Design review +    Authorization         Critical
                                        integration tests  precedes issuance;    
                                                           TTL and leakage       
                                                           controls are          
                                                           specified             

  V-12           Upload validation      Contract +         Size/type/signature   High
                                        integration tests  and record linkage    
                                                           are validated         

  V-13           Audit schema           Schema/design      Actor, action,        High
                                        review             resource, result,     
                                                           time, and correlation 
                                                           are captured          

  V-14           Audit integrity        Permission tests   Application actors    High
                                                           cannot edit/delete    
                                                           historical events     

  V-15           Redaction/privacy      Log inspection     Secrets, tokens, full Critical
                                                           signed URLs, and      
                                                           unnecessary PII are   
                                                           excluded              

  V-16           Error handling         API/UI review      Denials and failures  High
                                                           do not leak protected 
                                                           information           

  V-17           Test fixtures          Seed review        All roles,            High
                                                           relationships,        
                                                           invalid states, and   
                                                           cross-user cases are  
                                                           reproducible          

  V-18           Defect process         QA process review  Severity, owner,      Medium
                                                           reproduction,         
                                                           evidence, and retest  
                                                           rules are defined     

  V-19           Traceability           Matrix review      Every critical        High
                                                           requirement maps to   
                                                           one or more           
                                                           verification cases    

  V-20           Gate evidence          Evidence audit     Results, unresolved   High
                                                           risks, approvals, and 
                                                           version are recorded  
  ---------------------------------------------------------------------------------------------

## 8. Defect severity and priority criteria

Severity describes impact; priority describes how urgently the team
should address the issue. They must not be conflated.

  ------------------------------------------------------------------------
  Severity          Definition         Examples          Expected response
  ----------------- ------------------ ----------------- -----------------
  **S1 ---          Unauthorized       Citizen A reads   Stop affected
  Critical**        privilege          Citizen B's       release/gate;
                    escalation,        private evidence; notify Team
                    cross-user private instructor can    Leader
                    data exposure,     mutate data;      immediately; fix
                    authentication     signed URL is     and retest before
                    bypass, broad data issued without    gate pass
                    loss/corruption,   authorization     
                    or a security                        
                    control failure                      
                    that defeats a                       
                    core trust                           
                    boundary                             

  **S2 --- High**   Major workflow or  Member can        Must be resolved
                    security failure   reassign another  before the
                    with substantial   user's task;      affected gate
                    impact and no      privileged RPC    passes unless a
                    acceptable         lacks a required  documented,
                    workaround         check; audit      explicitly
                                       trail missing for approved
                                       critical approval exception is
                                                         permitted

  **S3 --- Medium** Important but      Incorrect         Fix before
                    bounded functional validation        release where in
                    issue with limited message;          scope, or
                    impact or a        non-critical      document owner
                    practical          workflow state    and due date
                    workaround         displayed         
                                       incorrectly       
                                       without           
                                       data/security     
                                       impact            

  **S4 --- Low**    Cosmetic or minor  Spacing issue,    Backlog or fix
                    usability issue    harmless wording  according to
                    that does not      inconsistency     agreed priority
                    affect                               
                    correctness,                         
                    access, privacy,                     
                    or core workflow                     
  ------------------------------------------------------------------------

### Priority guidance

-   **P0:** Immediate action; active security/privacy incident or
    critical blocker.
-   **P1:** Must be fixed before the relevant gate/release.
-   **P2:** Fix in the planned iteration; may be accepted with
    documented rationale.
-   **P3:** Low urgency; schedule when practical.

A defect with low likelihood can still be S1 if the impact is severe.
Any suspected unauthorized data access should be triaged promptly and
handled under the project's incident process.

### Required defect record

-   Defect ID and concise title.
-   Environment/build/commit and test run ID.
-   Severity and priority, with rationale.
-   Preconditions, role, and resource relationship.
-   Exact reproduction steps and expected versus actual result.
-   Sanitized request/response or logs and evidence links.
-   Security/privacy impact and affected roles/data.
-   Owner, status, fix reference, retest result, and regression
    coverage.
-   Risk acceptance details and approver, if an exception is allowed.

## 9. Checkpoint #1 --- Design Readiness gate

### Gate objective

Confirm that the design is sufficiently complete and verifiable to
proceed to implementation without unresolved ambiguity in critical
security boundaries, role permissions, core workflows, data privacy, or
quality ownership.

### Gate checklist

#### A. Requirements and architecture

-   [ ] Scope, assumptions, exclusions, and dependencies are documented.
-   [ ] Core user journeys and acceptance criteria are testable.
-   [ ] System components, trust boundaries, and authoritative
    enforcement points are identified.
-   [ ] API, database, Storage, and MCP responsibilities are consistent.
-   [ ] Unresolved decisions have owners and due dates.

#### B. RBAC and data isolation

-   [ ] `lead`, `member`, `instructor`, and `citizen` are defined.
-   [ ] Every sensitive action has explicit allowed and denied
    roles/scopes.
-   [ ] Resource ownership, assignment, team membership, and citizen
    isolation rules are defined.
-   [ ] Instructor monitoring-only restrictions cover backend, database,
    Storage, and MCP.
-   [ ] Unknown/missing roles and forged client claims fail closed.
-   [ ] Self-approval and role-management policies are explicit.

#### C. Storage and privacy

-   [ ] Private buckets and object-access strategy are specified.
-   [ ] Upload validation, quarantine/acceptance, ownership linkage, and
    quotas are defined.
-   [ ] Signed URL authorization, lifetime, leakage prevention, and
    revocation limitations are documented.
-   [ ] Retention, deletion, orphan cleanup, and any legal-hold behavior
    are defined.
-   [ ] Sensitive data minimization and log redaction are specified.

#### D. Auditability and operations

-   [ ] Audit event schema and mandatory event classes are specified.
-   [ ] Application-level audit tampering is prevented by design.
-   [ ] Audit read permissions, retention, and failure behavior are
    defined.
-   [ ] Correlation IDs connect relevant backend, database, and agent
    operations.
-   [ ] Monitoring and escalation for critical security failures are
    documented.

#### E. QA readiness

-   [ ] Test strategy covers design review, unit, API, database,
    Storage, E2E, and regression levels.
-   [ ] Fixtures cover all roles, cross-user boundaries, invalid inputs,
    and invalid states.
-   [ ] Critical positive and negative scenarios are mapped to
    requirements.
-   [ ] Severity/priority criteria and defect workflow are agreed.
-   [ ] Test environment, accounts, setup, evidence storage, and cleanup
    approach are documented.
-   [ ] A reproducible execution plan exists for implementation-stage
    verification.

#### F. Decision and sign-off

-   [ ] No unresolved S1-equivalent design gap remains.
-   [ ] Critical questions and assumptions are resolved or explicitly
    block the gate.
-   [ ] Risks, accepted exceptions, owners, and due dates are recorded.
-   [ ] Evidence links and reviewed document versions are recorded.
-   [ ] Team Leader and designated security/QA reviewer have recorded
    the decision.

### Gate decision rules

**PASS** - All mandatory checklist items are satisfied. - No unresolved
critical design gap remains. - Required reviewers approve the same
version. - Evidence and decision are recorded.

**CONDITIONAL PASS** - Only non-critical gaps remain. - Each gap has a
named owner, due date, mitigation, and explicit approver. - No exception
weakens a critical authorization, privacy, or audit boundary. - The
project process explicitly permits conditional approval.

**FAIL / BLOCKED** - A critical role boundary, resource ownership rule,
private storage rule, or audit control is undefined or contradictory. -
A required reviewer or authoritative design is missing. - Evidence is
insufficient to support the decision. - A critical defect or unresolved
S1-equivalent risk remains.

A conditional pass must not be used to waive a core security boundary.
If the project has no formal conditional-pass policy, use PASS or
FAIL/BLOCKED only.

### Sign-off record

  Field                               Value
  ----------------------------------- ------------------------------------------
  Checkpoint                          #1 --- Design Readiness
  Reviewed document version/commit    To be recorded
  QA reviewer                         To be recorded
  Team Leader                         To be recorded
  Security reviewer (if designated)   To be recorded
  Decision                            PASS / CONDITIONAL PASS / FAIL / BLOCKED
  Open risks/defects                  IDs and links
  Conditions, owners, due dates       If applicable
  Decision date                       UTC timestamp
  Evidence location                   Link/path

## 10. Execution reporting template

Use one row per executed test case:

  -----------------------------------------------------------------------------------
  Test ID    Build /    Role           Result     Defect ID  Evidence   Notes
             run ID                                                     
  ---------- ---------- -------------- ---------- ---------- ---------- -------------
  `E2E-01`   Pending    Anonymous /    Not Run    ---        ---        Execute in
                        member                                          staging

  `E2E-02`   Pending    Member         Not Run    ---        ---        Execute in
                                                                        staging

  `E2E-03`   Pending    Member         Not Run    ---        ---        Execute in
                                                                        staging

  `E2E-04`   Pending    Lead           Not Run    ---        ---        Execute in
                                                                        staging

  `E2E-05`   Pending    Lead           Not Run    ---        ---        Execute in
                                                                        staging

  `E2E-06`   Pending    Instructor     Not Run    ---        ---        Execute in
                                                                        staging

  `E2E-07`   Pending    Citizen        Not Run    ---        ---        Execute in
                                                                        staging

  `E2E-08`   Pending    Authorized     Not Run    ---        ---        Execute in
                        uploader                                        staging

  `E2E-09`   Pending    Authorized /   Not Run    ---        ---        Execute in
                        unauthorized                                    staging

  `E2E-10`   Pending    Authorized /   Not Run    ---        ---        Execute in
                        unauthorized                                    staging

  `E2E-11`   Pending    Member / no    Not Run    ---        ---        Execute in
                        role                                            staging

  `E2E-12`   Pending    Member /       Not Run    ---        ---        Execute in
                        instructor /                                    staging
                        citizen                                         

  `E2E-13`   Pending    Concurrent     Not Run    ---        ---        Execute if
                        actors                                          concurrency
                                                                        semantics
                                                                        apply

  `E2E-14`   Pending    Relevant role  Not Run    ---        ---        Execute in
                                                                        staging
  -----------------------------------------------------------------------------------

**Reporting rule:** Do not convert `Not Run` or `Blocked` into `Pass`.
If the environment or feature is not implemented, report the blocker and
preserve the test as pending.

## 11. Definition of done

This deliverable is complete when:

1.  The file exists at
    `docs/design/qa/e2e-test-scenarios-and-gate-criteria.md`.
2.  Test scope, principles, environment record, fixtures, E2E scenarios,
    verification matrix, defect criteria, and gate checklist are
    reviewed.
3.  The Team Leader confirms the intended Checkpoint #1 gate and
    sign-off owners.
4.  Every critical security requirement has traceable verification
    coverage.
5.  Unresolved assumptions and design gaps are tracked rather than
    represented as verified behavior.
6.  The document is committed and linked to the work package.
7.  Execution results are added during implementation-stage
    verification; no test is marked passed without evidence.

**Final note:** This strategy defines what must be verified and what
evidence is required. It does not claim that CleanOps has passed these
tests or that Checkpoint #1 has been approved.
