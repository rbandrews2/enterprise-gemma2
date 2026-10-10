-- Applied at startup by messaging.register (via team_modules.register); review before deploying.
-- Additive only: existing fixture_messages rows and columns are unchanged.
-- Rollback: deploy previous code. These tables are then ignored; keep them to preserve
-- consent, opt-out and delivery audit history. Do not drop without a retention decision.
CREATE TABLE IF NOT EXISTS message_receipts (
 organization_id TEXT NOT NULL, message_id TEXT NOT NULL, recipient_id TEXT NOT NULL,
 ack_required INTEGER NOT NULL, acknowledged_at TEXT,
 PRIMARY KEY(message_id, recipient_id)
);
CREATE TABLE IF NOT EXISTS sms_contacts (
 organization_id TEXT NOT NULL, user_id TEXT NOT NULL, phone TEXT NOT NULL, status TEXT NOT NULL,
 consent_version TEXT NOT NULL, consented_at TEXT NOT NULL, verified_at TEXT, opted_out_at TEXT,
 code_hash TEXT, code_expires_at TEXT, code_attempts INTEGER NOT NULL,
 codes_day TEXT NOT NULL, codes_sent INTEGER NOT NULL, version INTEGER NOT NULL, updated_at TEXT NOT NULL,
 PRIMARY KEY(organization_id, user_id)
);
CREATE TABLE IF NOT EXISTS sms_outbox (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, purpose TEXT NOT NULL, reference_id TEXT NOT NULL,
 recipient_id TEXT NOT NULL, phone TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL, reason TEXT NOT NULL,
 attempts INTEGER NOT NULL, next_attempt_at TEXT NOT NULL, lease_until TEXT,
 provider_sid TEXT UNIQUE, provider_status TEXT, error_code TEXT,
 created_by TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(organization_id, purpose, reference_id, recipient_id)
);
CREATE TABLE IF NOT EXISTS sms_events (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, outbox_id TEXT, source TEXT NOT NULL,
 event TEXT NOT NULL, detail TEXT NOT NULL, actor_id TEXT, occurred_at TEXT NOT NULL
);
