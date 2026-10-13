-- Reviewed additive startup schema for paid-seat licensing.
-- Applied by Accounts initialization; no existing rows/tables rewritten.
CREATE TABLE IF NOT EXISTS activation_entitlements (
    activation_hash TEXT PRIMARY KEY,
    seat_limit INTEGER NOT NULL CHECK(seat_limit > 0),
    purchaser_email TEXT
);
CREATE TABLE IF NOT EXISTS organization_entitlements (
    organization_id TEXT PRIMARY KEY,
    activation_hash TEXT NOT NULL UNIQUE,
    seat_limit INTEGER NOT NULL CHECK(seat_limit > 0)
);
-- Sandbox commerce only: applied only when Purchases is explicitly instantiated.
CREATE TABLE IF NOT EXISTS purchase_requests (
    id TEXT PRIMARY KEY, email TEXT NOT NULL, offer_id TEXT NOT NULL,
    edition TEXT NOT NULL CHECK(edition IN ('core','enterprise')),
    seats INTEGER NOT NULL CHECK(seats > 0), expected_items TEXT NOT NULL,
    expected_cents INTEGER NOT NULL, session_id TEXT UNIQUE,
    status TEXT NOT NULL, activation_hash TEXT UNIQUE, sealed_code TEXT
);
CREATE TABLE IF NOT EXISTS purchase_events (
    event_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, processed_at TEXT NOT NULL
);
-- Rollback: use the prior immutable application image and retain these tables.
-- Never delete entitlements or purchase history as an application rollback.
