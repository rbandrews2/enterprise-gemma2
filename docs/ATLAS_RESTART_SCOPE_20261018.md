# Atlas private inference restart review

Next integration after Core upgrade release. No GPU started by this review.

## Current verified infrastructure

- Existing quota preference grants1000 milliGPU (one RTX PRO6000) in us-central1.
- Dedicated identity wzos-atlas-inference@enterprise-gemma2.iam.gserviceaccount.com
  exists; its existing private model-bucket objectViewer binding is present.
- Isolated network wzos-atlas-vpc/subnet wzos-atlas-us-central1,10.83.0.0/26,
  Private Google Access=true.
- Retained gs://enterprise-gemma2-atlas-models-us-central1/gemma-4-31B-it/:
  all10 object names/sizes/CRC32C metadata match Google's public model directory;
  total62,578,670,545 bytes. Generations captured in cloud evidence
  atlas-model-metadata-verified.json. No weights downloaded or copied.
- Actual app uses private_vllm but enabled=0; configured31B service is absent.
  Legacy gemma-inference Gemma2-2B failure is a different service/model.
- App request deadline300s and its existing service identity verified after release.

## Proposed bounded pilot (requires action-time access approval)

Recreate only private wzos-atlas-inference, us-central1. Use existing dedicated
model-read identity, pinned Google image from scripts/deploy_atlas_vllm.sh,
full google/gemma-4-31B-it weights via Run:ai streamer, one non-zonal RTX PRO6000,
20 CPU/80GiB, min0/max1, concurrency2, timeout300s, isolated existing VPC/subnet.
Use a fresh wzos-trial=20261018 ownership label. No public unauthenticated access.
Grant only existing WZOS app identity roles/run.invoker on that one service.
Existing project administrators retain their inherited access; no new operator
impersonation, bucket, secret, project-wide role or credential permission.

Keep production Atlas enabled=0 for this private pilot. Run existing synthetic
operator evaluator only: at most8 serial requests,1024 output tokens/request,
600s total evaluation deadline; stop on first failure. Review actual responses;
transport success alone is not source applicability/safety or app acceptance.
No customer data, messages, model training, checkout or public app configuration changes.

Install an independent one-hour cleanup guard BEFORE deployment. It may delete only
the exact service with the matching20261018 trial ownership label. The foreground
workflow also deletes on success/failure and independently verifies absence. The
guard is a fallback, not a hard billing cap; remain present until deletion verified.
Retain existing model storage and private evidence; remove no customer data.

Target budget$5 for this pilot. At listed us-central1 instance-based rates,
20*.000018 +80*.000002 +.00036522 dollars/second = approximately$3.19/hour;
storage, logs and network are additional. Target less than one hour and tear down
immediately after tests, not simply leave a scale-to-zero service unattended.
Google pricing checked October18: https://cloud.google.com/run/pricing
GPU requirements: https://docs.cloud.google.com/run/docs/configuring/services/gpu

HF_TOKEN is retained in Secret Manager. This approved Google/GCS-streaming path
does not fetch gated Hugging Face files, so it requires no HF_TOKEN binding.
Do not expose or attach that secret merely because the separate legacy service failed.

## After this pilot

Real WZOS metadata-authenticated invocation, controlled browser/source-grounding
acceptance and any ongoing production inference hosting/budget remain separate.
No claim that Atlas is available for customer inference until those checks pass.

## Approved execution checkpoint

Ray approved this exact pilot on October18. Harness5d04c07:
scripts/run_atlas_private_pilot.sh. It installs a separate one-hour guard before
deploy, uses a per-pilot nonce in addition to the date label, and verifies ownership
before deleting only this service. Foreground cleanup runs on success/failure;
successful deletion independently verified before stopping the guard session.
No full app test repeat is required for this operational helper; bash syntax,
print-only command review and the actual bounded synthetic run are the relevant gates.

Cloud Shell lost its terminal connection before launch submission. No pilot/model
was started as of this checkpoint. Reconnect, inspect current service/pointer/logs
before submitting the command. Do not infer successful launch from a timeout.

Subsequent execution: reconnected Cloud Shell, refreshed routine authorization,
verified admin@workzoneos.org/enterprise-gemma2, model absent and no existing pilot
pointer. Home has225MiB free; existing test venv reused, no weights/local model copied.
Launched harness5d04c07 after bash syntax checks. Independent one-hour guard verified
installed before new-service deployment began. Evidence pointer:
$HOME/wzos-atlas-pilot-path.txt. Deployment/evaluation/cleanup outcome still pending;
read pilot.log,deploy.log,evaluation.log,observer.exit and cleanup.verified before
any retry. Production Atlas stays disabled and the Core upgrade release is unchanged.

Pilot completed successfully; see ATLAS_PILOT_RESULTS_20261018.md. Eight requests
passed. Model service absence, stopped guard and unchanged production spec/Atlas=0
independently verified. No active GPU/model service remains from this pilot. Do not
rerun the consumed eight-request pilot automatically. Context corrections are local
and tested, not deployed; actual app metadata-token and source-grounding gates remain.
