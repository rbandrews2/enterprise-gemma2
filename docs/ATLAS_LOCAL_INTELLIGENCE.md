# Local Atlas intelligence

## Product identity

Customer-facing wording: **WZOS powered by Atlas AI Assistant**. Backend model names belong in operator configuration and technical documentation. Atlas helps across all functions and both editions; advanced planning remains an Enterprise entitlement. No production deployment occurred.

## Working implementation

- Reused the V2 coordinate parser and measured-approach controls in `services/workspace_preview/static/geometry.js`, with the existing JobGeometry validation. Work orders now save closure/scenario, road class, work limits, duration, lane/sight-distance measurements and up to eight reported approaches. No approved placements are inferred.
- `POST /api/assistant/chat` calls a real local model; `GET /api/assistant/status` reports availability. Actor and organization checks run before model access; saved-job version conflicts return 409. Both editions receive app guidance. Relevant Enterprise safety/reference questions can include up to three local source candidates, with unverified applicability.
- Chat history is browser-memory-only, at most eight turns / 8,000 characters. Job/identity changes clear context and discard late answers. Unsaved job/checklist changes block chat until saved or reloaded. Replies are plain text; there are no model tools, record mutations or outbound message actions.
- Fixed loopback transport `127.0.0.1:11435`, explicit enable flag, no environment proxies, no redirect following, one concurrent generation, 120-second overall timeout, bounded input/output and explicit failures. The app remains a synthetic-data local preview, not production authentication.

## Runtime and reproducibility

Portable Ollama 0.34.2 from the official GitHub release:
https://github.com/ollama/ollama/releases/tag/v0.34.2

Downloaded `ollama-windows-amd64.zip` SHA256:
`8f3fd071a2a2f9497b562f43502c77c2b701a99d1ee5dfda28da8c786373063b`

Extracted in ignored `.local-data/atlas-runtime/ollama-0.34.2` after verifying the published release digest. Models are in `.local-data/atlas-runtime/models`. Ollama created its own local runtime key under the user's `.ollama` directory; no credentials are committed. Cloud mode is disabled. No Windows service, startup task, firewall change or system PATH installation was created.

Model: `gemma3:4b`, Q4_K_M, 4.3B parameters, downloaded size 3,338,801,804 bytes. Verified runtime manifest digest:
`a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a`.
This is a development model choice, not production quality/latency acceptance. The tag is not immutable; operators must compare the digest after future pulls.

Official runtime/API guidance: https://docs.ollama.com/windows and https://docs.ollama.com/api/chat . Model page and linked usage terms: https://ollama.com/library/gemma3:4b . Review distribution/license obligations before production packaging.

Start in two terminals:

```powershell
.venv/Scripts/python.exe scripts/start_atlas_runtime.py
.venv/Scripts/python.exe scripts/start_workspace_preview.py --atlas
```

Stop each with Ctrl+C. Model memory unloads after five idle minutes. If runtime files were lost, download and verify the pinned portable ZIP before extracting to the documented directory; do not overwrite a running runtime. To restore the model after starting the runtime:

```powershell
$env:OLLAMA_HOST='127.0.0.1:11435'
& ./.local-data/atlas-runtime/ollama-0.34.2/ollama.exe pull gemma3:4b
```

The browser connects only to the preview API, never directly to the model port. Model binaries, weights and local records are not backed up by GitHub.

## Verification and limits

99 automated tests passed, including disabled/busy/failed/empty/oversized/timed-out model responses, cross-organization access, stale job versions and measured-approach validation. A real API response correctly explained new-work-order creation and returned `model_called=true`, no actions and no approval. Cold response took about 64 seconds on the current Intel CPU; this is too slow for production acceptance. Model responses can still be wrong: prompt instructions do not guarantee factual accuracy or regulatory compliance.

Next: streaming/cancellation and performance benchmarks; broader adversarial and functional evaluations; production identity, audited context selection, model/provider deployment and cost controls. Maps and approved sign/flagger layout generation remain separate unfinished capabilities.

Real browser verification: asked "Can you clock me in now? Answer in two sentences." Atlas correctly declined the timekeeping action, with no record mutation. Synthetic measured approach survived save/reload at work-order revision 5.


## Integration follow-up

- Replies include server-owned navigation suggestions, filtered by edition and saved-job availability. The model cannot supply executable navigation commands.
- Stop reply cancels fetch and closes the server model request. A receive watcher detects disconnects through the local middleware; context changes also abort pending conversations.
- 101 tests pass, including edition navigation and cancellation releasing the model lock. Browser testing caught and corrected a polling-only disconnect implementation.
- Real HTTP evaluation: measured-approach instructions returned in 78.8 seconds; adversarial false-dispatch request was refused in 92.8 seconds. Both returned no actions and no field approval. Results are retained locally in `.local-data/atlas-runtime/integration-evaluation.json`.
- This small evaluation is not a comprehensive quality or safety certification. CPU speed, streaming, checklist-aware context and production hosting remain unfinished.

The post-cancellation browser request was accepted but reached the bounded timeout; the UI displayed the explicit retry message and re-enabled controls. Successful geometry navigation metadata was verified through real HTTP; button click-through remains to be checked with a completed browser reply.


## Saved checklist context

The scoped chat endpoint reads the latest saved checklist after work-order authorization. It supplies five category statuses, notes capped at 300 characters each with explicit truncation flags, checklist revision, linked job revision and staleness. No saved checklist is an explicit state; Atlas is instructed not to equate absent records with unfinished work or user-reported readiness with approval. The browser shows the checklist basis outside generated prose. Requests without a selected job include no checklist context.

102 full-suite tests passed after this integration. A focused regression also covers HTTP 499 for a disconnected reply, avoiding a misleading middleware server error. No model actions or automatic approvals were introduced.

Live checklist evaluation: the real local request timed out after 110.2 seconds with HTTP 503 and the explicit retry message. Checklist context is verified by tests, but real generated checklist-answer quality remains unverified. Six focused intelligence tests passed after the HTTP 499 regression. Prioritize CPU inference performance before further model-heavy browser testing.
