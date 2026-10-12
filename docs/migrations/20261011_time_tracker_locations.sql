-- Additive startup migration. Review and PostgreSQL gate precede deployment.
-- Roll back application code first; preserve captured evidence pending retention review.
CREATE TABLE IF NOT EXISTS time_location_events (
    organization_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    shift_id TEXT,
    captured_at TEXT NOT NULL,
    received_at TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY (organization_id, employee_id, request_id)
);
CREATE INDEX IF NOT EXISTS time_location_shift
    ON time_location_events (organization_id, shift_id, captured_at);
