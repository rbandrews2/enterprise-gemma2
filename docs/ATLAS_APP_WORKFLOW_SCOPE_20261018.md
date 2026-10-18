# Atlas application-path test preparation - October 18, 2026

## Purpose and limits

The completed operator pilot proved eight full-size model responses. It did not
prove the application's metadata identity or saved-job retrieval path. The next
test uses the real app factory, account authorization, storage, retrieval and
VLLM adapter inside a disposable job. No HTTP listener or external test login.

`scripts/check_atlas_app_workflow.py` uses temporary SQLite/files, injected test
account claims, and a deliberately synthetic reference through normal ingestion.
The reference has unreviewed provenance and a conspicuous synthetic label. This
proves plumbing, not real agency coverage, source freshness or field accuracy.

Local mocked orchestration passed: stale job 409, cross-organization job 404
(non-disclosure), Core report 403, then exactly two app inference requests. Model
response checks retain current job version, candidate revision/review status,
unverified applicability, no performed actions and no field approval. Denials
must occur before inference. Early fixture failures were repaired without
weakening application behavior: valid HTML envelope, expected 404 denial and
complete mock provider finish/usage fields.

Live mode requires CLOUD_RUN_JOB=wzos-atlas-app-workflow and refuses serving-app,
external database/bucket and emulator environments. A scoped environment marker
lets the existing production metadata helper execute in a job; no token provider
replacement in live mode. Tokens are neither printed nor stored. User auth is
injected in-process; this does not test Firebase browser sign-in.

## Prepared image

Dockerfile.atlas-app-workflow derives from the exact current public image
f347f6901acb223b412ae729aa52afc47a1210804b861916ecfc18f46f5e3873,
copies only the repaired intelligence guide and test harness, and runs mocked
orchestration at build time. It is a test image, never a customer deployment.

## Completed release gates

Exact application source c18951e passed the full disposable PostgreSQL suite:
811 tests in 348.308 seconds, zero failures/errors/skips. Node: 136 passed,
zero failures/cancellations/skips. The source c6bfa69 adds only this harness,
its derivative build files and this scope document; application sources are
identical to c18951e. Local mocked harness also passed its five checks.

Cloud evidence pointer: $HOME/wzos-atlas-context-gate-path.txt, under /tmp.
Its native database cleanup completed; no wzos-pg-gate PostgreSQL process remained.
The launcher's exit-file printf wrote literal `0n` for exit zero; preserve those
original artifacts and use the independently passing full-suite log summaries.
No suite was rerun merely to correct that presentation issue.

Test-only image build submitted as
74a46069-95f9-41e9-9965-c97ded5610d1 in us-central1 from c6bfa69.
Build pointer: $HOME/wzos-atlas-app-build-path.txt. Final status SUCCESS, including
Linux mocked orchestration in Docker RUN. Immutable test image:
`us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-atlas-app-workflow@sha256:eaa44f814c0917c2719ba0c09a1b34849145f2cc27ba9130a16153a094d4571d`.
Production application spec independently compared unchanged with the completed
pilot checkpoint; model service absent and production Atlas still disabled.

## Proposed live scope - not authorized by the consumed operator pilot

- Recreate one private full-size Gemma 4 31B service with the same pinned Google
  image, retained GCS weights, dedicated model identity/network, one RTX PRO 6000,
  20 CPU/80 GiB, min 0/max 1. Existing model-read permission only.
- Grant only the existing WZOS app identity service-scoped invocation.
- One new job wzos-atlas-app-workflow using that app identity: 1 task, 1 CPU,
  512 MiB, five-minute task timeout, zero retries. Bind only the canonical model
  origin; no secrets, production database/bucket, web endpoint or customer sends.
  The app identity retains its existing permissions while attached to the job.
- Two serial synthetic model requests, each at most 1024 output tokens; no retries
  or keep-warm probes. Fixture authorization checks consume no inference.
- $5 maximum test budget; independent one-hour model cleanup guard plus foreground
  teardown on success/failure. Remove the job and model and independently verify
  absence. Preserve logs/evidence and retained model files. Never delete customer
  data, alter the public application, or enable production Atlas.

At the previously verified resource rates, the model costs about $3.19/hour;
the completed operator pilot's whole guard window estimated $0.31. Actual new
duration is unknown. Build, job, logging, storage and network costs are separate;
the guard limits runtime, not a guaranteed billing cap. Stop rather than retry on
failure. Recheck current configuration and artifact digest before provisioning.
Pricing basis: https://cloud.google.com/run/pricing

Ray approved this exact bounded test in chat after build completion. Approval is
for one run with image eaa44f81… and two requests; no replay on failure.
`run_atlas_private_pilot.sh run-app` reuses the proven model guard and now also
removes only the nonce-labelled app job. Both foreground and one-hour guard
cleanup verify ownership before deletion. `run_atlas_app_workflow_job.sh` verifies
the exact image, identity, canonical audience, resources, timeout, no secrets or
volumes and zero retries before execution. It records only the specific job
execution's logs. No production application revision or configuration is changed.

Completed successfully with the approved image: two requests and all three
pre-inference denials passed. Model/job deleted; guard stopped; app unchanged.
See ATLAS_APP_WORKFLOW_RESULTS_20261018.md. Approval consumed; no automatic replay.
