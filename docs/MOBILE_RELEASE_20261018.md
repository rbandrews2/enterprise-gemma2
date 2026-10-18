# Mobile / personal weather public release — October 18

Authorized by Ray: update the live app with the new feature and mobile look.
Runtime candidate: c944173ed419ca664a3c11283af2c200ef8587bf. Includes mobile Home for both roles, location-based forecast, retained-permission guards and default-off Smart Field Voice implementation.

Existing service only: wzos-v2-accounts, us-central1. Preserve identity, secret bindings, resource limits, database/storage, ingress, billing/SMS and hourly weather settings. No new roles, provider activation, media sessions, customer sends or charges. Voice flags remain off pending separate activation and pilot.

Additive startup DDL is disclosed in SMART_FIELD_VOICE.md: field_voice_drafts table and organization/owner index. No existing column/data changes. Require exact-candidate PostgreSQL and Node gates, read-only schema compatibility, recent Cloud SQL backup, immutable image, no-traffic readiness/configuration comparison, then public asset/auth checks. Automatic rollback routes traffic to upgrade-live-bf9f524; additive tables stay intact. Existing reports and billing compatibility are preserved.

Run release_mobile_home.sh gate/build/deploy with a private evidence root. It must contain source at c944173 and check_release.py copied from check_mobile_release.py. Cloud Shell evidence pointer: $HOME/wzos-mobile-release-path.txt. Simulator is excluded from deployment (script-only local route); preview mode stays disabled in production.

## Verified release gates
Exact c944173 cloud gates: PostgreSQL831 PASS (365.542 seconds), Node148 PASS; zero failures/errors/skips. Read-only live schema and successful-backup-within-24h checks PASS. Build submitted as 9caba93c-4338-4f90-a46c-c8e24c502004. No public traffic changed yet.


## Deployment accepted

Live revision wzos-v2-accounts-mobile-c944173 serves 100% of traffic.
Image: us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-accounts@sha256:e9b8085ca49aa6d8236df0b3174ce57c82f2d86d15b72caf0063a1d31c7ea852
Public version: 4ac54119f08f1aea7fc1152f.

Staged Ready, image digest, runtime identity/resources/storage/secrets/flags, ingress and traffic-preservation checks PASS. Public hashes for 16 changed/existing assets, HTML/mobile onboarding references, CSP/Daily hosts and four anonymous API boundaries PASS. Final traffic check PASS. Live mobile browser showed the intended vertical Home, opened Navigation with start/destination fields and Google Maps guidance, and returned Home successfully. Screenshot: ignored .local-data/live-mobile-home-20261018.png. Browser viewport reset afterward.

Only field_voice_drafts was missing before startup; existing columns compatible. Proxy stopped after read-only inspection. No temporary IAM or scheduled resources created. Voice processing remains OFF; Android retained/revoked permissions, real weather movement and ten-recording Speech/Gemma pilot remain outstanding. Existing hourly monitor and provider configuration preserved.
