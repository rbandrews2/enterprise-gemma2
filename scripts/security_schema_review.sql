-- REVIEW ONLY. The application executes these additive statements at startup.
-- Do not drop these tables on rollback: retain holds, incidents and audit history.

CREATE TABLE IF NOT EXISTS security_incidents (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,code TEXT NOT NULL,severity TEXT NOT NULL,target_type TEXT NOT NULL,target_id TEXT NOT NULL,fingerprint TEXT NOT NULL,status TEXT NOT NULL,containment TEXT NOT NULL,version INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS security_incidents_org_status ON security_incidents(organization_id,status,updated_at);
CREATE TABLE IF NOT EXISTS security_actions (id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,incident_id TEXT NOT NULL,actor_id TEXT NOT NULL,action TEXT NOT NULL,reason TEXT NOT NULL,occurred_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS security_actions_org_actor_time ON security_actions(organization_id,actor_id,occurred_at);
CREATE INDEX IF NOT EXISTS security_actions_incident ON security_actions(organization_id,incident_id,occurred_at);
CREATE TABLE IF NOT EXISTS security_file_states (organization_id TEXT NOT NULL,file_id TEXT NOT NULL,sha256 TEXT NOT NULL,status TEXT NOT NULL,hold INTEGER NOT NULL,scanner TEXT NOT NULL,scanned_at TEXT,PRIMARY KEY(organization_id,file_id));
CREATE TABLE IF NOT EXISTS security_alert_reads (organization_id TEXT NOT NULL,user_id TEXT NOT NULL,incident_id TEXT NOT NULL,version INTEGER NOT NULL,PRIMARY KEY(organization_id,user_id,incident_id));
