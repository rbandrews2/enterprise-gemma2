-- Applied at startup by dispatch.register (account workspace only); review before deploying.
-- Additive only. Reads employee_profiles/employee_qualifications (20261009_employee_directory.sql),
-- module_records, preview_orders, fixture_messages, message_receipts and sms_outbox; changes none.
-- Rollback: deploy previous code. Tables are then ignored; keep them as the dispatch audit trail.
CREATE TABLE IF NOT EXISTS dispatch_requirements (
 organization_id TEXT NOT NULL, order_id TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL,
 updated_by TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(organization_id, order_id)
);
CREATE TABLE IF NOT EXISTS dispatch_plans (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, order_id TEXT NOT NULL, status TEXT NOT NULL,
 version INTEGER NOT NULL, payload TEXT NOT NULL, created_by TEXT NOT NULL, created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL, approved_by TEXT, approved_at TEXT, approval_request_id TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS dispatch_assignments (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, plan_id TEXT NOT NULL, order_id TEXT NOT NULL,
 user_id TEXT NOT NULL, role_id TEXT NOT NULL, status TEXT NOT NULL, starts_at TEXT NOT NULL, ends_at TEXT NOT NULL,
 message_id TEXT, responded_at TEXT, response_note TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dispatch_events (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, order_id TEXT NOT NULL, plan_id TEXT,
 actor_id TEXT NOT NULL, event TEXT NOT NULL, detail TEXT NOT NULL, occurred_at TEXT NOT NULL
);
