# Atlas application-path acceptance - October 18, 2026

## Result

Approved private Gemma 4 31B application-path run PASS. Exactly two model requests
through the production application factory and VLLM adapter, using real Google
metadata authentication from the existing WZOS app identity. No operator token or
downloaded service-account credential. The disposable job used injected in-process
user claims and temporary SQLite/files; this does not validate browser sign-in or
customer database/storage persistence.

| Check | Result |
| --- | --- |
| Stale saved job | HTTP 409 before inference |
| Another organization's saved job | Non-disclosing HTTP 404 before inference |
| Core user requests Enterprise report | HTTP 403 before inference |
| Saved synthetic job and source review | Model response in 4.832 seconds |
| Member notification guidance | Model response in 2.679 seconds |

The harness checked current job version, a retrieved passage reaching the adapter,
candidate revision and unreviewed provenance, unverified applicability, matching
canonical token audience, exactly two identity/inference requests, no performed
actions and no field approval. The source was deliberately synthetic: this does
not establish real VDOT/FHWA/OSHA coverage, freshness or field applicability.

Agent review: the first answer explicitly identified the synthetic reference as
unreviewed and unsuitable for field use; requested speed/traffic/site imagery,
geometry and qualified review; invented no placement coordinates. The second
correctly explained queued/sent/delivered/acknowledged distinctions, member versus
admin SMS permissions, consent and phone verification. Raw answers retain
needs_human_review; no qualified field reviewer or customer acceptance is implied.

## Provenance and safety

- Exact approved derivative image eaa44f814c0917c2719ba0c09a1b34849145f2cc27ba9130a16153a094d4571d;
  build74a46069-95f9-41e9-9965-c97ded5610d1; launcher6f500b7.
- Same retained Gemma4 31B weights, pinned Google image, model-read identity/network,
  one RTX PRO6000/20CPU/80GiB, min0/max1 and private app-only invocation.
- Dedicated one-task app-identity job, 1CPU/512MiB, 300s, no retries, no secret or
  external database/bucket bindings. No public listener or customer sends.
- One-hour guard installed2026-10-18T14:40:10Z before provisioning. Both foreground
  and independent guard cleanup covered only nonce-owned model/job resources.
- Pilot exit0; independent observer exit0. Model service and app job independently
  listed absent, guard process absent, production application spec unchanged and
  production Atlas enabled=0. Both workloads removed after this single run.
- Production remains upgrade-live-bf9f524. Guidance repairs are in the tested
  derivative only; not yet deployed to the customer app. No automatic replay.
- Observed model revision wzos-atlas-inference-00001-ctc; job execution
  wzos-atlas-app-workflow-skljr. Guard to independent cleanup verification422.21s.
  Compute-window estimate$0.374 at the previously recorded resource rates, not an
  actual billing result; excludes build/job/logging/storage/network charges.
  This window includes deployment, job provisioning and teardown, not a cold
  end-user request. See https://cloud.google.com/run/pricing.

## Evidence and next gate

Cloud pointer $HOME/wzos-atlas-app-live-path.txt contains artifacts.json,
image-before.json, model-ready.json, model-iam.json, job-config.json, execution.json,
workflow-logs.json, workflow-result.json, pilot.exit, foreground-cleanup.log,
independent-model-after.json, independent-jobs-after.json, app-before/after.json,
observer.exit and summary.json. Preserve evidence; do not remove retained weights.
Resolved evidence directory: /tmp/wzos-atlas-app-live.TclQ0viK. Private compressed
backup: $HOME/wzos-atlas-app-20261018-TclQ0viK.tgz with adjacent SHA256 sidecar.

Next: validate actual reviewed authoritative references and source-status behavior,
then prepare separately bounded customer-app/browser inference and hosting scope.
This test closes metadata invocation and synthetic saved-job retrieval plumbing;
it does not authorize ongoing hosting or public Atlas activation.
