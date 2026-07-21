-- 004_sync_public_schema_columns.sql
--
-- FIX-008 (2026-07-21): The legacy `public` schema still contains copies of
-- the application tables (historical single-schema layout). The API now
-- resolves tables via `SET search_path TO {demo|pilot}, public`, but a
-- connection whose search_path was never set (see FIX-008 root cause in
-- backend/app/database.py) resolves unqualified table names to `public`.
-- When the public tables drift behind the ORM models, such stray statements
-- fail with UndefinedColumnError (production incident: inquiry creation 500
-- "column inquiries.campaign_id does not exist").
--
-- This migration re-syncs the public tables with the model columns that
-- were added to demo/pilot only. It is a defense-in-depth measure: the
-- primary fix pins every request to a connection with the correct
-- search_path, so the API should never touch the public tables at all.
--
-- Idempotent: safe to run on every deploy.

ALTER TABLE public.inquiries ADD COLUMN IF NOT EXISTS campaign_id UUID;
ALTER TABLE public.inquiries ADD COLUMN IF NOT EXISTS campaign_title VARCHAR(255);
ALTER TABLE public.residents ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);
