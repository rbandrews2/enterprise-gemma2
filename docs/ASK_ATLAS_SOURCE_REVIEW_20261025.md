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
