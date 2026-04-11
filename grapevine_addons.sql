-- ============================================================
-- GRAPEVINE — vNext Addons
-- Safe additions to live schema | April 2026
-- Run in Supabase SQL Editor — idempotent
-- ============================================================
-- Scope: 3 targeted additions only.
-- Does NOT touch existing columns, CHECK constraints, or RLS.
-- Does NOT implement users/projects/auth — single-tenant V4G.
-- ============================================================

-- ─── ADDON 1: APPROVAL METADATA COLUMNS ─────────────────────
-- Adds who/when approved to grapevine_notes.
-- Uses TEXT (not UUID) — no users table in V4G schema.
-- Actor values: 'chris.raman' / 'intel_capture_v1' / 'analyst' etc.

ALTER TABLE grapevine_notes
  ADD COLUMN IF NOT EXISTS reviewed_by   TEXT,
  ADD COLUMN IF NOT EXISTS reviewed_at   TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS approved_by   TEXT,
  ADD COLUMN IF NOT EXISTS approved_at   TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS approval_note TEXT;

-- ─── ADDON 2: AUDIT LOG TABLE ────────────────────────────────
-- Lightweight provenance trail for state changes on grapevine_notes.
-- Named grapevine_audit_log (not audit_log) to avoid collisions.

CREATE TABLE IF NOT EXISTS grapevine_audit_log (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  table_name  TEXT        NOT NULL,
  record_id   UUID        NOT NULL,
  action      TEXT        NOT NULL,  -- INSERT / UPDATE / DELETE
  actor       TEXT,                  -- created_by string from the note
  payload     JSONB       NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_gal_record
  ON grapevine_audit_log (record_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_gal_action
  ON grapevine_audit_log (action, created_at DESC);

-- RLS: service role full access, anon read-only
ALTER TABLE grapevine_audit_log ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'grapevine_audit_log' AND policyname = 'gal_service_all'
  ) THEN
    EXECUTE 'CREATE POLICY gal_service_all ON grapevine_audit_log
      FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE)';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'grapevine_audit_log' AND policyname = 'gal_anon_select'
  ) THEN
    EXECUTE 'CREATE POLICY gal_anon_select ON grapevine_audit_log
      FOR SELECT TO anon USING (TRUE)';
  END IF;
END $$;

-- ─── ADDON 3: AUDIT TRIGGER ON GRAPEVINE_NOTES ───────────────
-- Fires on every state change. Logs status + review transitions only
-- (not full row — keeps payload small and focused).

CREATE OR REPLACE FUNCTION grapevine_audit_note_change()
RETURNS TRIGGER AS $$
DECLARE
  v_record_id UUID;
  v_actor     TEXT;
  v_payload   JSONB;
BEGIN
  v_record_id := COALESCE(NEW.note_id, OLD.note_id);
  v_actor     := COALESCE(NEW.created_by, OLD.created_by, 'system');

  IF TG_OP = 'INSERT' THEN
    v_payload := jsonb_build_object(
      'note_type',    NEW.note_type,
      'status',       NEW.status,
      'review_status',NEW.review_status,
      'capture_origin',NEW.capture_origin
    );
  ELSIF TG_OP = 'UPDATE' THEN
    v_payload := jsonb_build_object(
      'status_old',        OLD.status,
      'status_new',        NEW.status,
      'review_old',        OLD.review_status,
      'review_new',        NEW.review_status,
      'sensitivity_old',   OLD.sensitivity_level,
      'sensitivity_new',   NEW.sensitivity_level,
      'approved_by',       NEW.approved_by,
      'approved_at',       NEW.approved_at
    );
  ELSIF TG_OP = 'DELETE' THEN
    v_payload := jsonb_build_object(
      'title',         OLD.title,
      'status',        OLD.status,
      'note_type',     OLD.note_type
    );
  END IF;

  INSERT INTO grapevine_audit_log (table_name, record_id, action, actor, payload)
  VALUES ('grapevine_notes', v_record_id, TG_OP, v_actor, v_payload);

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_grapevine_notes ON grapevine_notes;
CREATE TRIGGER trg_audit_grapevine_notes
  AFTER INSERT OR UPDATE OR DELETE ON grapevine_notes
  FOR EACH ROW EXECUTE FUNCTION grapevine_audit_note_change();

-- ─── VERIFICATION ────────────────────────────────────────────

SELECT 'approval columns' AS check_name,
  COUNT(*) FILTER (WHERE column_name = 'reviewed_by') AS reviewed_by,
  COUNT(*) FILTER (WHERE column_name = 'approved_by') AS approved_by,
  COUNT(*) FILTER (WHERE column_name = 'approval_note') AS approval_note
FROM information_schema.columns
WHERE table_name = 'grapevine_notes';

SELECT 'audit_log table' AS check_name,
  EXISTS (SELECT 1 FROM information_schema.tables
          WHERE table_name = 'grapevine_audit_log') AS exists;

SELECT 'audit trigger' AS check_name,
  EXISTS (SELECT 1 FROM information_schema.triggers
          WHERE trigger_name = 'trg_audit_grapevine_notes') AS exists;

-- ─── DONE ────────────────────────────────────────────────────
-- Three clean additions. No existing columns, constraints or
-- RLS policies were modified.
-- ============================================================
