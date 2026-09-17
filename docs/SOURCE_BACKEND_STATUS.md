# Source backend validation and coverage

Verified locally on 2026-09-17. No cloud deployment, model call, email, or Cloud Shell change.

## Ingestion snapshot

| Source ID | Download/extraction | Passages | Review | SHA-256 revision |
| --- | --- | ---: | --- | --- |
| `vdot-vwapm-2026` | extracted | 649 | extraction_checked | f16aa1782e85c4b1237823eb8fbaafdf06128f3cc8d2c17c16fb696b92415274 |
| `vdot-field-guide-2026` | extracted | 91 | extraction_checked | 3c311ed030cbba7e91f684092c32b26cc7eb55d625f47eb1c1f3eaf94378c8b4 |
| `vdot-known-errors` | extracted | 4 | unreviewed | bec29b070d4cbe642761fd8a666331df6d48d220346a56d3c9ad2fc0e2a7f80b |
| `fhwa-mutcd-11-r1` | extracted | 1852 | extraction_checked | f508594285e5fccc45714660cc6aba1f895ae88226449345582fbbc1ceb7ba07 |
| `osha-workzone-facts` | unavailable | 0 | unreviewed | No download: HTTP 403 |
| `vosh-program` | extracted | 5 | extraction_checked | 8f5ed3e4daf8d25c5bd27bd4fae7083af72b52f3d58a12cd5ba990ac9b46f3ae |
| `vosh-regulatory` | extracted | 3 | extraction_checked | 1c77a3805cd1fa99badb03e7b904f92169a6dd28aa4077d3b84a9c6a4ab12c13 |

Total: **2,604 indexed passages from six downloaded sources**. The FHWA file contains the complete manual, including Part 6; search is not restricted to Part 6. Catalog: `knowledge/sources.json`. The known-errors document complements the VDOT manual but does not automatically correct its extracted text.

## Evidence and limitations

- VDOT manual: visual sample at physical page 12 (printed page 2). Field guide: physical page 14 (printed page 12). FHWA: physical page 807 (printed page 766). Text and physical citation targets matched the rendered originals. Checks are samples, not an audit of every page or diagram.
- VOSH: extracted heading labels were checked against the downloaded HTML. These are program/regulatory reference pages; the linked standards were not recursively ingested.
- Download, extraction, sample-check, and project applicability are distinct. No document has project applicability approval. Effective dates remain unset where no unconditional effective interval was established.
- OSHA fact-sheet download returned HTTP 403. It remains visible as unavailable; no replacement document or successful coverage claim was fabricated.
- Municipal requirements, permit conditions, official form templates, complete VOSH/OSHA standards, and project-specific applicability resolution remain gaps.
- The initial FHWA extraction timed out; its original was retained and successfully retried with PDFium. The Windows SQLite replacement issue found during the first run was corrected by closing database handles before replacement.
- Original documents and local metadata are excluded from Git and container uploads. Back them up together; GitHub contains the code, catalog, and this checksum report, not the downloaded document cache.

## Validation

All **25 automated tests** passed in the final validation run; dependency consistency and whitespace checks also passed.

- Automated coverage: valid/invalid inputs, page and heading extraction, blank/unreadable PDFs, network failures/timeouts, approved and rejected redirects, streamed size limits, duplicate/changed/reverted documents, preserved originals, extraction retry, review flags, superseded flags, corruption-safe rebuilds, filters/pagination, nonlocal denial, and existing V2 preview behavior.
- Real loopback HTTP checks passed for catalog browsing, source download status, citation search, agency filters, empty results, unknown IDs, and query limits.
- Rebuilding the live index preserved search results across all 2,604 passages.
- V1 main.py remained unchanged. Dependency consistency checks passed; this is not a production security or dependency audit.
