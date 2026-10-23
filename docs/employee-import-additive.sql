-- Additive only. Keep tables on application rollback; no existing tables changed.
CREATE TABLE IF NOT EXISTS employee_roster (
  organization_id TEXT NOT NULL, email TEXT NOT NULL,
  employee_number TEXT NOT NULL, name TEXT NOT NULL, phone TEXT NOT NULL,
  import_id TEXT NOT NULL, created_at TEXT NOT NULL,
  PRIMARY KEY (organization_id,email), UNIQUE (organization_id,employee_number)
);
CREATE TABLE IF NOT EXISTS employee_import_batches (
  id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, actor_id TEXT NOT NULL,
  payload TEXT NOT NULL, fingerprint TEXT NOT NULL, expires_at TEXT NOT NULL,
  receipt TEXT
);
