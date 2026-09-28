# Authorized self-hosted Atlas trial

Scope: $15 initial deployment/testing plus approximately $1.17/month retained
weights, approved by Ray. No production/DNS/V1 changes or customer delivery.

## Resources prepared

- Project/region: enterprise-gemma2 / us-central1.
- Quota: one RTX PRO 6000 granted (1000 milliGPU), preference
  wzos-atlas-rtx-us-central1.
- Isolated custom network wzos-atlas-vpc and subnet wzos-atlas-us-central1,
  10.83.0.0/26, Private Google Access enabled.
- Dedicated inference identity wzos-atlas-inference@enterprise-gemma2.iam.gserviceaccount.com.
- Private regional Standard model bucket enterprise-gemma2-atlas-models-us-central1;
  inference identity receives only storage.objectViewer on this bucket.
- Google's container pinned by digest in scripts/deploy_atlas_vllm.sh.
- Google source model: 10 objects, 62,578,670,545 bytes. Direct GCS copy completed;
  count/size/CRC32C all matched before GPU deployment. Source and copied generations
  recorded by /tmp/wzos-verify-weights.py in Cloud Shell.
- Application image build: 9fb24c22-f85b-4433-9a8a-b5dc561e4c82, source e99bb68,
  image tag wzos-v2-accounts:e99bb68. Build SUCCESS, not yet deployed.

## Current boundary

The first CLI invocation rejected repeated fp8 argument values before GPU
creation. Corrected to unique --key=value tokens in commit 9634578; deployment
retried with unchanged resource limits. Live inference has not started yet. The
application remains on its prior accepted revision. Syntax and print-only
deployment checks passed locally and in Cloud Shell. Do not mistake prepared
resources for accepted model quality or a production-ready integration.

Cloud Shell /tmp/wzos-start-approved-trial.sh waits for the copy process, runs
the checksum verifier, and only then starts deployment. A 90-minute best-effort
Cloud Shell cleanup guard is started before deployment and targets only the
`wzos-atlas-inference` service carrying trial label `20260926`. This is a fallback,
not a durable billing cap; operator supervision and final cleanup remain required.

## Startup repair

Revision wzos-atlas-inference-00001-7d7 imported the pinned image successfully,
then failed on `storage.buckets.get`. Added custom role
`projects/enterprise-gemma2/roles/wzosAtlasBucketMetadata` containing only that
permission. The September 26 binding failed, so no restart occurred then.
On September 28 the same bucket-scoped binding succeeded and was read back.
Revision wzos-atlas-inference-00002-dvx then started successfully. No broad
storage-admin role was granted. See ATLAS_LIVE_ACCEPTANCE_20260928.md.
