# Mobile / personal weather public release — October 18

Authorized by Ray: update the live app with the new feature and mobile look.
Runtime candidate: c944173ed419ca664a3c11283af2c200ef8587bf. Includes mobile Home for both roles, location-based forecast, retained-permission guards and default-off Smart Field Voice implementation.

Existing service only: wzos-v2-accounts, us-central1. Preserve identity, secret bindings, resource limits, database/storage, ingress, billing/SMS and hourly weather settings. No new roles, provider activation, media sessions, customer sends or charges. Voice flags remain off pending separate activation and pilot.

Additive startup DDL is disclosed in SMART_FIELD_VOICE.md: field_voice_drafts table and organization/owner index. No existing column/data changes. Require exact-candidate PostgreSQL and Node gates, read-only schema compatibility, recent Cloud SQL backup, immutable image, no-traffic readiness/configuration comparison, then public asset/auth checks. Automatic rollback routes traffic to upgrade-live-bf9f524; additive tables stay intact. Existing reports and billing compatibility are preserved.

Run release_mobile_home.sh gate/build/deploy with a private evidence root. It must contain source at c944173 and check_release.py copied from check_mobile_release.py. Cloud Shell evidence pointer: $HOME/wzos-mobile-release-path.txt. Simulator is excluded from deployment (script-only local route); preview mode stays disabled in production.
