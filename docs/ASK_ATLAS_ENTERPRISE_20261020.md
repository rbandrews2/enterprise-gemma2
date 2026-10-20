# Ask Atlas - Work Zone Guardian

## Current product decision

Smart Field Voice and Ask Atlas are the highlighted Enterprise features. Voice
records observations for reviewed office submission; Ask Atlas reasons over DOT
manual context to answer questions. Guidance is not automatically attached to a
report. Existing Voice report fields and office submission stay unchanged.
Maps/Navigation is separate. Weather configuration remains under the user's hold.

Work Zone Report is removed from launch cards/navigation. Previous saved revisions
remain available through Voice's Previous reports button, read-only with existing
ownership/organization checks and PDF downloads. Historical data and APIs are not
deleted or rewritten. Core retains ordinary Atlas app help and cannot use DOT APIs.

## Implemented locally

- Dedicated responsive Ask Atlas page: typed questions, reference date, source
  search, cited answers, clarification questions and explicit Read aloud/Stop.
  Search excerpts collapse by default. Existing black glass/amber design retained.
- Voice questions reuse the existing 30-second/6-MiB recorder/WAV encoder and
  Google US `long` Speech adapter. They do not require a report job. Transcription
  is reviewed/edited before Ask Atlas, not automatically submitted for inference.
- Existing onboarding explains both report and question processing. Retained
  browser permission is reused; browser revocation/temporary grants remain
  authoritative. Navigation/cancel/sign-out stop microphone tracks and playback.
- Read aloud selects an English `localService` voice only. No new TTS provider or
  automatic remote voice fallback. No voice playback until the user requests it.
- Questions/transcripts stay in page memory, clear on view/session changes, and
  never enter customer persistence, service-worker caches or application logs.
- Context preserves complete sections, continuation pages, one explicit hop to
  cited sections/tables/figures, and pinned mandatory correction documents. It
  never silently clips a table/section to fit. Missing/oversized evidence blocks
  inference and requests a narrower question or source review.
- The assembly limit is 96,000 UTF-8 bytes, not a token-window claim. The private
  model's `/tokenize` endpoint measures the actual chat template before generation.
  Capacity is capped at the smaller of its reported limit and 32,768 tokens, with
  4,096 output tokens plus 4,096 tokens reserved for schema/template overhead.
  Existing serving script specifies 32,767, not the advertised model maximum.
- Gemma reasoning is enabled for this transport only. Structured answers distinguish
  requirements/interpretation and retain conditions, exceptions and exact source
  quotations. Tools/function calls, truncation and unknown citations are rejected.
  Provisional errata require clarification rather than silent overrides.
- Exact quote validation does not prove semantic entailment, applicability or
  engineering correctness. Source review and real model acceptance remain required.
- Calculations use explicit, revision-bound, operator-reviewed formula rules only.
  Inputs must match question quotations and declared units. A bounded Decimal/AST
  arithmetic interpreter recomputes results; no eval, functions or model-generated
  code executes. Arithmetic verification is distinct from applicability. No real
  engineering formulas have been approved/registered yet.

## Sources and review

Seven PDFs are preserved/indexed locally: 2,627 physical pages. Four previously
supplied MUTCD/standards/TEDM copies retain their user-import/unreviewed identity.
The three new supplied PDFs were downloaded through Drive and compared against
fresh, allowlisted official VDOT downloads on October 20. All three hashes match:

| Source | Pages | SHA256 |
| --- | ---: | --- |
| VWAPM v11.0 January 2026 | 414 | f16aa1782e85c4b1237823eb8fbaafdf06128f3cc8d2c17c16fb696b92415274 |
| Work Zone Field Guide January 2026 | 93 | 3c311ed030cbba7e91f684092c32b26cc7eb55d625f47eb1c1f3eaf94378c8b4 |
| VWAPM known errors | 3 | bec29b070d4cbe642761fd8a666331df6d48d220346a56d3c9ad2fc0e2a7f80b |

The official publication page confirms VWAPM v11.0 as current with earlier
contract/permit and district exceptions. Field Guide is an informal companion,
not policy. Known-errors issue date remains unverified: its undated correction
snapshot cannot establish historical availability before this verification date.
Confirmed vs provisional corrections must remain distinguishable in answers.

Original PDFs, extraction manifests, annotations and indexes remain ignored local
artifacts, not Git content. Page reviews are bound to original SHA and exact text
SHA. Global sampled extraction checks do not approve every page. OCR changes
invalidate a previous page review. Source byte equality is not visual review.
Initial rollout prioritizes traffic control, then pavement marking. No all-topics
or field-ready coverage claim follows from indexing all pages.

Operator-only workflow (rebuild after sidecar changes):

```text
python -m services.v2.knowledge.manual_review ocr SOURCE SHA PAGE [PAGE ...]
python -m services.v2.knowledge.manual_review review SOURCE SHA PAGE --note "Specific visual comparison and limitations"
python -m services.v2.knowledge.manual_cli review-formula REVIEW_SPECIFICATION.json
python -m services.v2.knowledge.manual_cli rebuild
```

OCR uses the distribution `tesseract-ocr` package in Cloud Shell, at most 25 pages
per explicit batch. It renders immutable originals to temporary PNGs, writes
unreviewed hash-bound OCR sidecars and never runs in the web API. No paid OCR API.
Visual review must include tables, symbols, units, notes and diagram limitations.
No actual cloud OCR has run yet. Cloud attachment recovered after authorization;
Tesseract was absent at the fresh tool check. PostgreSQL is installed.

Formula specification fields: formula_id, citation_id, supporting_quote,
expression, inputs (variable -> exact unit), input_bounds (variable -> lower/upper
numeric strings in that unit), result_unit, reviewer, review_note.
The cited original page must already pass source/page review. Existing formula
IDs cannot be silently overwritten. Registration records an explicit operator
decision; it does not automatically derive or verify a formula's interpretation.

## API, privacy and compatibility

- `GET /api/atlas/dot/config`: Enterprise capability flags/recording limits.
- `POST /api/atlas/dot/search`: bounded excerpts and source metadata.
- `POST /api/atlas/dot/ask`: ManualQuery plus required UUID request_id; cited draft,
  unresolved details, verified calculation traces, used citations and token usage.
- `POST /api/atlas/dot/transcribe?request_id=UUID`: bounded WAV, ephemeral transcript.
- `POST /api/atlas/dot/requests/UUID/cancel`: scoped cancellation.
- Existing source outline remains available. Customer `/context` returns 404;
  whole-page source packets remain internal/operator-only, including blocked answers.

All data routes authenticate and enforce Enterprise. The existing `atlas_requests`
table supplies cross-replica request uniqueness/cancellation and DOT admission:
one active per user, two active overall, six starts/user/minute. Keys use a `dot:`
namespace; state expires after ten minutes. Records contain only IDs/state/expiry,
not questions, audio or answers. No new customer DDL or report migration. Ordinary
chat limits/transport, Voice job authorization and existing provider access remain
unchanged. Full PostgreSQL validation is still mandatory before shared deployment.

`WZOS_ATLAS_DOT_ENABLED` and `WZOS_ATLAS_DOT_INFERENCE_ENABLED` remain independently
gated. `WZOS_ATLAS_DOT_ORGANIZATIONS` must list exact enabled organization IDs;
an empty list denies processing/search, so activation cannot accidentally enable
every Enterprise organization. Private origin uses the existing operator-configured DOT/Voice URL and Google
metadata ID-token authentication. No IAM, secrets or cloud resources were changed.
One explicit transcription and one generation per attempt; no automatic paid retry.
The tokenizer request is preprocessing, not an additional generation.

## Preview and remaining activation

Local simulator: `python scripts/run_mobile_preview.py --port 8083 --manuals`.
It can search the real local library, but middleware blocks DOT inference and
transcription regardless of external flags. It cannot establish live microphone,
provider or installed-device acceptance. Production is unchanged by this work.

Remaining sequence:
1. Fresh Cloud Shell verified admin@workzoneos.org / enterprise-gemma2 and latest
   ready app revision ui-6047e5b. Preserve the live baseline while checking this candidate.
2. Complete bounded CPU OCR and page/table/errata/formula review for the first
   traffic-control questions. Do not enable answers from unreviewed pages.
3. Package/verify originals and derived sidecars together; no originals in Git.
4. Run the PostgreSQL gate on the frozen candidate and review mobile/desktop plus
   installed-device recording/cancellation/local speech behavior.
5. One synthetic pilot only: at most one Speech and three Gemma generations within
   the approved $5 ceiling, existing model only, no new GPU/workload/IAM. Stop on
   failure; no automatic repeat. Existing shared hosting is not a hard-spend-capped
   resource and must not be shut down or altered at Voice's expense.
6. Stage then enable only after acceptance, initially for Molecular's organization;
   preserve roles/entitlements. No customer messages/SMS or report changes.

Rollback independently disables DOT inference/search or restores the previous app
revision. Voice and submitted reports remain intact. Use the existing PWA update
prompt; never force-refresh an unsaved report. No public cutover is claimed here.

Primary references:
- https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/work-area-protection-manual-and-pocket-guide/
- https://docs.vllm.ai/en/latest/serving/openai_compatible_server/
- https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice/localService

## Local validation checkpoint

Broader affected regression suite:58Python PASS, no failures/skips. Full Node
suite:158PASS, no failures/skips. Subsequent affected checks:11backend and17Node
PASS, including source gates, tokenizer overflow, arithmetic, duplicate/tenant
controls, late cancellation and a microphone grant arriving after backgrounding.
All provider traffic was mocked. Syntax and diff checks PASS. These are not the
frozen-candidate PostgreSQL or real provider acceptance gates. Evidence logs are
ignored under.local-data/dot-manuals. No real source page/formula is approved yet.
