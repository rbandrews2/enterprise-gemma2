# Persistent V2 staging proposal

Prepared September 26, 2026. Ray approved this priced scope on September 26.
Provisioning has begun; see STAGING_PROVISIONING_20260926.md for acceptance evidence and remaining gates. This proposal replaces temporary
SQLite staging for account acceptance; it is not the production capacity plan.

## Proposed resources

| Resource | Proposed configuration |
|---|---|
| Project / region | enterprise-gemma2 / us-central1 |
| Database | wzos-v2-staging-db; PostgreSQL 16, Enterprise edition, db-g1-small, zonal, 10 GiB SSD |
| Database safeguards | Daily automated backups, seven retained backups; deletion protection; storage growth limited to 20 GiB; verify restore before acceptance |
| Database connectivity | Cloud SQL authenticated connector/socket; no authorized public client networks; dedicated application DB user; credential in Secret Manager |
| App | wzos-v2-accounts; 1 vCPU, 512 MiB, request-based billing, minimum 0 / maximum 2 instances, concurrency 8, timeout 60 seconds |
| Access | Initially IAM-restricted testers via authenticated proxy; verified Firebase email/password accounts and database-owned admin/member memberships inside the app |
| Files | New dedicated regional Standard bucket, proposed enterprise-gemma2-wzos-v2-files-staging (subject to availability), uniform access, public-access prevention, versioning and seven-day soft delete |
| File retention | Retain current objects; remove noncurrent versions after 30 days; account for soft-deleted/versioned bytes in cost. Synthetic uploads only until scanning acceptance |
| Identity | Enable/configure email/password Firebase Authentication; authorized test origins only; no SMS authentication |
| Runtime identity | Dedicated service account, Cloud SQL Client, bucket-scoped required object access, access only to application DB secret; no project editor |
| Monitoring | Billing alerts at $25/$40/$50 for the selected resource scope where supported; service errors and database capacity alerts |

IAM/proxy staging access is intentionally a tester workflow. Customer browser access
and final hostname require a separate reviewed ingress/authentication decision.
No GPU, inference endpoint, Maps expansion, SMS/MMS or paid email is included.

## Cost estimate and limits

USD, 730-hour month. SQL db-g1-small compute rate rechecked September 26 at
$0.035/hour: $25.55/month. Shared-core has no Cloud SQL SLA and is for this limited
test environment only. [Cloud SQL pricing](https://cloud.google.com/sql/pricing).

September 24 stored-data assumptions remain planning figures: 10 GiB SSD $1.70,
10 GiB used backups $0.80, 10 GiB regional objects $0.20. Approximate foundation
subtotal **$28.25/month**, before requests, retained versions and ancillary services.
Reconfirm storage/backup SKUs in the provisioning estimate; this is not a fixed quote.

At 100,000 requests and 50,000 billed instance-seconds/month, the proposed Cloud Run
CPU and memory would cost about $1.20 + $0.0625, plus $0.04 requests, **$1.3025**
before free allowances. Actual billed instance time, not summed request latency,
determines this calculation. [Cloud Run pricing](https://cloud.google.com/run/pricing).

Use **$50/month as an initial planning budget**, not a guaranteed cap. Build/image
storage, logs, secrets, networking and authentication usage can add charges. Free
allowances may already be consumed. Max instances and alerts are not hard spending
limits. Existing V1 services, Atlas inference, Maps and messaging are excluded.
Do not represent this as the total cost of WZOS.

## Read-only inspection September 26

- Reconnected the existing authorized Cloud Shell as admin@workzoneos.org.
- Project enterprise-gemma2 / 910004733138 verified in console.
- Enabled-API query returned Cloud Run and Storage; SQL Admin and Identity Toolkit
  were not present. No APIs enabled during inspection. No SQL inventory attempted
  that would prompt API enablement; historical DB absence is not established.
- Existing buckets: enterprise-gemma2_cloudbuild and gemma_think_v2, both US.
- Existing gemma_think_v2 bucket reports uniform access true and public-access prevention inherited; versioning value was not returned. No claim of private-object acceptance.
- Staging latest-ready revision remains wzos-v2-staging-00007-8fs; legacy API is gemma-assistant-api-00008-njc.
- Cloud Run list in us-central1 includes gemma-assistant-api, gemma-inference and
  wzos-v2-staging. The inference entry has no latest-ready revision in the result;
  do not assume it is usable or cost-free. Existing resources remain unchanged.

## Provisioning acceptance sequence

1. Ray accepts the priced scope and variable-cost basis.
2. Verify final SKUs, IAM capabilities and resource-name availability; stop if a
   material cost/configuration change is needed.
3. Enable required APIs and create isolated resources; configure secrets without
   printing values. Restrict tester access; do not modify V1 DNS or permissions.
4. Run all PostgreSQL tests, verified sign-in/member/admin isolation, private-file
   upload/download, instance-replacement persistence and backup restoration.
5. Record resource IDs, revision, exact configuration and observed billing. Only
   then attach provider integrations and move toward the September 30 test milestone.
