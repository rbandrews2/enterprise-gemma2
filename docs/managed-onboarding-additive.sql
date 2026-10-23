-- Additive only. Retain on rollback. No password fields.
CREATE TABLE IF NOT EXISTS managed_accounts (user_id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,username TEXT NOT NULL UNIQUE,email TEXT NOT NULL UNIQUE,created_by TEXT NOT NULL,request_id TEXT NOT NULL,fingerprint TEXT NOT NULL,state TEXT NOT NULL,password_changed INTEGER NOT NULL,created_at TEXT NOT NULL,UNIQUE(organization_id,request_id));
CREATE TABLE IF NOT EXISTS organization_creation_grants (id TEXT PRIMARY KEY,email TEXT NOT NULL,edition TEXT NOT NULL,seat_limit INTEGER NOT NULL,expires_at TEXT NOT NULL,organization_id TEXT,used_by TEXT);
CREATE TABLE IF NOT EXISTS managed_login_limits (key TEXT PRIMARY KEY,window_start INTEGER NOT NULL,attempts INTEGER NOT NULL);
