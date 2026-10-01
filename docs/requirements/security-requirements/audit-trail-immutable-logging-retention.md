# Audit Trail, Immutable Logging, and Retention Standards

| Field | Value |
|---|---|
| **Task ID** | T_f860e3 |
| **Package** | Security Requirements (P01 — Project Foundation & Requirements) |
| **Project** | CleanStreet AI — Smart Citizen-Requested Street Cleaning and Waste Management Platform |
| **Author** | Mariam Mahfouz (Back-end, Java Spring Boot) |
| **Version** | 1.0 (Draft for Team Leader review) |
| **Date** | 2 October 2026 |
| **Depends on** | T_85ab37 — Authentication and RBAC Specification |
| **Compliance reference** | ADR-004 |
| **Repository path** | `docs/requirements/security-requirements/audit-trail-immutable-logging-retention.md` |

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Definitions and Conventions](#2-definitions-and-conventions)
3. [Dependencies and Assumptions](#3-dependencies-and-assumptions)
4. [Auditable Event Catalog](#4-auditable-event-catalog)
5. [Audit Record Schema](#5-audit-record-schema)
6. [Immutability Rules](#6-immutability-rules)
7. [Tamper-Prevention and Tamper-Detection Measures](#7-tamper-prevention-and-tamper-detection-measures)
8. [Access Control for Audit Data](#8-access-control-for-audit-data)
9. [Data Minimisation and Privacy Rules](#9-data-minimisation-and-privacy-rules)
10. [Retention Schedule](#10-retention-schedule)
11. [Automated Archive and Purge Criteria](#11-automated-archive-and-purge-criteria)
12. [Backend Implementation Requirements (Spring Boot)](#12-backend-implementation-requirements-spring-boot)
13. [Verification and Acceptance Criteria](#13-verification-and-acceptance-criteria)
14. [Traceability to the Project Proposal](#14-traceability-to-the-project-proposal)
15. [Out of Scope](#15-out-of-scope)
16. [Open Items](#16-open-items)

---

## 1. Purpose and Scope

This document defines the audit logging standard for the CleanStreet AI backend. It specifies:

- which events **must** be audited (administrative, security, and status-transition events);
- the structure of an audit record;
- how audit records are stored **immutably** and how tampering is prevented and detected;
- how long records are retained, and the criteria for **automated archiving and purging**.

The proposal (Section 17) lists *"Audit logging for important status changes, implemented via the STATUS_HISTORY table"* as a security requirement, and Section 16.2 states that a report cannot be closed solely because a team marked it complete. Both depend on a trustworthy record of who did what and when. This specification extends that intent to a full audit trail covering security and administrative activity.

**In scope:** the PostgreSQL/PostGIS audit store, the Spring Boot components that write to it, archive storage, and the scheduled lifecycle jobs.

**Out of scope:** see [Section 15](#15-out-of-scope).

## 2. Definitions and Conventions

| Term | Meaning |
|---|---|
| **Audit event** | A single recorded fact: an *actor* performed an *action* on a *target* at a *time* with an *outcome*. |
| **Audit record** | The persisted row representing one audit event. |
| **Actor** | The authenticated principal (user ID and role) or `SYSTEM` for scheduled/automated actions. |
| **Immutable** | Once committed, a record cannot be updated or deleted by any application or database role during its retention period. |
| **Hash chain** | Each record stores a SHA-256 hash covering its own content plus the previous record's hash, so any alteration breaks all later hashes. |
| **Hot storage** | The live PostgreSQL audit table (queryable by the application). |
| **Cold storage** | Archived, compressed, write-once audit files in Object Storage (Firebase Storage or Amazon S3, as per proposal Section 15.1). |
| **Legal hold** | A flag that suspends purging of specified records. |

Requirement keywords **MUST**, **MUST NOT**, **SHOULD**, and **MAY** follow RFC 2119. Each requirement has an ID (`AUD-xxx`) for traceability in reviews and tests.

## 3. Dependencies and Assumptions

**Dependency — T_85ab37 (Authentication and RBAC Specification).** Audit records identify the actor by the identity and role established by that specification. This document assumes:

| ID | Assumption |
|---|---|
| A-1 | Every API request is authenticated (Firebase Authentication token validated by Spring Security) before reaching business logic, except public endpoints (login/register). |
| A-2 | The authenticated principal exposes a stable `user_id` and a `role`. Role names used below are `CITIZEN`, `OPERATOR`, `CLEANING_TEAM`, `ADMIN`, and the pseudo-actor `SYSTEM`. If T_85ab37 uses different names, only the `actor_role` values in this document change. |
| A-3 | Authorisation decisions (allow/deny) are made in a single place (Spring Security method/URL security) so that denials can be captured centrally. |
| A-4 | The data model matches proposal Section 15.2 (USERS, REPORTS, IMAGES, STATUS_HISTORY, CLEANING_TEAMS, ASSIGNMENTS, CATEGORIES). |

## 4. Auditable Event Catalog

The system MUST record every event listed below. Event types are fixed string constants (enum `AuditEventType`) and MUST NOT be free text.

### 4.1 Security events

| Event type | Trigger | Outcome values |
|---|---|---|
| `AUTH_LOGIN` | Login attempt (operator, cleaning team, admin, citizen) | `SUCCESS`, `FAILURE` |
| `AUTH_LOGOUT` | Explicit logout / token revocation | `SUCCESS` |
| `AUTH_TOKEN_REJECTED` | Expired, malformed, or invalid token presented | `FAILURE` |
| `AUTH_LOCKOUT` | Account temporarily locked after repeated failures | `SUCCESS` |
| `AUTH_PASSWORD_CHANGED` | User changes or resets credentials | `SUCCESS`, `FAILURE` |
| `ACCESS_DENIED` | Authorisation failure (HTTP 403) on a protected resource | `DENIED` |
| `RBAC_ROLE_CHANGED` | A user's role is granted, changed, or revoked | `SUCCESS` |
| `RBAC_PERMISSION_CHANGED` | Role-to-permission mapping is modified | `SUCCESS` |

### 4.2 Administrative events

| Event type | Trigger |
|---|---|
| `USER_CREATED` / `USER_UPDATED` / `USER_DEACTIVATED` | User account lifecycle changes |
| `TEAM_CREATED` / `TEAM_UPDATED` / `TEAM_DEACTIVATED` | Cleaning-team management |
| `CONFIG_CHANGED` | Change to configurable values, including the **severity weight table** and priority-score weights (proposal Section 11, Tier 2) and SLA thresholds |
| `PRIORITY_OVERRIDDEN` | An operator manually overrides the system-computed priority score (supports the "AI assists, operator decides" principle, proposal Section 16.3). The record MUST store old and new score and a mandatory reason. |
| `DUPLICATE_LINKED` / `DUPLICATE_UNLINKED` | Operator accepts or rejects a suggested duplicate link (proposal Section 11, Tier 3) |
| `DATA_EXPORT` | Any bulk export of reports, analytics, or audit data |

### 4.3 Report status-transition events

| Event type | Trigger |
|---|---|
| `REPORT_CREATED` | Citizen submits a report |
| `REPORT_STATUS_CHANGED` | Any change to `REPORTS.current_status` (e.g. `SUBMITTED → ASSIGNED → IN_PROGRESS → COMPLETED → RESOLVED`, or return to workflow when cleaning is judged unsatisfactory — proposal Section 16.2, step 9) |
| `REPORT_ASSIGNED` / `REPORT_REASSIGNED` | Creation or change of an ASSIGNMENTS row |
| `COMPLETION_EVIDENCE_ADDED` | Cleaning team uploads an `after` image (IMAGES row) |
| `REPORT_RESOLVED` | Operator closes a report after reviewing completion evidence |
| `REPORT_REOPENED` | Operator returns a report to the workflow |
| `AI_ANALYSIS_WRITTEN` | AI service writes priority score/category back to the report (actor = `SYSTEM`) |

For every `REPORT_STATUS_CHANGED` event, the record MUST capture `old_status` and `new_status`.

### 4.4 Audit-system events (the audit trail audits itself)

| Event type | Trigger |
|---|---|
| `AUDIT_ARCHIVE_CREATED` | A partition is archived to cold storage |
| `AUDIT_PURGE_EXECUTED` | A partition is purged from hot storage |
| `AUDIT_INTEGRITY_CHECK` | Scheduled or manual chain verification (result recorded) |
| `AUDIT_INTEGRITY_VIOLATION` | Chain verification detected a mismatch |
| `AUDIT_ACCESS` | Any read of audit records through the audit API |
| `AUDIT_LEGAL_HOLD_SET` / `AUDIT_LEGAL_HOLD_RELEASED` | Legal hold changes |

### 4.5 Core requirements

| ID | Requirement |
|---|---|
| AUD-001 | The system **MUST** write an audit record for every event in Sections 4.1–4.4. |
| AUD-002 | Audit records for business events (Section 4.3 and `PRIORITY_OVERRIDDEN`, `DUPLICATE_*`) **MUST** be written **in the same database transaction** as the business change. If the audit write fails, the business change **MUST** roll back. |
| AUD-003 | Audit records for failed or rejected operations (`AUTH_LOGIN` failure, `ACCESS_DENIED`, `AUTH_TOKEN_REJECTED`) **MUST** be written even though no business change occurs. |
| AUD-004 | A failure to write an audit record **MUST NOT** be silently ignored. It **MUST** raise an error, log to the application log, and trigger an alert. |
| AUD-005 | Audit writes **MUST NOT** be disabled, skipped, or made conditional through configuration flags in any environment other than automated unit tests. |

## 5. Audit Record Schema

### 5.1 Logical fields

| Column | Type | Null | Description |
|---|---|---|---|
| `id` | `BIGINT` (identity) | No | Strictly increasing primary key; also serves as the chain sequence number. |
| `event_id` | `UUID` | No | Globally unique event identifier (for cross-system correlation and archive de-duplication). |
| `occurred_at` | `TIMESTAMPTZ` | No | Server-side UTC timestamp, set by the database (`now()`), **never** supplied by the client. |
| `event_type` | `VARCHAR(64)` | No | Value from `AuditEventType` (Section 4). |
| `category` | `VARCHAR(16)` | No | `SECURITY`, `ADMIN`, `STATUS`, or `AUDIT`. Drives the retention class (Section 10). |
| `actor_id` | `BIGINT` | Yes | `USERS.id` of the actor. `NULL` for `SYSTEM` or unauthenticated attempts. |
| `actor_role` | `VARCHAR(32)` | No | Role at the moment of the event (`CITIZEN`, `OPERATOR`, `CLEANING_TEAM`, `ADMIN`, `SYSTEM`, `ANONYMOUS`). Stored so later role changes do not rewrite history. |
| `target_type` | `VARCHAR(32)` | Yes | `REPORT`, `USER`, `TEAM`, `ASSIGNMENT`, `IMAGE`, `CONFIG`, `AUDIT_PARTITION`, etc. |
| `target_id` | `VARCHAR(64)` | Yes | Identifier of the affected entity. |
| `action` | `VARCHAR(32)` | No | `CREATE`, `UPDATE`, `STATUS_CHANGE`, `DELETE`, `LOGIN`, `READ`, `EXPORT`, `PURGE`, `ARCHIVE`, etc. |
| `outcome` | `VARCHAR(16)` | No | `SUCCESS`, `FAILURE`, or `DENIED`. |
| `old_value` | `JSONB` | Yes | Previous state of changed fields only (e.g. `{"status":"IN_PROGRESS"}`). |
| `new_value` | `JSONB` | Yes | New state of changed fields only. |
| `reason` | `VARCHAR(500)` | Yes | Mandatory for `PRIORITY_OVERRIDDEN`, `REPORT_REOPENED`, `REPORT_REASSIGNED`, `AUDIT_LEGAL_HOLD_*`. |
| `request_id` | `UUID` | Yes | Correlation ID of the HTTP request (also written to application logs). |
| `source_ip_trunc` | `VARCHAR(45)` | Yes | Client IP with the last IPv4 octet / last 80 IPv6 bits zeroed (see Section 9). |
| `user_agent_hash` | `CHAR(64)` | Yes | SHA-256 of the user-agent string (not the raw string). |
| `prev_hash` | `CHAR(64)` | No | `record_hash` of the preceding record (`id − 1`). Genesis record uses 64 zeros. |
| `record_hash` | `CHAR(64)` | No | SHA-256 over the canonical serialisation of this record's fields plus `prev_hash` (Section 7.1). |

### 5.2 Reference DDL (PostgreSQL)

```sql
CREATE TABLE audit_log (
    id               BIGINT GENERATED ALWAYS AS IDENTITY,
    event_id         UUID         NOT NULL DEFAULT gen_random_uuid(),
    occurred_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    event_type       VARCHAR(64)  NOT NULL,
    category         VARCHAR(16)  NOT NULL
                     CHECK (category IN ('SECURITY','ADMIN','STATUS','AUDIT')),
    actor_id         BIGINT,
    actor_role       VARCHAR(32)  NOT NULL,
    target_type      VARCHAR(32),
    target_id        VARCHAR(64),
    action           VARCHAR(32)  NOT NULL,
    outcome          VARCHAR(16)  NOT NULL
                     CHECK (outcome IN ('SUCCESS','FAILURE','DENIED')),
    old_value        JSONB,
    new_value        JSONB,
    reason           VARCHAR(500),
    request_id       UUID,
    source_ip_trunc  VARCHAR(45),
    user_agent_hash  CHAR(64),
    prev_hash        CHAR(64)     NOT NULL,
    record_hash      CHAR(64)     NOT NULL,
    PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);

-- Monthly partitions, created ahead of time by a scheduled job
CREATE TABLE audit_log_2026_10 PARTITION OF audit_log
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');

CREATE INDEX idx_audit_occurred_at ON audit_log (occurred_at);
CREATE INDEX idx_audit_actor       ON audit_log (actor_id, occurred_at);
CREATE INDEX idx_audit_target      ON audit_log (target_type, target_id, occurred_at);
CREATE INDEX idx_audit_event_type  ON audit_log (event_type, occurred_at);
```

### 5.3 Supporting tables

```sql
-- Records the last hash of every purged partition so the remaining chain stays verifiable
CREATE TABLE audit_chain_checkpoint (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    partition_name   VARCHAR(64) NOT NULL UNIQUE,
    first_record_id  BIGINT      NOT NULL,
    last_record_id   BIGINT      NOT NULL,
    last_record_hash CHAR(64)    NOT NULL,
    record_count     BIGINT      NOT NULL,
    archive_uri      VARCHAR(500) NOT NULL,
    archive_sha256   CHAR(64)    NOT NULL,
    purged_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Tracks archive/purge lifecycle per partition
CREATE TABLE audit_partition_state (
    partition_name   VARCHAR(64) PRIMARY KEY,
    range_start      TIMESTAMPTZ NOT NULL,
    range_end        TIMESTAMPTZ NOT NULL,
    state            VARCHAR(16) NOT NULL
                     CHECK (state IN ('ACTIVE','CLOSED','ARCHIVED','PURGED')),
    legal_hold       BOOLEAN     NOT NULL DEFAULT FALSE,
    archived_at      TIMESTAMPTZ,
    purged_at        TIMESTAMPTZ
);
```

### 5.4 Schema requirements

| ID | Requirement |
|---|---|
| AUD-010 | Every audit record **MUST** contain all non-null fields in Section 5.1. |
| AUD-011 | `occurred_at` **MUST** be generated by the database server in UTC. Application- or client-supplied timestamps **MUST NOT** be used. |
| AUD-012 | `old_value` / `new_value` **MUST** contain only the fields that changed, and **MUST NOT** contain data prohibited by Section 9. |
| AUD-013 | `event_type`, `category`, `action`, and `outcome` **MUST** be validated against fixed enumerations in code and by `CHECK` constraints in the database where applicable. |
| AUD-014 | The audit table **MUST** be range-partitioned by `occurred_at` (monthly) to enable efficient archiving and purging. |

## 6. Immutability Rules

| ID | Requirement |
|---|---|
| AUD-020 | Audit records **MUST** be **append-only**: no `UPDATE` and no `DELETE` of any record in `audit_log` during its retention period, by any application or database account. |
| AUD-021 | The only permitted removal of audit records is the automated partition purge defined in Section 11, executed by a dedicated lifecycle role, after all purge criteria are satisfied. |
| AUD-022 | The audit table **MUST NOT** be exposed through any API endpoint that allows modification (`POST` to create arbitrary events, `PUT`, `PATCH`, `DELETE`). Audit records are created only by internal backend components. |
| AUD-023 | Corrections are made by appending a **new** record that references the original `event_id` in `new_value` (e.g. `{"corrects":"<event_id>"}`); the original is never edited. |
| AUD-024 | `STATUS_HISTORY` (proposal Section 15.2) **MUST** follow the same append-only rule. Each `STATUS_HISTORY` insert **MUST** be paired with a `REPORT_STATUS_CHANGED` audit record in the same transaction. `STATUS_HISTORY` remains the analytics-friendly table (response times, resolution rate); `audit_log` is the authoritative trail. |
| AUD-025 | Archived files in cold storage **MUST** be stored with write-once protection (object lock / retention policy where the storage provider supports it, otherwise bucket policy denying overwrite and delete to all application identities). |

## 7. Tamper-Prevention and Tamper-Detection Measures

Defence is layered: **prevent** modification at the database, **detect** it cryptographically, and **limit** who can touch the data at all.

### 7.1 Hash chain (detection)

| ID | Requirement |
|---|---|
| AUD-030 | Each record **MUST** store `prev_hash` (the previous record's `record_hash`) and `record_hash`. |
| AUD-031 | `record_hash` **MUST** be `SHA-256` over the UTF-8 bytes of a canonical serialisation of: `id`, `event_id`, `occurred_at` (ISO-8601 UTC, microsecond precision), `event_type`, `category`, `actor_id`, `actor_role`, `target_type`, `target_id`, `action`, `outcome`, `old_value`, `new_value`, `reason`, `request_id`, `source_ip_trunc`, `user_agent_hash`, `prev_hash`. Fields are joined with a fixed delimiter, `NULL` is serialised as an empty token, and JSON values use canonical form (sorted keys, no whitespace). |
| AUD-032 | Chain computation **MUST** be performed inside a database function invoked by the application (`append_audit_record(...)`) that takes a transaction-level advisory lock, reads the last `record_hash`, computes the new hash, and inserts. This guarantees a single linear chain even under concurrent requests. At MVP scale the serialisation cost is acceptable; this is a documented trade-off. |
| AUD-033 | An optional keyed hash (HMAC-SHA-256) **SHOULD** be used instead of plain SHA-256 when a secret is available, with the key held in a secret manager (not in the database, source code, or `application.yml`). This prevents an attacker with database write access from recomputing a valid chain. |

### 7.2 Database-level prevention

| ID | Requirement |
|---|---|
| AUD-034 | A `BEFORE UPDATE OR DELETE` trigger on `audit_log` (and every partition) **MUST** raise an exception, regardless of the calling role. Only the purge procedure (AUD-052) may bypass it, by dropping whole partitions rather than deleting rows. |
| AUD-035 | `TRUNCATE` on `audit_log` and its partitions **MUST** be revoked from all roles except the lifecycle role. |
| AUD-036 | The application's runtime database role **MUST** hold only `INSERT` (through the `append_audit_record` function) and `SELECT` on audit tables. It **MUST NOT** own the tables and **MUST NOT** hold `UPDATE`, `DELETE`, `TRUNCATE`, `DROP`, or `ALTER`. |
| AUD-037 | Table ownership **MUST** belong to a migration/admin role that is not used by the running application. |

Reference permissions:

```sql
REVOKE ALL ON audit_log FROM PUBLIC;
GRANT  SELECT ON audit_log TO cleanstreet_app;
GRANT  EXECUTE ON FUNCTION append_audit_record(...) TO cleanstreet_app;

-- Immutability trigger
CREATE FUNCTION audit_block_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only (% blocked)', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_immutable
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION audit_block_mutation();
```

### 7.3 Integrity verification (detection)

| ID | Requirement |
|---|---|
| AUD-038 | A scheduled job **MUST** verify the hash chain at least **daily** for records added since the last verified `id`, and **weekly** for the full hot-storage chain (starting from the latest checkpoint). |
| AUD-039 | On any mismatch the system **MUST** record `AUDIT_INTEGRITY_VIOLATION`, raise a high-severity alert to the administrator, and stop lifecycle jobs (archive/purge) until the violation is investigated. |
| AUD-040 | Before archiving, the partition's chain **MUST** be verified end to end; an unverified partition **MUST NOT** be archived or purged. |
| AUD-041 | Archive files **MUST** include a manifest containing partition name, first/last record `id`, record count, first `prev_hash`, last `record_hash`, and the SHA-256 of the data file. The manifest hash **MUST** be written to `audit_chain_checkpoint`. |

### 7.4 Application-level controls

| ID | Requirement |
|---|---|
| AUD-042 | Audit components **MUST** be internal Spring beans; no REST controller may accept caller-supplied audit event content. |
| AUD-043 | Audit-write code **MUST** be covered by automated tests that confirm updates and deletes are rejected (Section 13). |
| AUD-044 | Audit data **MUST** be included in database backups, and backups **MUST** be access-controlled to the same level as the live database. |
| AUD-045 | All transport to the database and object storage **MUST** use TLS (proposal Section 17: secure API communication). |

## 8. Access Control for Audit Data

| ID | Requirement |
|---|---|
| AUD-046 | Read access to audit records **MUST** be restricted to the `ADMIN` role. `OPERATOR`, `CLEANING_TEAM`, and `CITIZEN` roles **MUST NOT** read the global audit log. |
| AUD-047 | A citizen **MAY** see the status timeline of **their own report** (derived from `STATUS_HISTORY`, supporting the citizen-tracking workflow in proposal Section 16.1). This view **MUST NOT** expose actor identities of staff, IP data, or internal reasons. |
| AUD-048 | An operator **MAY** see the status timeline of reports within their scope, including who changed the status and when, but not security events. |
| AUD-049 | Every read through the audit API **MUST** itself be audited (`AUDIT_ACCESS`). |
| AUD-050 | Audit queries **MUST** be paginated and bounded by a mandatory time range to prevent bulk extraction. Exports **MUST** be restricted to `ADMIN` and audited as `DATA_EXPORT`. |
| AUD-051 | Role definitions and permission names **MUST** be taken from T_85ab37 so that audit access follows the central RBAC model. |

## 9. Data Minimisation and Privacy Rules

The proposal (Section 17) requires data minimisation, protection of location information, and protection of account information. Audit logs are a common leakage point, so the following apply.

| ID | Requirement |
|---|---|
| AUD-060 | Audit records **MUST NOT** contain: passwords, password hashes, authentication tokens, API keys, secrets, or session identifiers. |
| AUD-061 | Audit records **MUST NOT** contain image content or image bytes. Images are referenced by `IMAGES.id` only. |
| AUD-062 | Audit records **MUST NOT** contain exact GPS coordinates. Reports are referenced by `report_id`. Location changes, if audited, record only that the location field changed. |
| AUD-063 | Personal data in `old_value` / `new_value` (e.g. email on `USER_UPDATED`) **MUST** be limited to the changed field name and a masked or hashed value; full values **MUST NOT** be stored. |
| AUD-064 | IP addresses **MUST** be truncated before storage (IPv4: last octet zeroed; IPv6: last 80 bits zeroed). Raw IPs **MUST NOT** be written to the audit table. |
| AUD-065 | Free-text fields (`reason`) **MUST** be length-limited, and the UI **SHOULD** warn operators not to enter personal data. |
| AUD-066 | Audit records reference users by `actor_id`. When a user account is deleted or anonymised, `actor_id` remains (it is a pseudonymous key) and the USERS row is anonymised; audit records are **not** rewritten. |

## 10. Retention Schedule

Retention is defined per **category**. Values below are the standard for the MVP and pilot, and are stored in configuration (`audit.retention.*`) so they can be adjusted without code changes. Any change to them is itself an audited `CONFIG_CHANGED` event.

| Category | Examples | Hot storage (PostgreSQL) | Cold storage (archive) | Total retention | Rationale |
|---|---|---|---|---|---|
| `STATUS` | `REPORT_STATUS_CHANGED`, `REPORT_ASSIGNED`, `REPORT_RESOLVED` | 12 months | +24 months | **36 months** | Supports response-time and resolution analytics (proposal Section 11, features #9–#12) and dispute handling. |
| `SECURITY` | `AUTH_LOGIN`, `ACCESS_DENIED`, `AUTH_LOCKOUT` | 6 months | +18 months | **24 months** | Incident investigation window; limits retention of behavioural/IP-related data. |
| `ADMIN` | `RBAC_ROLE_CHANGED`, `CONFIG_CHANGED`, `PRIORITY_OVERRIDDEN`, `USER_*`, `TEAM_*`, `DATA_EXPORT` | 12 months | +48 months | **60 months** | Accountability for privileged actions and for changes to scoring weights. |
| `AUDIT` | `AUDIT_PURGE_EXECUTED`, `AUDIT_INTEGRITY_*` | 12 months | +48 months | **60 months** | Proof that lifecycle jobs ran and that integrity was checked. |

**Retention requirements**

| ID | Requirement |
|---|---|
| AUD-070 | Records **MUST NOT** be purged before the end of their category's total retention period. |
| AUD-071 | Records **MUST NOT** be retained beyond their category's total retention period unless a legal hold applies (data minimisation, proposal Section 17). |
| AUD-072 | Retention is evaluated per partition using the partition's **latest** `occurred_at`. A monthly partition containing mixed categories is therefore retained at the **longest** applicable category period in hot storage and split by category on archive (Section 11.2) so each category can be purged on its own schedule. |
| AUD-073 | Retention periods **MUST** be configurable and **MUST** have documented defaults equal to the table above. |
| AUD-074 | The retention of uploaded report images and location data is governed by the project's data-retention policy (proposal Section 17) and is **independent** of audit retention. Deleting an image **MUST** produce an audit record (`DATA_PURGED`, referencing `IMAGES.id` only). |

## 11. Automated Archive and Purge Criteria

### 11.1 Lifecycle

```
ACTIVE ──(month ends)──▶ CLOSED ──(hot period elapsed + verified)──▶ ARCHIVED ──(total retention elapsed + criteria met)──▶ PURGED
```

| State | Meaning |
|---|---|
| `ACTIVE` | Current month's partition, receiving writes. |
| `CLOSED` | Partition no longer receives writes; chain is final. |
| `ARCHIVED` | Exported to cold storage and verified; may still be present in hot storage until its hot period ends. |
| `PURGED` | Removed from hot storage; the archive is the only copy until total retention expires, after which the archive file is deleted by the same job. |

### 11.2 Archive criteria

A partition **MUST** be archived when **all** of the following are true:

| # | Criterion |
|---|---|
| 1 | The partition is `CLOSED` (its date range has fully elapsed). |
| 2 | Its age exceeds the **hot-storage period** of at least one category it contains. |
| 3 | The hash chain for the partition has been verified successfully (AUD-040). |
| 4 | No unresolved `AUDIT_INTEGRITY_VIOLATION` exists. |

Archive procedure:

1. Export the partition's records, **grouped by category**, to compressed newline-delimited JSON (`.jsonl.gz`).
2. Compute SHA-256 of each file and build the manifest (AUD-041).
3. Upload to the archive bucket under `audit-archive/{category}/{yyyy}/{mm}/…` with write-once protection (AUD-025).
4. Re-download (or read back checksum from the provider) and confirm the SHA-256 matches.
5. Insert a row in `audit_chain_checkpoint`, update `audit_partition_state` to `ARCHIVED`, and write `AUDIT_ARCHIVE_CREATED`.

### 11.3 Purge criteria

A partition (hot storage) or archive file (cold storage) **MUST** be purged only when **all** of the following are true:

| # | Criterion |
|---|---|
| 1 | The relevant retention period (hot period for hot purge; total retention for archive deletion) has fully elapsed for **every** category in the partition/file. |
| 2 | For hot purge: the archive exists, its checksum was verified, and a checkpoint row exists. |
| 3 | `legal_hold` is `FALSE` for the partition. |
| 4 | The hash chain was verified successfully within the last 24 hours. |
| 5 | No `AUDIT_INTEGRITY_VIOLATION` is open. |
| 6 | The job is running under the dedicated lifecycle role and the purge is not a manual ad-hoc request. |

Purge procedure:

1. Re-check criteria 1–5 inside a transaction.
2. Drop the partition (`DROP TABLE audit_log_YYYY_MM`) — **not** row-level `DELETE`.
3. Update `audit_partition_state` to `PURGED`.
4. Write `AUDIT_PURGE_EXECUTED` with partition name, record count, archive URI, and checksum.
5. The checkpoint row remains, so the chain of newer partitions can still be verified starting from the checkpoint's `last_record_hash`.

### 11.4 Lifecycle requirements

| ID | Requirement |
|---|---|
| AUD-080 | The archive/purge lifecycle **MUST** be implemented as scheduled jobs (default: nightly at 02:00 Africa/Cairo) with distributed locking (e.g. ShedLock) so only one instance runs at a time. |
| AUD-081 | Lifecycle jobs **MUST** be **idempotent**: re-running after a partial failure **MUST NOT** duplicate archives or purge unverified data. |
| AUD-082 | A failure at any step **MUST** abort that partition's processing, leave hot data intact, record the error, and alert the administrator. Purge **MUST** fail closed. |
| AUD-083 | Next-month partitions **MUST** be pre-created at least 7 days before use. If a partition is missing at write time, the insert **MUST** fail loudly (AUD-004) rather than fall into a default partition. |
| AUD-084 | Legal hold **MUST** be settable only by `ADMIN`, requires a `reason`, and is audited. A held partition **MUST NOT** be purged or its archive deleted. |
| AUD-085 | A dry-run mode **MUST** exist that reports which partitions *would* be archived or purged without changing anything. |
| AUD-086 | Manual deletion of audit data outside this procedure is **prohibited**. |

## 12. Backend Implementation Requirements (Spring Boot)

This section states constraints on the implementation, not the code itself.

| ID | Requirement |
|---|---|
| AUD-090 | A single `AuditService` (Spring `@Service`) **MUST** be the only component that writes audit records, delegating to the `append_audit_record` database function. |
| AUD-091 | Business services **MUST** publish a domain event (e.g. `ReportStatusChangedEvent`) inside their `@Transactional` method; an event listener annotated `@TransactionalEventListener(phase = BEFORE_COMMIT)` **MUST** write the audit record so that it commits or rolls back with the business change (AUD-002). |
| AUD-092 | Spring Security **MUST** be configured to publish authentication success/failure and access-denied events (`AuthenticationSuccessEvent`, `AbstractAuthenticationFailureEvent`, `AuthorizationDeniedEvent`, and a custom handler for rejected Firebase tokens) which are mapped to Section 4.1 events. |
| AUD-093 | A request filter **MUST** assign a `request_id` (UUID) per request, put it in the logging MDC, and make it available to the audit writer. |
| AUD-094 | Actor identity and role **MUST** be read from the `SecurityContext`, never from request parameters or body. |
| AUD-095 | Audit code **MUST** be isolated in its own package (e.g. `com.cleanstreet.audit`) with its own tests, and **MUST NOT** depend on controllers. |
| AUD-096 | Schema changes to audit tables **MUST** be made through versioned migrations (Flyway or Liquibase) run by the admin/migration role, never by Hibernate `ddl-auto`. `spring.jpa.hibernate.ddl-auto` **MUST** be `validate` or `none` in all non-test profiles. |
| AUD-097 | The `AuditLog` JPA entity **MUST** be mapped as read-only for application use (`@Immutable`, no setters, no `merge`/`remove` paths). |
| AUD-098 | Application logs (SLF4J) **MUST NOT** be treated as the audit trail; they are operational diagnostics only. Audit records go to the database. |

Suggested component layout:

```
com.cleanstreet.audit
├── AuditEventType.java        // enum of Section 4 event types
├── AuditCategory.java         // SECURITY | ADMIN | STATUS | AUDIT
├── AuditService.java          // sole writer, calls append_audit_record
├── AuditEventListener.java    // BEFORE_COMMIT listener for domain events
├── SecurityAuditListener.java // Spring Security events → audit
├── AuditQueryController.java  // ADMIN-only, read-only, paginated
├── lifecycle/
│   ├── AuditPartitionJob.java // pre-creates partitions
│   ├── AuditIntegrityJob.java // chain verification
│   ├── AuditArchiveJob.java   // archive per Section 11.2
│   └── AuditPurgeJob.java     // purge per Section 11.3
└── model/AuditLog.java        // @Immutable entity
```

## 13. Verification and Acceptance Criteria

The specification is considered implemented and accepted when every test below passes.

| # | Test | Expected result | Covers |
|---|---|---|---|
| T-01 | Change a report's status through the API | One `REPORT_STATUS_CHANGED` record with correct `old_status`, `new_status`, actor, and a `STATUS_HISTORY` row, both committed together | AUD-001, 002, 024 |
| T-02 | Force the audit insert to fail during a status change | Business change is rolled back; error and alert raised | AUD-002, 004 |
| T-03 | Submit invalid credentials | `AUTH_LOGIN` record with outcome `FAILURE`; no password data stored | AUD-003, 060 |
| T-04 | Access an admin endpoint as `CITIZEN` | `ACCESS_DENIED` record; HTTP 403 | AUD-003 |
| T-05 | Run `UPDATE audit_log …` as the application role | Rejected (permission denied / trigger exception) | AUD-020, 034, 036 |
| T-06 | Run `DELETE FROM audit_log …` as the application role and as the admin role | Rejected in both cases | AUD-020, 034 |
| T-07 | Modify one record directly in a test database by bypassing triggers, then run the integrity job | `AUDIT_INTEGRITY_VIOLATION` raised; archive/purge jobs halt | AUD-038, 039 |
| T-08 | Insert 1,000 audit events concurrently from multiple threads | Single unbroken chain; verification passes | AUD-032 |
| T-09 | Operator overrides a priority score without a reason | Request rejected (reason is mandatory) | `PRIORITY_OVERRIDDEN` rules |
| T-10 | Call the audit API as `OPERATOR` | HTTP 403 | AUD-046 |
| T-11 | Call the audit API as `ADMIN` | Records returned (paginated, time-bounded); `AUDIT_ACCESS` record created | AUD-049, 050 |
| T-12 | Scan stored `old_value`/`new_value`/`reason` for tokens, passwords, coordinates, and raw IPs using seeded test data | None found | AUD-060–064 |
| T-13 | Run archive job on a closed, verified partition | Archive file with manifest, checksum matches, checkpoint written, `AUDIT_ARCHIVE_CREATED` recorded | Section 11.2 |
| T-14 | Run purge on a partition before retention expires | Nothing purged | AUD-070 |
| T-15 | Run purge on an expired partition with archive verified | Partition dropped; checkpoint intact; `AUDIT_PURGE_EXECUTED` recorded; newer chain still verifies | Section 11.3 |
| T-16 | Run purge on an expired partition with `legal_hold = TRUE` | Nothing purged | AUD-084 |
| T-17 | Run purge when archive checksum does not match | Purge aborted (fail closed); alert raised | AUD-082 |
| T-18 | Re-run archive/purge jobs after a simulated mid-job crash | No duplicates, no data loss | AUD-081 |
| T-19 | Run lifecycle jobs in dry-run mode | Report produced; no data changed | AUD-085 |
| T-20 | Insert a record when next-month partition is missing | Insert fails loudly; alert raised | AUD-083 |

## 14. Traceability to the Project Proposal

| Proposal reference | How this specification addresses it |
|---|---|
| Section 17 — "Audit logging for important status changes, implemented via the STATUS_HISTORY table" | AUD-024: `STATUS_HISTORY` is append-only and paired with an audit record for every status change. |
| Section 17 — Authentication, role-based authorisation, access control | Section 4.1 (security events), Section 8 (access control), dependency on T_85ab37. |
| Section 17 — Protection of location information and user account information; data minimisation and retention | Section 9 (privacy rules) and Section 10 (retention schedule). |
| Section 16.2 — Operator may not close a report solely because the team marked it complete | `REPORT_STATUS_CHANGED`, `REPORT_RESOLVED`, `REPORT_REOPENED` events record the review decision and reason. |
| Section 16.3 — "AI assists, operator decides" | `PRIORITY_OVERRIDDEN` and `DUPLICATE_LINKED/UNLINKED` events record every human decision that departs from or confirms AI/rule output; `AI_ANALYSIS_WRITTEN` records the system's own output. |
| Section 11, Tier 2 — Configurable severity weight table, provisional pending calibration | `CONFIG_CHANGED` records every change to weights, so calibration history is traceable. |
| Section 15.2 — STATUS_HISTORY feeds response-time and resolution-rate analytics | Retained 36 months (Section 10) and preserved as a separate analytics table. |
| Section 23 — Security and privacy success criterion: no critical findings outstanding | Section 13 provides the test cases supporting this criterion for the audit component. |

## 15. Out of Scope

- Application/operational logging (debug, performance, error logs) — separate from the audit trail (AUD-098).
- A SIEM or external log-shipping integration (possible future phase).
- Blockchain or third-party notarisation of hashes.
- Audit of the AI model's internal inference steps (only its written results are audited).
- Legal-retention rules of a specific jurisdiction; retention values here are project standards pending confirmation (Section 16).

## 16. Open Items

| # | Item | Owner |
|---|---|---|
| 1 | Confirm retention periods in Section 10 with the Team Leader and the pilot operator (proposal Section 19, Operational risk) and against any national data-protection requirements that apply to the pilot. | Team Leader |
| 2 | Confirm that role names in A-2 match T_85ab37; update the `actor_role` values if they differ. | Back-end / Security |
| 3 | Confirm the archive storage provider (Firebase Storage vs. Amazon S3) and whether it supports object-lock retention (AUD-025). | Back-end / DevOps |
| 4 | Confirm the secret-management mechanism for the HMAC key (AUD-033). | Back-end / DevOps |

---

*End of document.*
