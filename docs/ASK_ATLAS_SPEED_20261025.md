# Ask Atlas response speed and citation reliability

## Changes

- Place sorted, complete public reference context before the question, conversation
  history and request date. This permits reuse of an identical model prefix when
  the same reference packet is used. It does not cache private answers or prove
  that the serving engine actually reused cached tokens.
- Keep trailing continuation pages intact, but stop following references from the
  next unrelated section on that extra page. The hand-signal packet now contains
  15 pages instead of 17; all three pinned known-errors pages remain present.
- Represent every source page as consecutive, lossless spans of at most 1,000
  characters. Atlas selects a supplied passage ID; the server attaches its exact
  source text and original citation. No fuzzy quote repair or inferred page number.
  The complete page text remains in context, including exceptions and continuations.
- Keep the public GuidanceDraft contract and its exact-quote/source validation.
  The private model transport uses PassageDraft with a request-specific enum of
  eligible passage IDs. Unknown, unreviewed and too-short passages are rejected.
  Source selection still does not establish applicability or field approval.
- Show immediate waiting feedback and elapsed seconds every 15 seconds. Stop
  waiting preserves the question and clears the timer. This does not claim a
  particular backend stage or an estimated completion time.

## Evidence and limitations

Baseline accepted hand-signal response: 80.86 seconds, 22,983 input tokens and
2,545 output tokens. Baseline qualification and follow-up checks are already
recorded in ASK_ATLAS_SOURCE_REVIEW_20261025.md; do not repeat unrelated suites.

Two intermediate attempts were correctly rejected and are not speed successes:

1. Smaller/sorted context: 62.24 seconds, 21,354 input/1,947 output. Quotes matched
   source pages, but model substituted printed page labels for PDF citation IDs.
2. Citation-ID enum: 71.36 seconds, 21,370 input/2,077 output. IDs were valid;
   one quote joined a sentence across source pages. Replaced copying with passage
   selection rather than repeatedly retrying the same nondeterministic output.

Final adapter normalized SHA256:
`5a55527707d985eab9372fb0f11a1666cca5d54e5ae2e7792b0a6a0c0b1cb6f7`.
Cloud test copy was hash-verified before execution. Context canonical SHA256:
`b3609fb719276ca4fabfbbeabbf0f748ac63681b5b2b983cd2e180f8ddb4c83a`.
Cloud evidence: `/home/admin_/atlas-acceptance-6329a06/`.

The repaired hand-signal check passed schema, exact-source and citation validation:
58.91 seconds, 22,510 input/1,395 output tokens (`acceptance-passages-result.json`).
That is about 27% lower elapsed time and 45% fewer generated tokens than the accepted
baseline for the same question. Input is only 2% lower after adding passage labels.
These are single observations, not a latency guarantee or controlled cache benchmark.
The server returned no cached-token metric, so cache reuse is unproven. Source
selection does not automatically establish that every clause is supported; human
applicability review and broader semantic acceptance remain necessary.

One contextual follow-up passed in29.15s, 22,738input/665output tokens
(`acceptance-speed-followup-result.json`). It answered the hand-only control question
directly, retained the one-lane/two-way scope, and separately explained the police/
emergency-responder exception. This was a different follow-up question from the
earlier33.52s baseline and is not a matched speed comparison. No further model runs.
Temporary local preview server8097 stopped and its agent-created tab closed.

Focused Python coverage: 41 cases across test_dot_reasoning and test_dot_manuals.
The passage transport required updating the mocked provider response and accounting
for existing schema whitespace stripping; both affected checks passed on targeted
rerun after the other 39 passed. Seven Node Ask Atlas checks passed. Browser checked
immediate/elapsed feedback and Stop waiting preserving the question, using synthetic
data and no model call. Screenshot: ignored `.local-data/atlas-status-preview.png`.

## Release boundary and rollback

No database migration, IAM change, new workload, always-on model setting, customer
send or production deployment. Reasoning, reviewed-source holds, strict validation,
one-request/no-automatic-retry behavior and existing access controls remain intact.
No new provider/model or hosting-cost change. Eight existing VWAPM source holds
remain unresolved; this speed work does not approve more source pages.

Before deployment, run required integrated release gates on the frozen candidate.
Rollback reverts the adapter, retrieval and waiting UI changes together; no data
migration or persisted format conversion is necessary. Public response shape remains
compatible. Private model test harnesses must use the new passage-selection schema.
