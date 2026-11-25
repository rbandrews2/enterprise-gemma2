# Enterprise Equipment Locator

Enterprise members and admins can place equipment, view outstanding placements across their organization, and mark an entire placement quantity as retrieved. Core accounts cannot list or change placements. Coordinates are manually reported locations, with no GPS tracker or employee tracking.

A placement requires a preset equipment type or a custom name, a positive whole quantity, and either a complete coordinate pair or a street address, city and region. Address mode uses the workspace's Google Maps JavaScript loader and Geocoding service to resolve a single street-level match before saving. Map display requires the configured Maps browser key. The list and coordinate submissions remain available when the map provider is unavailable and the WZOS server is reachable. Markers group equipment at identical coordinates and display the equipment types and quantities when opened.

## Database and release

The startup DDL in `services/workspace_preview/equipment_locator.py` creates the additive `equipment_placements` table. It stores the submitted location, equipment type, custom name and quantity, along with placement and retrieval identities and timestamps. The primary key is organization and placement ID. Retrying the same placement or pickup preserves the original record. Older app versions can run with this table present. Preserve it on rollback to retain field inventory.

SQLite and disposable PostgreSQL 16 tests cover input validation, shared visibility within an organization, cross-organization isolation, Core denial, retries and retrieval. A mobile-sized Chrome check used a synthetic member account and simulated Google Maps responses to exercise address and coordinate entry, coincident markers, reopening and retrieval. Verify the target origin's Maps and Geocoding permissions during the shared-environment release check.
