-- Applied at startup by training_content.register; review before deploying.
-- Additive only: study_plans and training_records (self-reported study) are unchanged.
-- Rollback: deploy previous code. Tables are then ignored; keep them as training history.
CREATE TABLE IF NOT EXISTS training_modules (
 organization_id TEXT NOT NULL, id TEXT NOT NULL, status TEXT NOT NULL, published_version INTEGER NOT NULL,
 draft TEXT NOT NULL, draft_version INTEGER NOT NULL, updated_by TEXT NOT NULL, updated_at TEXT NOT NULL,
 PRIMARY KEY(organization_id, id)
);
CREATE TABLE IF NOT EXISTS training_module_versions (
 organization_id TEXT NOT NULL, module_id TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL,
 published_by TEXT NOT NULL, published_at TEXT NOT NULL, PRIMARY KEY(organization_id, module_id, version)
);
CREATE TABLE IF NOT EXISTS training_assignments (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, module_id TEXT NOT NULL, module_version INTEGER NOT NULL,
 user_id TEXT NOT NULL, due_on TEXT, status TEXT NOT NULL, assigned_by TEXT NOT NULL, created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL, UNIQUE(organization_id, module_id, module_version, user_id)
);
CREATE TABLE IF NOT EXISTS training_attempts (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, user_id TEXT NOT NULL, module_id TEXT NOT NULL,
 module_version INTEGER NOT NULL, answers TEXT NOT NULL, score INTEGER NOT NULL, passed INTEGER NOT NULL, submitted_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS training_completions (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, user_id TEXT NOT NULL, module_id TEXT NOT NULL,
 module_version INTEGER NOT NULL, attempt_id TEXT NOT NULL, score INTEGER NOT NULL, completed_at TEXT NOT NULL,
 UNIQUE(organization_id, user_id, module_id, module_version)
);
