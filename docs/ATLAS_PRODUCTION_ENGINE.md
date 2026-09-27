# Atlas production engine decision

September 26, 2026. Proposal, not a deployed or accepted production engine.

## Selected direction — September 26

Ray selected **self-hosted Gemma on Google Cloud**, following Google's hosting
recommendations while minimizing charges. This supersedes the managed API
recommendation and its pending $5 evaluation request below. Do not activate MaaS.
The selected model target from the compared options is Gemma 4 31B IT.

Use Google's Cloud Run + prebuilt vLLM path, including its advanced large-model
loading configuration (Direct VPC Egress and Run:ai Model Streamer). Prepare a
separate private inference service, not the failed legacy service. Reuse existing
compatible registry/network/storage settings after inspecting them. Preserve V1.

Cost controls for initial evaluation:

- One non-zonally-redundant RTX PRO 6000, 20 vCPU, 80 GiB in us-central1.
- Minimum instances zero; maximum one at service and revision level. Maximum
  instances limits capacity, not dollar spend, and transient excess is possible.
- No always-on instance, keep-warm scheduler, paid health-check inference,
  reservations or long-term commitments. Cache only authorized results and avoid
  duplicate model calls; app guides remain deterministic where appropriate.
- Keep weights in the same region; avoid a continuously billed VPC connector
  when Direct VPC Egress meets the documented deployment requirements.
- Validate a pinned image/weight revision, startup settings, quota and vLLM
  compatibility before deployment. Measure cold starts and latency; scale-to-zero
  trades idle savings for slower first requests and reduced capacity certainty.
- Published baseline is about $3.19 per provisioned instance-hour including GPU,
  CPU and RAM: roughly $6.37 for two hours or $31.87 for ten hours, excluding
  storage/build/network. Billing includes startup and idle time while an instance
  exists, not just response generation. Weight storage persists at zero instances.
- Record an exact bounded first-run estimate and stop procedure before creating
  paid resources, per the prior price-before-provisioning instruction. A hosting
  choice does not establish an unlimited monthly spend allowance.

Next implementation: adapt the prepared OpenAI-style transport to private vLLM
with Cloud Run ID-token authentication, fixed served model and no provider
fallback. Align request timeouts with measured cold starts without keeping the GPU
warm just for the status display. Then run the full-size WZOS acceptance suite.
No paid resources or model calls were made to record this selection.

## Product direction

Atlas is a central WZOS service across every module. The laptop's Gemma 3 1B
runtime is a development fallback, not the intended customer model. Customer
branding remains **WZOS powered by Atlas AI Assistant**. Use the intended full
cloud model during restricted acceptance and retain that model for launch once
quality, capacity, security and availability gates pass.

## Historical comparison (self-hosted selected above)

### A. Managed Gemma 4 26B A4B IT — recommended first evaluation

- Model: `google/gemma-4-26b-a4b-it-maas`.
- Project: `enterprise-gemma2`; managed location: `global`.
- Endpoint: `https://aiplatform.googleapis.com/v1/projects/enterprise-gemma2/locations/global/endpoints/openapi/chat/completions`.
- This is a 26B mixture-of-experts model, with approximately 4B active parameters;
  it is not the small laptop model. Text/image inputs and text output are supported.
- No dedicated GPU deployment. Use runtime service-account OAuth, never a
  browser credential or downloaded service-account key.
- Live project model card explicitly labels the API **public preview**. Model
  card visibility does not establish invocation access, quota, acceptance of
  terms, production SLA or residency suitability. Those remain checks before use.
- Official listed inference prices: $0.15 per million input tokens and $0.60
  per million output tokens. A 4,000-input / 1,000-output interaction calculates
  to $0.0012; 10,000 such interactions calculate to $12. This excludes all other
  WZOS services and does not predict actual context, image or reasoning usage.

### B. Dedicated Gemma 4 31B IT — private hosting alternative

- Model: `google/gemma-4-31B-it`; vLLM protocol.
- Separate private inference service in `us-central1`; one RTX PRO 6000 GPU,
  at least 20 vCPU and 80 GiB memory. Evaluate with maximum one instance,
  minimum zero, explicitly bounded concurrency and no request-body logging.
- Pin a tested container digest and weights revision before deployment; use
  Google's documented model-streaming path and read-only weights access.
- Iowa non-zonal instance pricing gives approximately $3.19 per active hour
  including CPU, memory and GPU; about $2,326 for 730 continuously active hours.
  Storage, build, network, startup/idle-tail time and other WZOS services add cost.
  Scale-to-zero saves idle expense but introduces cold starts. A budget alert is
  not a hard cap. The GPU tutorial carries a pre-GA notice; verify support terms.
- No GPU quota, cold-start, concurrency, latency or reliability acceptance yet.

The managed option is substantially cheaper at the example usage and is a
full-size candidate. Its preview status prevents declaring it production-ready.
Do not choose solely by parameter count; compare WZOS task quality and latency.

## Proposed bounded first live evaluation (requires priced acceptance)

Use option A against synthetic WZOS scenarios only, with a $5 maximum test
allocation. Start with at most 40 serial requests, <=16,000 input characters,
<=1,024 output tokens, thinking disabled, no automatic retries or tool execution.
Record provider token usage and elapsed time, stop on authentication/quota errors,
and reconcile actual billed usage. Verify these request options against the API
before execution. Do not treat an alert as spending enforcement; keep the request
count and per-call limits in the operator runner. No always-on GPU is authorized.

## Implementation sequence

1. Complete the current restricted application deployment acceptance checkpoint.
2. Add a disabled-by-default managed API adapter. Existing Cloud Run adapter speaks
   Ollama and cannot be pointed directly at MaaS or vLLM. Use a fixed approved
   endpoint/model, bounded context/response/timeouts, no redirects or implicit
   provider fallback, redacted errors and explicit usage accounting.
3. Verify project access, applicable terms, scoped runtime permissions and quota;
   run the bounded full-model evaluation after cost acceptance. No public ingress.
4. Connect app-authorized saved records and source passages, including revision,
   page and applicability status. Preserve admin/member, Core/Enterprise and
   tenant boundaries before retrieval or inference. Do not ship the whole database
   or unrelated employee records into a prompt.
5. Expand Atlas from advice to typed tool proposals. Backend rechecks permissions,
   record versions and arguments; consequential actions require user confirmation.
   Dispatch remains Enterprise/admin. Never infer success from generated prose.
6. Add imagery understanding to the reviewed map/geometry pipeline. Gemma text
   output does not itself generate truthful site photographs or surveyed positions.
   Render icons with existing map geometry and retain image/source provenance.
7. Run quality, capacity, cost and recovery acceptance; select hosting and enable
   only the accepted capabilities. Production/DNS cutover remains separate.

## Required acceptance evidence

### Local preparation completed

`services/workspace_preview/managed_intelligence.py` now provides the managed
text transport, selected only by `WZOS_ATLAS_PROVIDER=managed_gemma` and enabled
only by `WZOS_ATLAS_MANAGED_ENABLED=1`. It fixes the project/model/endpoint above,
uses Cloud Run metadata OAuth credentials, bounds input to 16,000 characters and
output to 1,024 tokens/64 KiB response, uses a 50-second total deadline, and rejects
truncated/tool-call/missing-usage responses. No automatic retries or fallback.
Readiness is cached successful inference within five minutes, not a paid health
probe; a fresh process reports not ready until its first successful request.
Four transport tests passed, including disabled state, identity boundaries,
redirect/oversize rejection and usage accounting. This is local preparation,
not live protocol, model-quality, quota or production acceptance. No deployment
of this adapter has occurred. Request limits are per process, not a global spend
cap; a bounded operator evaluation runner and production tenant quotas remain.
Full local regression after the adapter: 172 tests total, 156 passed and 16
PostgreSQL-dependent tests skipped locally. Managed access acceptance was run
separately against the deployed application; this new adapter was not deployed.

### Launch gates

- Every module: grounded, useful help and correct capability limits; no fabricated
  completed actions, certification, payroll or message delivery.
- Job/report: identifies relevant missing information beyond any single example
  form; cites verified sources and distinguishes candidate applicability.
- Geometry: no invented sign spacing or flagger positions without the necessary
  governing references and site measurements; stale inputs are visible.
- Security: cross-tenant, Core report denial, member admin actions, prompt injection
  in notes/documents, cancelled requests, malformed responses and provider failure.
- Operations: measured p50/p95 latency, token cost, bounded concurrency, timeout
  alignment, throttling, retry policy, outage behavior and rollback.
- Multimodal/tool calling and automatic execution are not claimed implemented by
  the first text transport test. Each receives separate scenario evidence.

## Sources verified during planning

- [Managed Google models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/google)
- [Managed API usage](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/maas/call-open-model-apis)
- [Model pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing)
- [Cloud Run GPU configuration](https://docs.cloud.google.com/run/docs/configuring/services/gpu)
- [Cloud Run pricing](https://cloud.google.com/run/pricing)
- [Official 31B deployment tutorial](https://codelabs.developers.google.com/codelabs/cloud-run/cloud-run-gpu-rtx-pro-6000-gemma4-vllm)

No new paid inference resources, model requests or production changes were made
while preparing this proposal. Model quality remains unverified on WZOS tasks.
