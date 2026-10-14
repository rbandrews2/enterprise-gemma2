-- Additive startup DDL. Deployment applies these statements. No existing tables altered.
CREATE TABLE IF NOT EXISTS hub_notes (organization_id TEXT NOT NULL,id TEXT NOT NULL,author_id TEXT NOT NULL,body TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(organization_id,id));
CREATE TABLE IF NOT EXISTS hub_preferences (organization_id TEXT PRIMARY KEY,version INTEGER NOT NULL,hidden_modules TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS hub_status_checks (organization_id TEXT NOT NULL,kind TEXT NOT NULL,status TEXT NOT NULL,explanation TEXT NOT NULL,source TEXT NOT NULL,checked_at TEXT NOT NULL,expires_at TEXT NOT NULL,PRIMARY KEY(organization_id,kind));
CREATE TABLE IF NOT EXISTS integration_credentials (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,creator_id TEXT NOT NULL,name TEXT NOT NULL,token_hash TEXT NOT NULL UNIQUE,scopes TEXT NOT NULL,created_at TEXT NOT NULL,expires_at TEXT NOT NULL,revoked_at TEXT);
CREATE TABLE IF NOT EXISTS integration_usage (organization_id TEXT NOT NULL,minute TEXT NOT NULL,requests INTEGER NOT NULL,PRIMARY KEY(organization_id,minute));
CREATE TABLE IF NOT EXISTS hub_audit (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,actor_id TEXT NOT NULL,action TEXT NOT NULL,target_id TEXT NOT NULL,occurred_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS hub_audit_org_action_time ON hub_audit(organization_id,action,occurred_at);
