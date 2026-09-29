# Virginia source coverage audit — September 29, 2026

## Scope and result

Local metadata audit supporting remaining-task item 3. No web verification, ingestion, cloud changes, model calls, or publication/applicability approvals were performed. This audit describes the preserved September 28 snapshot, whose source retrievals and link-verification dates are September 17. It does not establish which publications are current today.

The catalog has **seven sources; six preserved documents contain 2,604 passages**. Five documents have sampled extraction checks; one remains unreviewed. The OSHA fact sheet is unavailable. **No preserved document has project-applicability review.**

## Recorded coverage

| Source ID | Recorded edition | Preserved passages | Recorded review | Main remaining work |
| --- | --- | ---: | --- | --- |
| `vdot-vwapm-2026` | 11.0 January 2026 | 649 | extraction_checked | Verify publication/edition applicability, exceptions, diagrams and relevant tables; resolve amendments |
| `vdot-field-guide-2026` | January 2026 | 91 | extraction_checked | Verify current guide and matching manual; review diagrams/table layout for intended scenarios |
| `vdot-known-errors` | Unknown | 4 | unreviewed | Verify which manual edition the errors apply to and review each correction before linking it to recommendations |
| `fhwa-mutcd-11-r1` | 11th Edition Revision 1 December 2025 | 1,852 | extraction_checked | Resolve state/project applicability and review relevant Part 6 sections; index currently includes the full manual |
| `osha-workzone-facts` | Unknown | 0 | unreviewed/unavailable | September 17 attempt returned HTTP 403; verify an accessible official publication route without bypassing access controls |
| `vosh-program` | Unknown | 5 | extraction_checked | Overview only; curate applicable linked standards and jurisdiction exclusions |
| `vosh-regulatory` | Unknown | 3 | extraction_checked | Reference page only; curate underlying requirements and effective dates |

### Review and supersession limitations

- `extraction_checked` means the recorded sample/heading checks passed, not that every page, diagram, or legal requirement was reviewed.
- Every preserved manifest has `effective_from` and `effective_to` unset and `applicability_reviewed=false`. Project dates, road ownership, contract/permit conditions, exceptions and authority remain necessary inputs.
- The snapshot contains one revision for each downloaded source. No superseded revision is demonstrated by this snapshot. Absence of a superseded flag does **not** prove that an external publisher has not replaced it.
- The catalog labels three manuals/guides `current_at_verification`, dated September 17; the remaining four publication statuses are `unknown`.
- The manuals record seven little/no-text page warnings in total: VWAPM physical page 414; field guide pages 2 and 92; FHWA pages 2, 4, 1157 and 1161. These may be expected blank/image pages; classify them by inspecting the originals before claiming extraction completeness.
- Recorded visual samples: VWAPM physical page 12/printed 2; field guide physical 14/printed 12; FHWA physical 807/printed 766. Accurate sample references do not validate placement diagrams elsewhere.
- The known-errors file is separate from the manual. Its presence does not mean corrections have been incorporated into extracted manual text.

## Coverage gaps affecting the Virginia pilot

1. **Local authority:** no municipality-specific source is present in the seven-entry catalog. Norfolk example jobs therefore have no cataloged Norfolk permit, road-owner, closure, local supplement, or official-form evidence. Resolve the actual road authority for each site before selecting requirements.
2. **Worker safety:** the OSHA fact sheet is missing, and VOSH HTML pages do not constitute an ingested standards corpus. Work-type hazards require curated underlying official material, not only a traffic-control manual.
3. **Forms:** no official form template is a catalog entry. Recycled V1 worksheets must be distinguished from authority-issued forms and given verified version, recipient, signature and submission metadata.
4. **Traffic and speed:** no project traffic-count dataset or posted-speed record is cataloged. The traffic-monitoring methodology link in the register is a discovery seed; it provides no site-specific measurements.
5. **Placement evidence:** extraction alone does not supply reviewed, machine-readable sign-spacing/flagger/geometry rules. Relevant diagrams, tables, units, conditions and exceptions must be checked against originals for each supported scenario.
6. **Freshness and recovery:** preserved hashes establish identity, not continuing currency. Revalidation, supersession relationships and restoration of source originals/metadata need an operational procedure. The September 28 source-enabled image supersedes the older status document's statement that documents are excluded from all container uploads; general source caches remain ignored by Git.

## Prioritized next actions and acceptance evidence

1. **Revalidate the seven official publication links.** Record verification time and publisher edition/status; compare downloaded content hashes through the approved ingestion command. Retain existing revisions and explicitly flag inaccessible or replaced documents. Completion: a dated publication comparison with no unknowns silently upgraded to current.
2. **Review VWAPM corrections and placement-source extraction.** Determine the known-errors file's affected edition, inspect warning pages and the diagrams/tables for the first supported scenario, and record physical/printed page references. Completion: reviewer notes and cited scenario evidence; no automated applicability approval.
3. **Fill worker-safety coverage for the pilot work types.** Resolve the OSHA fact-sheet access failure through official sources and curate actual VOSH/OSHA standards references appropriate to the pilot scope. Completion: successful preserved downloads or explicit unresolved gaps with jurisdiction notes.
4. **Complete one pilot locality before broad expansion.** Start with Norfolk, already used in saved-job testing: verify road ownership, permits/closures, local supplements and official forms from the responsible agencies. Completion: a locality coverage record tied to a representative site's authority and dates. A city name alone is insufficient.
5. **Attach independently sourced project evidence.** Add dated speed/count records and approved project conditions; keep field measurements, official records and estimates distinguishable. Completion: values retain origin, collection date, units and limitations.
6. **Document the controlled update/review cycle.** Define curator/reviewer responsibility, revalidation triggers, supersession behavior, preserved-report citations and missing-source presentation. Rebuild from retained originals/metadata and confirm previously issued citations remain traceable. Completion: documented procedure and a restoration/check example.

These actions prepare the reference foundation for Maps/placement and report work. Until those checks are complete, Atlas should present candidate references and missing evidence, with qualified review required for project-specific recommendations.

## Evidence inspected

- `knowledge/sources.json` — seven approved catalog entries and September 17 link-verification metadata.
- `knowledge/SOURCE_REGISTER.md` — jurisdiction, forms, traffic and review requirements/discovery seeds.
- `docs/SOURCE_BACKEND_STATUS.md` — original extraction counts and sampled validation evidence.
- `.local-data/source-deployment-20260928/snapshot.json` and six revision `manifest.json` files — preserved revision counts, review flags, warning pages and effective-date fields.
- `.local-data/source-deployment-20260928/attempts/osha-workzone-facts.json` — recorded HTTP 403.
- `docs/ATLAS_SOURCE_STAGING_20260928.md` — source-enabled image/snapshot preservation evidence; its pending inference result is historical and is not used to assess the later live test.
- `docs/REMAINING_TASKS.md` — sequence and scope of reference-foundation work.

No source originals or application code were changed by this audit.
