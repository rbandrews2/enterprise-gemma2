# Private Atlas vLLM integration

Ray approved the $15 initial trial and approximately $1.17/month weights on
September 26. Do not repeat that approval request. See ATLAS_LIVE_TRIAL_20260926.md
for current resource/deployment evidence; earlier proposed wording below is the
cost basis of the accepted scope.

## Implemented locally

- `WZOS_ATLAS_PROVIDER=private_vllm`, `WZOS_ATLAS_VLLM_ENABLED=1` and
  `WZOS_ATLAS_VLLM_URL` select a canonical private Cloud Run origin.
- Fixed model `google/gemma-4-31B-it`; `/v1/chat/completions`; service ID token
  for the exact origin. No browser credentials, redirects, retries or fallback.
- Reuses bounded chat transport: 16,000 input characters, 1,024 output tokens,
  64 KiB response; rejects incomplete/tool-call responses and missing usage.
- 290-second inference deadline accommodates cold startup. Set application Cloud
  Run request timeout to at least 300 seconds before activation (currently 60).
- Readiness never wakes the GPU: it reflects successful inference within five
  minutes. A fresh process reports unavailable until first successful conversation.
- Advice only. Existing application scope checks precede inference. This does not
  implement autonomous actions, image inputs or model training.

## Repeatable operator evaluation

From the repository root:

```sh
python scripts/evaluate_atlas_vllm.py
python scripts/evaluate_atlas_vllm.py --live --url https://ACTUAL-SERVICE.run.app --output /tmp/atlas-evaluation-001.jsonl
```

First command is a no-network dry run. Second needs an authorized gcloud identity
and the actual private service URL; the placeholder is not deployable. Eight
synthetic module scenarios maximum, serial requests, ten-minute session deadline,
stop at first failure, no retries. Output must be a new file; keep it outside Git.
Responses require human quality review. The runner tests model transport and
supplied module context, not the entire authenticated browser workflow. Re-run
managed app permission tests when connecting the application to this service.
The runner deadline cancels client work; it does not guarantee immediate server
generation cancellation, service shutdown, or a dollar spending cap.

## Read-only cloud preflight, September 26 evening

- Account app remains `wzos-v2-accounts-00006-gjq`; legacy inference has no ready
  revision. No resources or permissions changed during this preflight.
- Regional default subnet exists but Private Google Access is false. Prepare an
  isolated appropriate subnet or a reviewed change before Direct VPC model loading.
- Google public weights listing: 10 objects, 62,578,670,545 bytes (58.28 GiB),
  under `gs://vertex-model-garden-public-us/gemma4/gemma-4-31B-it/`.
- Existing private file bucket is regional; other surviving buckets are US
  multi-region. Prefer a separate regional model bucket with inference identity
  object-viewer access so customer files and model permissions stay independent.
- Cloud Quotas command failed because the quota API is disabled in its consumer
  project. No API was enabled. GPU quota remains unverified, not assumed zero.

## Concrete initial deployment scope and estimate

Proposed: one private `wzos-atlas-inference` service, us-central1, one non-zonal
RTX PRO 6000, 20 vCPU / 80 GiB, min zero/max one, vLLM concurrency initially 2,
model context 32,767, Google's documented FP8 loading/cache configuration. Pin
container digest and weight generations before activation. Use Direct VPC Egress,
Private Google Access, read-only model bucket access and app-only invocation.
No keep-warm traffic, request-content logging, customer delivery or public access.

Compute baseline is $3.186792 per instance-hour; two hours approximately $6.37.
58.28 GiB regional Standard weights cost approximately $1.17 per 730-hour month.
Copy/build/operations/network and startup/idle-tail time add costs; these are
estimates, not exact invoices. Proposed initial test allocation: $15 total,
with no more than two provisioned compute hours targeted and no unattended
service left processing traffic. Obtain acceptance of that allocation and ongoing
weight storage before provisioning under Ray's price-before-provisioning rule.

Before deployment: verify GPU quota, network ranges, image digest and container
flags. Plan an explicit end-of-session service teardown or verified zero-instance
state; max-one and budget alerts alone do not enforce a hard dollar ceiling.
Do not provision training hardware in this inference test. Training needs a
separate reviewed dataset, compatibility check and priced run.

Sources: [Google deployment tutorial](https://codelabs.developers.google.com/codelabs/cloud-run/cloud-run-gpu-rtx-pro-6000-gemma4-vllm),
[Cloud Run prices](https://cloud.google.com/run/pricing),
[regional storage prices](https://cloud.google.com/storage/pricing).

## Validation and next checkpoint

Twelve focused transport/runner tests passed. Full suite: 175 tests total,
159 passed and 16 PostgreSQL-dependent skips. Dry run produced the scenario plan
without credentials or inference. No live 31B quality or latency evidence yet.
Next: approved bounded deployment, real eight-scenario run, review outputs, then
authenticated WZOS integration. Preserve V1 and public DNS.
