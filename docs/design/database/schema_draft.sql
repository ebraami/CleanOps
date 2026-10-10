-- =============================================================================
-- CleanOps / CleanStreet AI — PostgreSQL Relational Schema (Draft)
--
-- Implements the seven tables named in CleanStreet AI Proposal Section 15.2
-- (USERS, CATEGORIES, REPORTS, IMAGES, STATUS_HISTORY, CLEANING_TEAMS,
-- ASSIGNMENTS) and the indexes required by Section 15.3.
--
-- See erd-and-data-model.md for the full rationale behind every decision
-- in this file (table 6: "Design Decisions"). Anything not directly named
-- in the proposal (column types, enumerated value lists, ON DELETE
-- behaviour) is a PROPOSED MVP decision, called out in that document and
-- cross-referenced here by section number.
--
-- Target: PostgreSQL on Supabase, with the PostGIS extension available
-- (per ADR-001-ARCH-3TIER and Proposal Section 15.1).
--
-- Status: Draft for Team Leader review. Open questions: see
-- erd-and-data-model.md, Section 9 (Q1-Q3).
-- =============================================================================

begin;

-- -----------------------------------------------------------------------------
-- Extensions
-- -----------------------------------------------------------------------------
-- PostGIS: required for the spatial index on REPORTS (Proposal Section 15.3).
create extension if not exists postgis;

-- pgcrypto: required for gen_random_uuid(), used nowhere here directly since
-- USERS.id is populated from Supabase Auth (see erd-and-data-model.md, 6.1),
-- but kept available for any future uuid default in this schema.
create extension if not exists pgcrypto;

-- -----------------------------------------------------------------------------
-- Table: USERS
-- Purpose (Proposal 15.2): registered citizens who submit reports.
-- id is uuid to match Supabase Auth's auth.users.id (erd-and-data-model.md, 6.1).
-- -----------------------------------------------------------------------------
create table public.users (
    id         uuid        primary key,                -- matches auth.users.id (Supabase Auth)
    name       text        not null,
    email      text        not null unique,
    role       text        not null,
    created_at timestamptz not null default now(),      -- proposed (6.8): not in Figure 5, needed for audit/ordering

    constraint users_role_check
        check (role in ('CITIZEN', 'TEAM_MEMBER', 'OPERATOR', 'SUPERVISOR', 'ADMIN'))
        -- Value list reused verbatim from the already-approved
        -- Backend_Serverless_Architecture_and_API_Gateway_Design.md, Section 7.4.2
        -- (AuthContext.role). See erd-and-data-model.md, 6.2.
);

comment on table public.users is
    'Registered citizens (and staff) who authenticate via Supabase Auth. Proposal Section 15.2.';

-- -----------------------------------------------------------------------------
-- Table: CATEGORIES
-- Purpose (Proposal 15.2): fixed waste/issue types used to classify reports.
-- -----------------------------------------------------------------------------
create table public.categories (
    id   bigint generated always as identity primary key,
    name text   not null unique
);

comment on table public.categories is
    'Fixed waste/issue classification types. Proposal Section 15.2.';

-- -----------------------------------------------------------------------------
-- Table: CLEANING_TEAMS
-- Purpose (Proposal 15.2): cleaning teams responsible for execution, and
-- each team's working area.
-- Created before REPORTS/ASSIGNMENTS purely for DDL ordering; it has no
-- dependency on either.
-- -----------------------------------------------------------------------------
create table public.cleaning_teams (
    id   bigint generated always as identity primary key,
    name text   not null,
    area text   not null
    -- 'area' is kept as free text per Figure 5's two-column model
    -- (id, name, area). If the operator map needs a geographic service
    -- area rather than a text label, that is a change to raise with the
    -- Team Leader (out of scope here: not named in the proposal's ERD).
);

comment on table public.cleaning_teams is
    'Teams that execute cleaning work, with their working area. Proposal Section 15.2.';

-- -----------------------------------------------------------------------------
-- Table: REPORTS
-- Purpose (Proposal 15.2): the central table — every report with location,
-- description, priority score, and current status.
--
-- AI results (category_id, priority_score) are written back onto this same
-- row by an UPDATE, never into a separate table — consistent with Proposal
-- Section 15.1 and the approved Data Flow & Storage Architecture document.
-- -----------------------------------------------------------------------------
create table public.reports (
    id              bigint generated always as identity primary key,
    user_id         uuid        not null
        references public.users (id) on delete restrict,   -- proposed (6.7)
    category_id     bigint
        references public.categories (id) on delete restrict, -- proposed (6.7); nullable: AI classification may not have run yet
    latitude        double precision not null,
    longitude       double precision not null,
    description     text,
    priority_score  numeric,                                  -- nullable: not yet scored until AI analysis completes
    current_status  text        not null default 'NEW',        -- proposed default + value list (6.3)
    created_at      timestamptz not null default now(),

    -- Generated PostGIS column so the spatial index required by Proposal
    -- Section 15.3 is an actual spatial index, not a B-tree on two floats.
    -- See erd-and-data-model.md, 6.5.
    location geography(Point, 4326)
        generated always as (
            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
        ) stored,

    constraint reports_current_status_check
        check (current_status in ('NEW', 'ANALYZED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'REOPENED')),
        -- PROPOSED, open question Q1 in erd-and-data-model.md Section 9.
        -- NEW / ANALYZED / ASSIGNED are evidenced in the approved API Gateway
        -- document; IN_PROGRESS / RESOLVED / REOPENED are proposed to cover
        -- the operator workflow's remaining states (Proposal Figure 7).

    constraint reports_latitude_check  check (latitude  between -90  and 90),
    constraint reports_longitude_check check (longitude between -180 and 180)
);

comment on table public.reports is
    'Central report table: location, classification, priority score and status. Proposal Section 15.2.';

-- -----------------------------------------------------------------------------
-- Table: IMAGES
-- Purpose (Proposal 15.2): photo links per report; a report can hold more
-- than one image (before/after). Binaries live in Object Storage — this
-- table stores only the reference (Proposal Section 15.1).
-- -----------------------------------------------------------------------------
create table public.images (
    id          bigint generated always as identity primary key,
    report_id   bigint      not null
        references public.reports (id) on delete cascade,      -- proposed (6.7)
    storage_url text        not null,
    image_type  text        not null,
    uploaded_at timestamptz not null default now(),

    constraint images_image_type_check
        check (image_type in ('BEFORE', 'AFTER'))
        -- Wording taken directly from Proposal Section 15.1 ("before/after
        -- photos"). See erd-and-data-model.md, 6.6.
);

comment on table public.images is
    'Photo references (Object Storage URLs) per report; BEFORE = citizen submission, AFTER = completion evidence. Proposal Section 15.2.';

-- -----------------------------------------------------------------------------
-- Table: STATUS_HISTORY
-- Purpose (Proposal 15.2 / Section 17): audit log for every status change.
-- -----------------------------------------------------------------------------
create table public.status_history (
    id         bigint generated always as identity primary key,
    report_id  bigint      not null
        references public.reports (id) on delete cascade,      -- proposed (6.7)
    status     text        not null,
    changed_at timestamptz not null default now()

    -- No CHECK constraint mirroring reports_current_status_check is added
    -- here deliberately: an audit log must still be able to record a status
    -- value even if the live enum changes later. This keeps the audit trail
    -- (required by Proposal Section 17) append-only and tamper-evident
    -- regardless of future changes to reports.current_status's allowed set.
);

comment on table public.status_history is
    'Append-only audit log of every report status change. Proposal Sections 15.2 and 17.';

-- -----------------------------------------------------------------------------
-- Table: ASSIGNMENTS
-- Purpose (Proposal 15.2): links each report to the responsible team, with
-- assignment and completion timestamps.
--
-- "report_id" is UNIQUE rather than the report's own id, implementing the
-- "at most one assignment per report" reading of Figure 5's 1..1 edge.
-- See erd-and-data-model.md, 6.4.
-- -----------------------------------------------------------------------------
create table public.assignments (
    id           bigint generated always as identity primary key,
    report_id    bigint      not null unique
        references public.reports (id) on delete cascade,      -- proposed (6.7)
    team_id      bigint      not null
        references public.cleaning_teams (id) on delete restrict, -- proposed (6.7)
    assigned_at  timestamptz not null default now(),
    completed_at timestamptz,                                    -- nullable: not yet completed

    constraint assignments_completed_after_assigned_check
        check (completed_at is null or completed_at >= assigned_at)
);

comment on table public.assignments is
    'Links a report to the cleaning team responsible for it, with assignment/completion timestamps. Proposal Section 15.2.';

-- =============================================================================
-- Indexes (Proposal Section 15.3)
-- =============================================================================

-- "Spatial index on latitude/longitude in REPORTS (via PostGIS) — supports
-- nearby-report search for hotspot and duplicate detection."
create index idx_reports_location on public.reports using gist (location);

-- "Index on current_status — the operations dashboard filters on this constantly."
create index idx_reports_current_status on public.reports (current_status);

-- "Index on created_at — for analytics and chronological ordering of reports."
create index idx_reports_created_at on public.reports (created_at);

-- Foreign-key support indexes (not created automatically by PostgreSQL;
-- each backs a lookup/join path used by the already-approved API routes).
create index idx_reports_user_id        on public.reports (user_id);
create index idx_reports_category_id    on public.reports (category_id);
create index idx_images_report_id       on public.images (report_id);
create index idx_status_history_report_id on public.status_history (report_id);
create index idx_assignments_report_id  on public.assignments (report_id);
create index idx_assignments_team_id    on public.assignments (team_id);

commit;

-- =============================================================================
-- End of schema_draft.sql
--
-- Not included here (out of scope for this task, defined in
-- Backend_Serverless_Architecture_and_API_Gateway_Design.md instead):
--   - row-level security policies
--   - rate_limit_counters / rate_limit_policies
--   - api_idempotency
--   - outbox_events
--   - any PL/pgSQL RPC function (create_report, apply_ai_result, etc.)
-- =============================================================================
