# Source revalidation and recovery check

Completed September 29, 2026 Eastern (download timestamps September 30 UTC).

## Results

Reused the catalog-approved bounded ingestion command. All seven sources were attempted; four PDF hashes were unchanged, two HTML revisions were preserved, and OSHA remained unavailable (HTTP 403). The command correctly returned nonzero for incomplete coverage. Machine-readable attempts and hashes: `knowledge/revalidation-20260929.json`.

- VDOT manual, field guide, known-errors PDF and FHWA manual: unchanged bytes.
- VOSH program and regulatory pages: changed HTML hashes; extracted text and section labels match the preceding revisions. Extraction objects differ; this is not evidence of changed legal requirements. New revisions remain **unreviewed**, with older checked revisions retained.
- OSHA fact sheet: official listing identifies a 2005 publication and still links the catalog URL. Web research can read the PDF, but the local downloader receives 403. No bypass or substituted third-party copy. Catalog link-verification date remains September 17 because successful local PDF retrieval was not established.
- Rebuilt index: **2,612 passages including historical revisions**, versus 2,604 before refresh. Eight additional passages are retained VOSH revisions, not eight new requirements.

## Publisher checks

[VDOT publication page](https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/work-area-protection-manual-and-pocket-guide/) identifies January 2026 v11.0, the matching field guide and 2026 known-errors list. It describes exceptions involving pre-January 18 contracts/permits and district decisions. Catalog applicability notes retain those conditions; no blanket effective-date rule or project approval was added. The field guide is an informal companion.

[FHWA publication page](https://mutcd.fhwa.dot.gov/kno_11th_Editionr1.htm) identifies December 2025 Revision 1 as current. State adoption and project applicability still require review.

[OSHA publication listing](https://www.osha.gov/publications/bytopic/highway-work-zones) identifies the fact sheet's publication year; listing availability does not resolve the local download failure.

## Recovery validation

Copied preserved documents, extraction files and manifests into an isolated temporary directory **without SQLite**. Rebuilt 2,612 passages and matched the current revision mapping to the active local index. Existing knowledge tests also exercise historical revision search, failed-download preservation, integrity rejection and duplicate ingestion. This is local recovery evidence, not a cloud backup restoration claim.

## Controlled update procedure

1. Curator checks the official publication page, edition, amendments and exceptions before editing catalog metadata. Record unsuccessful checks; do not advance dates on assumptions.
2. Run `python -m services.v2.knowledge.cli ingest all` with one operator. Downloads must stay within catalog HTTPS/redirect/type/size/time limits. Nonzero means at least one source needs attention.
3. Record attempt status, new/unchanged hashes and previous revisions. A new hash starts unreviewed even when extracted text looks unchanged. Never transfer applicability approval automatically.
4. Reviewer compares original pages/headings, tables, diagrams, footnotes and corrections relevant to the intended use. Use `check-extraction` only with recorded sample evidence. Extraction review does not approve field use.
5. Preserve original revisions and report citations. A latest download is not necessarily the legally governing edition; resolve project authority, contract/permit dates and exceptions separately. Confirm publisher supersession before marking a publication superseded.
6. Rebuild the index and run source tests. Before releasing a new source snapshot, verify restored originals/hashes and citation traceability; package via the existing source snapshot workflow. Git contains catalog/evidence, not ignored source binaries.
7. Recheck before pilot/release, when a publisher announces changes, or when a project's authority/date changes. A recurring refresh is not configured by this document.

## Remaining gates

Review corrections and placement diagrams; resolve OSHA ingestion; curate underlying VOSH standards; add Norfolk road-authority/permit/form evidence and project-specific speed/traffic evidence. Reference-foundation task 3 remains open. No cloud deployment, model call, source applicability approval or production change occurred.
