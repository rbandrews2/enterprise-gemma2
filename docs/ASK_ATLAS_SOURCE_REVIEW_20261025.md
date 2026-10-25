# Ask Atlas source review - October 25, 2026

## First batch completed

- Rechecked VDOT publication pages for Virginia MUTCD11.0 and VWAPM11.0.
  Preserve the January18,2026 applicability exceptions; no project approval inferred.
- Verified local VWAPM original SHA256
  `f16aa1782e85c4b1237823eb8fbaafdf06128f3cc8d2c17c16fb696b92415274`.
- Visually compared physical pages34,35,36 (printed24,25,26) against PDFium text.
- Recorded AI-assisted extraction-fidelity reviews for34 and36. Standard/Guidance/
  Option/Support labels, deleted paragraphs, exceptions and fractions preserved.
  Terminal replacement glyphs were a display encoding issue: underlying Unicode
  quarter fractions are intact. No OCR correction was needed.
- Page35/Figure6D-1 remains unapproved for text-only use: extracted labels lose
  gesture/column/dimension relationships. Captions alone cannot explain the diagram.
- The flagger-context check remains `image_review_required`; two reviewed pages
  do not approve the full section or its figure/table/cross-reference dependencies.

## Missing companion added, not approved for answering

The existing three-page `vdot-known-errors` is the VWAPM list. It is NOT an older
version of the separate five-page Virginia MUTCD known-errors list. The initial
suspicion of a superseded file was disproved by comparing titles/content.

Added `vdot-mutcd-known-errors-20260615` separately in knowledge/sources.json and
pinned it as a required companion for the supplied MUTCD. Original SHA256:
`5d5ceed217ee150b473bab714815ed17dd8c7049afa389a0faec6d8cfaf29b5f`.
Imported official bytes locally; no current-source approval granted to the supplied
MUTCD (its publication_status remains unknown). Existing VWAPM companion preserved.

Visual inspection of new companion pages3-5 identified strike-through semantics
not preserved in extracted text (notably Sections2F.10 and3A.03), a missing paragraph
notice in3B.07, and ambiguous clearance typography in Figure2C-V2. Do not infer a
corrected number or silently turn known-error advice into an adopted requirement.
The publisher explicitly says these are informational, not official changes yet.
All five companion pages remain unapproved for model answering.

## Evidence and next batch

Ignored artifacts: `.local-data/dot-manuals/review-20261025/` includes provenance,
current PDF, page images, stored/current text, context result and index rebuild.
Revision-bound reviews are in the VWAPM revision's page-reviews.json. Preserve
these sidecars with originals; Git does not back up the local knowledge library.

Next: finish VWAPM flagger pages37-38 and the referenced Table6G-1; review all
three VWAPM correction pages; resolve diagram/strike-through representation before
marking affected pages usable. Compare supplied MUTCD with official original,
review separate federal corrections, and continue taper/buffer and marking batches.
No broad all-pages review flag, paid inference, customer data, cloud changes or
activation. Conversational quality acceptance still follows source readiness.

## Official references

- https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/virginia-mutcd/
- https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/work-area-protection-manual-and-pocket-guide/
- https://www.vdot.virginia.gov/media/vdotvirginiagov/doing-business/technical-guidance-and-support/technical-guidance-documents/traffic-operations/2026-06-15-Virginia-MUTCD-Version-11.0-List-of-Known-Errors_acc06152026_RM.pdf

## Second batch - flagger, corrections and taper dependencies

Twelve additional pages visually inspected: VWAPM23-26,37-38,51-53 and
VWAPM known-errors1-3. Full extraction comparison completed for23-26,37-38
and corrections1-3;51-53 received layout/dependency triage, not blanket acceptance.

Five new extraction-fidelity reviews saved: VWAPM23,37,38 and corrections1,2.
Together with the first batch this makes seven accepted page transcriptions,
NOT seven approved operational procedures. Guidance versus Standard, exceptions,
continuations and provisional correction wording are preserved.

Findings requiring repair/review:

- Corrections page3 Table6N-1 had no extracted table content. Added an AI-assisted
  manual transcription (110 cells, row labels, mph/feet units) to its OCR-compatible
  sidecar. Source visibly has a non-monotonic four-lane-divided left-turn cell:
  645 at40mph followed by615 at45mph. Do not guess a replacement. Initially saved
  fidelity review3 was withdrawn before index rebuild to keep the page blocked;
  original review and reason preserved in review-withdrawals.json. Transcription
  remains unreviewed for answer eligibility pending source clarification or a
  representation that reliably carries this uncertainty into model context.
- Corrections page1 itself prints an ambiguous foot-mark in a plaque dimension;
  extraction preserves it. This is source uncertainty, not a license to normalize
  it to inches. Page2 explicitly says I believe and Need to verify in places.
- VWAPM25 contains invisible extracted content: an unlabeled speed/distance list
  and part of Table6B-V5 that are absent from the rendered page. One extracted
  formula has075 rather than0.75. Do not approve or merely append OCR to this text;
  a verified replacement transcription must exclude invisible PDF objects.
- VWAPM26 tables have merged cells for wider lanes and conditions in footnotes.
  Flattening loses column span meaning. It also includes repeated preceding-page
  text. Requires structured transcription and retained notes before acceptance.
- VWAPM52-53 Table6G-1 includes blank/merged cells, minimum-size restrictions,
  footnotes and known-error additions. Needs explicit column mapping; page52 alone
  is not a complete source for sign dimensions. These pages remain unreviewed.
- VWAPM24 and prior35 are diagrams; captions alone do not preserve layout.

Artifacts remain ignored in review-20261025 and revision-bound sidecars. No
source originals modified. Rebuild and two focused context checks confirm flagger
and taper questions still cannot enter reviewed-answer mode with these dependencies.
No paid inference, production deployment, provider/IAM change or unrelated retests.

Next: implement a provenance-bound reviewed replacement-text/structured-table
mechanism (not additive OCR for hidden-text pages), with invalidation checks;
then repair25-26,52-53 and diagram descriptions before model acceptance. Preserve
unresolved source anomalies rather than silently fixing official documents.

## Batch3 - replacement text and taper tables

Added provenance-bound full-page replacement transcriptions. Each entry binds the
original PDF hash, physical page, raw extraction hash, replacement text hash and
metadata. A separate visual review binds that exact representation; any change
invalidates review. Replacement happens before heading/caption extraction, so
invisible PDF objects cannot leak back through metadata. Existing OCR remains
supported. Packaging includes replacements and review-withdrawal history.

Visually compared VWAPM physical pages25-26 (printed15-16) against their rendered
originals. Accepted replacement transcription fidelity for all visible table rows,
merged-column scope, formulas, notes and surrounding prose. Hidden objects and
repeated prior-page text excluded. Nine page transcriptions now accepted overall;
this is not engineering approval or approval of a complete operational procedure.
Original PDFs remain unchanged. Ignored artifacts: review-20261025/batch3-* and
revision-bound page-transcriptions.json/page-reviews.json.

Focused validation: 16 reasoning tests and16 manual tests passed, including four
new replacement/invalidation/packaging cases. Earlier new-test Windows temporary
file cleanup failures were repaired by explicitly closing SQLite connections.
No paid model calls, production changes, unrelated suites or customer DB changes.

Disposable index format is now7; rebuild before use. Rollback to older code must
not rebuild these sources without replacement support: keep Ask Atlas disabled or
restore its matching earlier source snapshot/index. Never discard the originals
or review history. Remaining: diagram semantics (24/35), sign tables52-53 and
unresolved correction-table anomaly, then bounded model acceptance.

## Batch4 - sign table and taper diagram

Visually inspected physical pages24,35,52,53 against original page renderings.
Accepted three more replacement representations: VWAPM24 (printed14) and52-53
(printed42-43). Total accepted page representations:12. This is transcription
fidelity, not engineering approval or a complete operational source review.

- Table6G-1: mapped all55 rows (43+12) to sign designation, section and three
  road-category size columns. Preserved the blank variable-speed minimum cell,
  printed dashes, asterisks, original spelling, all six notes and Table2B-1
  reference. Explicitly linked page52 to the continuation/notes on53.
- Page53 surrounding speed-safety-camera and crosswalk prose retained in full;
  did not normalize or reinterpret the source's legal references.
- Figure6B-V3 on24: added spatial description, opposing travel directions,
  legend, two flaggers and ordered dimension labels. Distinguished the required
  approach buffer before the curve from the optional downstream buffer. Kept
  illustration-only scope and Chapter6P reference; inferred no unlabeled lengths.
- Figure6D-1 on35 remains unreviewed: do not use isolated labels as sufficient
  evidence of hand motion. Needs a complete gesture description checked against
  accompanying prose, including the emergency/spotter-only flag column and
  dimension-arrow endpoints.
- Correction-table page3 anomaly remains unresolved; no guessed replacement.

Artifacts: ignored review-20261025/vwapm-{24,52,53}-replacement.txt,
batch4-sign-rows.json and revision-bound replacement/review sidecars. Originals
unchanged. No application/runtime code or customer database changes this batch;
prior32 focused code checks remain applicable and were not repeated. No paid
inference, IAM changes or deployment. Local source originals/sidecars are not
Git-backed; use the source-library packaging workflow before any release.

## Batch5 - hand-signal diagram and publisher recheck

Accepted physical35 (printed25), Figure6D-1, after comparing all six panels with
Sections6D.02/03/05 on34/36/37. Replacement preserves paddle vs emergency/spotter
flag columns, stop/proceed/slow rows, lowered flag for proceed, optional paddle
hand motion, flag sweep and dimension-arrow endpoints.13 page representations
accepted overall; no engineering or full procedure approval.

Publisher check: the currently linked wapm-list-known-errors_acc.pdf remains
SHA256 bec29b070d4cbe642761fd8a666331df6d48d220346a56d3c9ad2fc0e2a7f80b,
three pages, identical to the pinned original. A search-engine result for the old
list-known-errors_acc.pdf shows a stale two-page copy, while direct HTTP returns
404. Do not use search cache as evidence of the currently published revision.
The four-lane-divided left-turn value at40mph remains645 followed by615 at45mph;
no replacement guessed, correction page3 remains ineligible.

Official FAQ linked from the same publication page identifies itself and the
known-errors document as informal/non-policy. FAQ is not ingested or approved in
this batch. Candidate for later scoped review, not automatic governing authority:
https://www.vdot.virginia.gov/media/vdotvirginiagov/doing-business/technical-guidance-and-support/traffic-operations/work-zones/wapm-faq_acc.pdf

Prepared clarification question (not sent): In VWAPM11 known-errors Table6N-1,
is the four-lane-divided left-turn40mph value645 correct given45mph615? Please
identify an authoritative correction or confirm applicability. Keep this source
blocked until clarified or an explicit uncertainty-aware response path is tested.

Remaining context dependencies, beyond the previously highlighted diagrams:
- Sign questions: VWAPM51/54,47-50,11,141-143 and correction3.
- Taper questions:27-28,20-22,11,134-135,157-159 and correction3.
- Flagger questions:39-41,11,143-144,51/54 and correction3 (query-dependent).
These are actual unreviewed context pages from batch4 packets, not a claim that
reviewing one remaining table finishes all source coverage. Next prioritize the
flagger continuation39-41 and cross-reference applicability. Preserve unresolved
source uncertainty. No customer communications, paid model calls or live changes.

## Batch6 design - source uncertainty holds

Add revision-bound page-issues.json: physical page to list of unresolved issue
notes. Validate page keys and nonempty bounded notes. Include it in index basis
and source packaging. Expose notes in evidence; any issue makes answer_eligible
false even if transcription fidelity was reviewed. Context explicitly explains
source disagreement. No issue auto-resolution or mutation of original reviews.
Derivative index schema8 requires rebuild; no customer DB migration. Rollback
must keep Ask Atlas off or restore the matching prior snapshot; older readers
cannot safely ignore new holds. Tests cover review-vs-eligibility, staleness,
packaging and malformed issue rejection. No public activation in this task.

## Batch6 completed work and user correction-precedence decision

Visually inspected all24 queued dependency pages. Accepted18 additional VWAPM
pages:11,20,21,22,27,28,39,40,41,47,50,51,54,134,135,141,143,144.
Page21 had invisible neighboring tables: removed those, retained visible6B-V2.
Pages11/28/41/143 had extracted control characters in hyphenated words: repaired
against image. Figure6B-2 on22 received spatial label mapping. Other pages retained
all source paragraphs, modal distinctions and cross-references.

User explicitly confirmed known-errors data overrides corresponding original
claims. Implemented correction precedence in prompt and evidence packet; cite
correction, keep original for traceability, do not treat a resolved replacement
as an unresolved conflict. Provisional notes remain provisional. Rechecked all110
cells of known-errors3 and accepted exact published values, without smoothing or
interpolation. Removed earlier non-monotonicity hold with recorded user decision
in page-issues-history.json; prior withdrawal history preserved.32 total reviewed
page representations now, including3 reviewed pages held for other source conflicts.

Distinct unresolved conflicts not resolved by that replacement table:
- VWAPM25 vs157: shoulder taper1/3 L versus L; shifted minimum note differs.
- VWAPM26 vs158:45mph/4ft shift180 versus200 in purported duplicate tables.
- VWAPM48 vs50/51: drawing plaque code and rounding annotation disagree with prose.
-142 explicitly marked Known Error (FHWA); sign code differs from preceding prose.
-159: <40mph versus <=40mph in another source; downstream NTRS dimension ambiguous.
Unreviewed diagram descriptions48/49/142 remain;157/158/159 deduplicated/staged but
not approved. New revision-bound issues hold affected pages even when extraction
is reviewed. This is separate from correction precedence and never promotes a
known explicit replacement back to an unresolved base-manual disagreement.

34 focused DOT tests passed after the precedence change. Synthetic mocked transport
checks prompt policy; no paid model output test has run. New uncertainty checks
cover reviewed-but-held pages, stale indexes, malformed holds and snapshot retention.
Local artifacts batch6-* preserve comparisons, holds, rebuild and context results.
Source originals/sidecars remain ignored and require snapshot packaging for release.
No PostgreSQL schema change, customer sends, live deployment or paid inference.

### Batch6 final local readiness check

Rebuilt the schema8 index after recording the completed sampled extraction
reviews through the existing source-review API. The old source-level
extraction_checked flags were still false; individual page review and issue
holds remain independently enforced. This does not approve the whole manual.

Final local evidence-packet checks passed: hand signaling flaggers is
ready_for_reviewed_answer with no unreviewed or held dependencies. Taper lengths
and variable-speed-limit queries remain needs_clarification with the documented
source holds/unreviewed diagrams. This is retrieval readiness, not live model
acceptance. Evidence: batch6-final-rebuild.json, batch6-final-flagger.json,
batch6-final-taper.json, batch6-final-signs.json and batch6-final-remaining.json
under the ignored local review-20261025 artifact directory. No paid calls.

## VDOT contradiction wording - October 25, 2026

Added user-requested concise update notice to Atlas guidance instructions. Use
only for documented unresolved VDOT contradictions after applicable known-errors
corrections. Identify the affected item; direct users to check VDOT's website.
Do not assert latest-release currency or active revisions without evidence.
Difficult questions, missing inputs/sources, extraction review gaps and model
errors require their actual explanation, not this notice. Existing source holds
remain intact; this change does not route held evidence into inference.
Focused mocked prompt/token-budget test passed (1 test, no paid inference).
No schema changes or deployment. Initial test command had an incorrect Python
path; rerunning with the verified absolute interpreter passed.

## Batch7 - sign illustrations and late-merge diagram - October 25, 2026

Visually compared pinned VWAPM physical pages 48, 49 and 142 and created
full-page replacement representations. Figure 6G-1 now associates each sign
code with its visible legend/symbol and plaque assembly. Page 49 retains all
Standard/Guidance/Option prose. Figure 6N-1 records the upstream sign order,
five A intervals, optional downstream sign and printed Known Error notice.
Illustrated numbers are examples, not selected job requirements. No inferred
scale or silent sign-code corrections. Original PDFs remain unchanged.

35 page representations reviewed overall. Pages 48 and 142 retain their
existing source-conflict holds; page 49 has no recorded source hold. The next
remaining staged tables are 157-159. Source artifacts and review bindings are
under the ignored knowledge directory; batch7-* evidence is in the local
review-20261025 directory. No production change or paid inference.

## Source review batch7 validation - October 25, 2026

Real local index rebuild completed. All three new representations bind to
reviewed originals. Assertions passed: physical page49 answer_eligible=true;
pages48/142 page_reviewed=true and answer_eligible=false with original issue
notes retained. Evidence: review-20261025/batch7-validation.json and
batch7-rebuild.json. No application code changed; previous passing tests reused.
No paid model test, production activation or full-manual approval claimed.

## Batch8 - remaining staged tables - October 25, 2026

Completed visual comparison of VWAPM physical pages157-159 against pinned images:
advance warning spacing, buffers, taper criteria, merging/shifting tables with
merged cells/formulas/notes, channelizer spacing, barrier flare and rumble strips.
Corrected staged extraction's erroneous shoulder-taper cross-reference from
6B-V6 to the visibly printed6P-V6. Made page159 column relationships explicit;
retained <40 mph and literal downstream 4'-6' rather than inventing a value.
Prior unreviewed transcriptions preserved in batch8-prior-staged-transcriptions.json.

38 page representations reviewed overall. These three pages remain held for
previously documented unresolved source discrepancies. Accurate transcription
is distinct from applicability or field approval. No executable formula added.
All24 dependency pages queued in batch6 now have reviewed representations;
source-conflict holds remain. This is not a review of the entire manual/library.
Next: resolve or explicitly report affected conflicts, assess remaining context
dependencies for intended question coverage, then bounded model acceptance.
No application changes, paid inference, or production deployment.

## Source review batch8 validation - October 25, 2026

Local index rebuilt successfully. Assertions passed for all three pages157-159:
page_reviewed=true, answer_eligible=false, nonempty original source-issue holds.
Evidence: review-20261025/batch8-validation.json, batch8-rebuild.json and
batch8-reviews.json. Original PDFs unchanged; no runtime code changes, so passing
application suites were not repeated. Source snapshot packaging remains required
before release; ignored source artifacts are not backed up by the Git commit.

## Ask Atlas answer-path readiness - October 25, 2026

Fixed a gap in VDOT notice delivery: held source packets never reach Gemma, so
prompt instructions alone could not display the requested notice. The server now
returns concise discrepancy wording and affected source links only for recorded
VDOT page issues. The UI displays this without fabricating a model answer; missing
sources, difficult questions and unreviewed pages alone do not trigger the claim.
No assertion of latest-publication currency. Existing holds and permissions retained.
Also removed misleading 'this copy alone' warning when no evidence fits the context
budget. Budget remains unchanged; no clipping or added inference calls.

Eight real local retrieval probes: hand signaling flaggers, flagger qualifications,
and STOP SLOW paddle ready for model validation. Taper query reports recorded issues.
Variable Speed Limit exceeds context capacity; pedestrian accessibility, rumble strips
and channelizer questions need additional reviewed dependencies and/or narrower scope.
See ignored review-20261025/answer-readiness.json for exact remaining pages.

Validation: 3 Python source-uncertainty tests, 1 context-budget regression, and
6 Node Ask Atlas tests passed. New Node test initially selected the matching heading
instead of button; fixed selector and reran affected file successfully. DOM simulation,
not browser screenshot or live model acceptance. No paid calls, deployment or schema
changes. Prior passing unrelated suites not repeated.
Next: package source artifacts, validate conversational model answers on ready topics,
and continue the explicitly listed dependencies for broader coverage. Live acceptance
and deployment remain outstanding.

## Model context repair - October 25, 2026

The isolated real adapter check stopped before generation: actual /tokenize input
27808 tokens against max_model_len32767, plus unchanged4096 output and4096 safety
reserve exceeded capacity. No generated answer was produced by that attempt.
Removed repeated retrieval/audit metadata from model input, grouped source metadata
once, and retained complete text of all17 pages, captions, headings, applicability,
page notes, citation IDs, corrections, formulas and conversation context. Full original
packet remains server-side for citation validation and audit. No source text clipping,
window increase, IAM change or production deployment.
Packet decreased from93353 to78113 UTF-8 bytes.20 focused reasoning tests passed;
additional inconsistent-source-metadata assertion passed in the affected test.
Cloud isolated adapter normalized SHA256 matches local:
5f4c90809a8b11fa8b9aa919fbc67438071f399ec4d495b5faca08c2a90ea8f9.
Original failure preserved as acceptance-result.json in
/home/admin_/atlas-acceptance-6329a06; repaired bounded attempt writes
acceptance-compact-result.json. No automatic paid retries.

### Bounded cloud result and next checkpoint

Repaired attempt finished in96.17s with generic draft-validation failure. Server logs
confirm POST /tokenize HTTP200 at06:34:16Z and /v1/chat/completions HTTP200 at06:35:51Z.
Thus the context guard passed, but answer acceptance did NOT pass. The old adapter
suppressed the precise failure and no raw response was retained; do not claim a
specific quote, schema or output-limit cause. No second generation was launched.
Added safe stage/error-type diagnostics (no question, answer, token or exception text)
and explicit output-limit handling. Focused output-limit/privacy test passed.
Next: use instrumented adapter for one bounded diagnostic acceptance, then fix the
observed cause before release. Preserve all source holds. Source package and prior
20 passing reasoning tests need not be repeated for unchanged code.

## Diagnostic acceptance result - October 25, 2026

User authorized one diagnostic run. Isolated adapter matched normalized SHA256
6b4d099fc7cedd21392db4526520b8a855143f5b8cfc7672119b492cf81cccb2 (commit16b85f5).
One generation attempt completed in66.93s. Actual input22828 tokens, capacity32767;
completion2009 tokens, total24837, finish_reason=stop, content_present=true.
Adapter rejected response at validate_draft with JSONDecodeError. Context overflow
is repaired; output truncation is not the observed cause. Citation/schema validation
has not run successfully because JSON decoding failed first. Exact formatting cause
is unknown because raw output was intentionally not retained. Do not claim markdown
fences, parser tags or a specific provider bug without inspecting evidence.

Cloud artifacts: /home/admin_/atlas-acceptance-6329a06/acceptance-diagnostic.log
and acceptance-diagnostic-result.json. No automatic retry, IAM change, deployment,
new workload or customer data. Prior local tests were not repeated.
Next: repair the structured-response/parser boundary using targeted format evidence;
keep strict schema, citations and source holds. Do not rerun the same blind check.

## Structured response repair - October 25, 2026 (in progress)

Captured one synthetic-only response in the isolated Cloud Shell test folder for
replay, not production logging. It began with a bare thought label and had no channel
delimiters: the pinned serving decoder stripped them before reasoning parsing.
Reference: https://github.com/vllm-project/vllm/issues/38855 and the official
Gemma recipe https://docs.vllm.ai/projects/recipes/en/stable/Google/Gemma4.html.

Set skip_special_tokens=False on the DOT request, retaining enable_thinking=True.
Added explicit final JSON and literal quote instructions. Live repaired response now
has separate reasoning and parseable JSON (111.05s,22942 input/3014 output tokens).
Three of four quotes matched exactly. Remaining quote crossed pages36/37 while
citing37 only; rejected correctly. Added explicit page-boundary instruction and
continued bounded acceptance. No weakened quote/schema validation or inference retry.
37 focused Python checks and6 Node checks passed before the last prompt-only change.
Source holds and live deployment remain unchanged.

## Ask Atlas structured-answer acceptance passed - October 25, 2026

Completed the formatting/citation repair and proceeded through the next checks.
Final adapter normalized SHA256:
83d94a6dee64d67ad575901f9f2ef348ae4d3d3a455c7d013627c400bd45c5e7.
Preserve special tokens for the pinned vLLM reasoning parser; reasoning remains on.
Require a JSON final answer and continuous page-specific verbatim supporting quotes.
Do not strip arbitrary prefixes, accept partial JSON, fuzzy-match quotes or auto-retry.

Actual private Gemma31B acceptance through GuidelinesGemma, all using the complete
reviewed17-page context with pinned corrections and strict server validation:
- Hand signals/STOP-SLOW: validated draft,80.86s,22983 input/2545 output tokens.
- Virginia flagger qualifications: validated draft,87.74s,22980 input/2819 output.
- Contextual follow-up asking to skip training for10 minutes: validated draft,33.52s,
  23134 input/892 output. Rejected the invented exception, retained conversation,
  and distinguished traffic delay guidance from the worker's assignment duration.
All answers passed JSON/schema/exact-quote/citation checks; final prose was reviewed.
No field approval implied.34-88s latency remains a UX/performance limitation, not an
instant-response claim. No customer data, IAM changes, new infrastructure or deployment.

37 focused Python tests and6 Node Ask Atlas tests passed. The final prompt-specific
regression passed after adding the cross-page quote instruction. Existing access,
cancellation, conflict-notice, context-budget and formula safeguards retained.
Do not repeat these checks unless affected code/source/model configuration changes.

Cloud evidence folder: /home/admin_/atlas-acceptance-6329a06.
Accepted artifacts: acceptance-pages-result.json, acceptance-qualification-result.json,
acceptance-followup-result.json and corresponding logs. Synthetic-only raw diagnostic
responses are separate in that isolated folder; never enable production raw logging.
Source package remains .local-data/atlas-release-sources-20261025 (ignored),52 files;
38 page representations reviewed,8 VWAPM holds retained. Broader source review remains
open. The live app is unchanged. This completes the bounded answer-path repair and
acceptance; deployment/in-app acceptance and broader manual coverage are separate.
Rollback: revert DOT request/prompt changes; no database or source schema changes.
