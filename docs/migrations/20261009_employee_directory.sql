-- Applied at startup by employees.register; review before deploying.
-- Roll back code without dropping these tables or losing employee history.
CREATE TABLE IF NOT EXISTS employee_profiles (
 organization_id TEXT NOT NULL, user_id TEXT NOT NULL,
 employee_number TEXT NOT NULL, payload TEXT NOT NULL,
 version INTEGER NOT NULL, updated_at TEXT NOT NULL,
 PRIMARY KEY(organization_id,user_id), UNIQUE(organization_id,employee_number)
);
CREATE TABLE IF NOT EXISTS employee_qualifications (
 organization_id TEXT NOT NULL, user_id TEXT NOT NULL,
 qualification_id TEXT NOT NULL, payload TEXT NOT NULL,
 version INTEGER NOT NULL, updated_at TEXT NOT NULL,
 PRIMARY KEY(organization_id,user_id,qualification_id)
);
CREATE TABLE IF NOT EXISTS employee_history (
 organization_id TEXT NOT NULL, user_id TEXT NOT NULL,
 record_key TEXT NOT NULL, version INTEGER NOT NULL,
 payload TEXT NOT NULL, actor_id TEXT NOT NULL, saved_at TEXT NOT NULL,
 PRIMARY KEY(organization_id,user_id,record_key,version)
);
