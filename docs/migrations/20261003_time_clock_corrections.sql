-- Time Clock: admin corrections audit and offline submissions review.
-- Prepared 2026-10-03 on branch claude/time-clock. NOT applied to any shared database.
--
-- Review note: services/workspace_preview/timeclock.py runs these same statements
-- (CREATE ... IF NOT EXISTS) at application startup, as every other workspace table
-- does. Deploying the code is therefore what applies this DDL. Apply or review it
-- deliberately before deploying to a shared database; it is additive only.
--
-- Existing tables preview_shifts and preview_clock_events are unchanged. Shift
-- payload JSON gains optional keys (source, correction_count, last_changed_at,
-- last_changed_by); older rows without them read as server_recorded.
-- PostgreSQL and SQLite compatible.

CREATE TABLE IF NOT EXISTS time_corrections (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    shift_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    admin_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    kind TEXT NOT NULL,                -- correction | manual_entry
    occurred_at TEXT NOT NULL,         -- server UTC ISO-8601
    reason TEXT NOT NULL,
    from_version INTEGER NOT NULL,     -- 0 for manual_entry
    to_version INTEGER NOT NULL,
    before_payload TEXT,               -- NULL for manual_entry
    after_payload TEXT NOT NULL,
    resolves TEXT NOT NULL,            -- JSON array of offline submission ids
    response TEXT NOT NULL,            -- stored idempotent response
    UNIQUE (organization_id, admin_id, request_id)
);
CREATE INDEX IF NOT EXISTS time_corrections_shift ON time_corrections (organization_id, shift_id);

CREATE TABLE IF NOT EXISTS time_offline_submissions (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    action TEXT NOT NULL,
    payload TEXT NOT NULL,
    captured_at TEXT NOT NULL,         -- device clock, unverified
    stated_at TEXT,                    -- device clock, user-stated, unverified
    device_submitted_at TEXT NOT NULL, -- device clock at submission
    received_at TEXT NOT NULL,         -- server UTC
    device_offset_seconds INTEGER NOT NULL,
    estimated_at TEXT NOT NULL,        -- (stated_at or captured_at) + offset, capped at received_at
    status TEXT NOT NULL,              -- pending | applied | rejected | duplicate
    resolved_by TEXT,
    resolved_at TEXT,
    resolution_reason TEXT,
    resolution_ref TEXT,               -- time_corrections.id when applied
    resolved_shift_id TEXT,
    UNIQUE (organization_id, employee_id, request_id)
);
CREATE INDEX IF NOT EXISTS time_offline_status ON time_offline_submissions (organization_id, status, estimated_at);

-- Rollback (only if no audit data must be retained):
-- DROP TABLE time_offline_submissions; DROP TABLE time_corrections;
