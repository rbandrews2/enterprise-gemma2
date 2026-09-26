# Restricted V2 update - September 26, 2026

## Deployed release

- Application commit: `579a3bdba2aab014bd22fde0c90812b7615f103e`.
- Cloud Build: `47f8fc82-3166-4916-983b-6b427e67e2ec`, SUCCESS.
- Service: `wzos-v2-accounts`, project `enterprise-gemma2`, region `us-central1`.
- Ready revision: `wzos-v2-accounts-00006-gjq`, 100% traffic.
- Previous revision: `wzos-v2-accounts-00005-2ns`.
- Image-only update preserved environment/secret references, service identity, resource limits and template annotations; private IAM policy verified.
- No schema migration, database replacement, public DNS change, V1 deployment or new inference resources.

## Validation

Anonymous root/session requests return 403. Cloud-IAM authenticated root and current assistant.js return 200; application session without an application identity returns 401. Browser shows the verified-account sign-in page through the existing Cloud Shell preview origin.

Managed account acceptance passed: real sign-in, refresh, verified-email enforcement, admin/member permissions, cross-organization boundaries and last-admin protection. The read-only deployed Atlas runner passed eight module guides, canonical roles and tenant/email denials. These were verified application guides with no model calls; model-quality acceptance remains open. New revision error-log query returned no entries at severity ERROR or above during the inspected 30-minute window.

## Inference inventory

The surviving `gemma-inference` service has no ready revision. Revision `gemma-inference-00006-xfp` failed startup on PORT 8080. Its configured image is `us-central1-docker.pkg.dev/enterprise-gemma2/gemma-repo/gemma-inference:v3-python3` with 4 CPU, 16 GiB and one GPU. It was inspected only, not restarted or changed. New private adapter code is included but remains disabled. Verified application guidance does not require a model.

## Operator tooling

Fresh isolated checkout and test environment: `/tmp/wzos-update-pjWc85hN`. Downloads were slow; the already-installed `/usr/bin/cloud-sql-proxy` resolved the dependency and the redundant download was stopped. Reuse the installed proxy first on future Cloud Shell sessions. Global CLI configuration was unchanged.

Cleanup confirmed: synthetic provider users disabled, refresh tokens revoked, test organizations disabled, sensitive fixture token fields stripped and password environment variable unset. Temporary SQL proxy stopped after acceptance. Web preview proxy remains available while Cloud Shell stays awake. Operator state remains outside Git. Public V1 and the older synthetic-only V2 preview are unchanged; the persistent account service is the current V2 deployment.

## Next: full-size Atlas engine

Read ATLAS_PRODUCTION_ENGINE.md. A managed Gemma adapter was subsequently prepared locally, disabled by default and not included in this deployed image. It is transport-tested only; no full-size inference call has been made. The user is comparing free model weights with paid cloud hosting; no hosting choice or new inference spending is approved yet.
