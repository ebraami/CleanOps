-- =============================================================================
-- Migration 01: Initialise users table
-- Task:    PostgreSQL Database Setup & Users Migration
-- Package: P03 / Package 01 - Authentication & Foundation Baseline
-- Run:     psql -d cleanops_db -f backend/migrations/01_init_users.sql
-- Verify:  \d public.users
--          INSERT INTO public.users (firebase_uid, name, email, role)
--          VALUES ('123', 'Test', 't@t.com', 'SUPERUSER');   -- must FAIL (check_user_role)
-- Idempotent: safe to re-run (IF NOT EXISTS on every object).
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.users (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    name         VARCHAR(255) NOT NULL,
    email        VARCHAR(255) UNIQUE NOT NULL,
    role         VARCHAR(50)  NOT NULL DEFAULT 'CITIZEN',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT check_user_role CHECK (role IN ('CITIZEN', 'OPERATOR', 'TEAM_MEMBER'))
);

CREATE INDEX IF NOT EXISTS idx_users_firebase_uid ON public.users(firebase_uid);
CREATE INDEX IF NOT EXISTS idx_users_email        ON public.users(email);
