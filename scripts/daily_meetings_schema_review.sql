-- Additive startup DDL. Rollback code/traffic; preserve these rows.
CREATE TABLE IF NOT EXISTS daily_meeting_rooms (
 organization_id TEXT NOT NULL, record_id TEXT NOT NULL,
 record_version INTEGER NOT NULL, room_name TEXT NOT NULL,
 expires_at INTEGER NOT NULL, state TEXT NOT NULL,
 PRIMARY KEY(organization_id,record_id)
);
