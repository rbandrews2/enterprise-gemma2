# Account and storage cost estimate

Prepared 2026-09-24. USD, us-central1, 730 hours/month, on-demand rates. Planning estimate only; no resources authorized or provisioned. Ray selected local preparation and pricing before provisioning.

## Proposed foundation

Reuse the PostgreSQL adapter for organization-scoped operational records, private Cloud Storage for attachments, and Firebase Authentication/Identity Platform for verified accounts. Supabase is not a dependency of this runtime. Keep local SQLite preview and synthetic tests available without cloud costs.

| Component | Restricted staging example | Initial production example |
| --- | ---: | ---: |
| SQL compute | Shared db-g1-small: $25.55/month | 2 vCPU + 7.5 GiB: $98.62/month |
| SSD capacity | 10 GiB: $1.70/month | 20 GiB: $3.40/month |
| Used backup storage assumption | 10 GiB: $0.80/month | 20 GiB: $1.60/month |
| Standard regional object storage | 10 GiB: $0.20/month | 100 GiB: $2.00/month |
| **Database and stored-data subtotal** | **$28.25/month** | **$105.62/month** |

SQL assumptions: shared compute $0.035/hour; dedicated compute $0.0413/vCPU-hour plus $0.007/GiB-hour; SSD approximately $0.17/GiB-month; used backups approximately $0.08/GiB-month. Shared-core instances have no Cloud SQL SLA and are proposed only for staging. [Cloud SQL pricing](https://cloud.google.com/sql/pricing).

Regional Standard object storage is approximately $0.02/GiB-month. Requests, downloads, retained versions and soft-deleted objects can add charges. [Cloud Storage pricing](https://cloud.google.com/storage/pricing).

For production high availability, the same SQL example has approximately $197.25 compute + $6.80 SSD + $1.60 assumed backups + $2 object storage = **$207.65/month**. This is a pricing comparison, not a capacity or availability approval. Confirm tier eligibility, region and backup settings in the final configuration.

## Additional usage costs

- Email/password authentication falls under Identity Platform Tier 1, whose first 50,000 monthly active users are free; phone authentication/MFA and other tiers have different charges. [Identity Platform pricing](https://cloud.google.com/identity-platform/pricing).
- US Twilio long-code outbound SMS starts at $0.0083 per segment: 1,000 segments = $8.30. Outbound MMS starts at $0.022: 1,000 messages = $22. Carrier fees, number rental, registration, incoming replies and applicable failed-message fees are additional. Long or Unicode texts may use multiple segments. [Twilio US pricing](https://www.twilio.com/en-us/sms/pricing/us).
- Cloud Run, builds, image registry, logging, Secret Manager, networking and monitoring are additional. Actual runtime cost requires request count, CPU/memory, duration, concurrency and minimum-instance settings. Free allowances may already be consumed elsewhere. [Cloud Run pricing](https://cloud.google.com/run/pricing), [Secret Manager pricing](https://cloud.google.com/secret-manager/pricing).
- Atlas inference, Maps/route calls, email delivery, taxes and existing project resources are excluded. These subtotals are **not total WZOS operating costs**.

## Decision and next gates

Remain local at no new managed-resource cost. Before provisioning: confirm PostgreSQL integration tests, private file-store behavior, verified sign-in, backup/restore, expected traffic and a monthly budget. Then produce the exact resource configuration for review. Budget alerts do not cap spending. Set application quotas, message limits, connection limits and Cloud Run scaling bounds as well.

The current database adapter serializes writes with an advisory lock. It needs concurrency/load testing and a narrower locking strategy before making claims about supporting hundreds or thousands of companies. Enterprise dispatch must budget route calculations and message segments and prevent duplicate sends.
