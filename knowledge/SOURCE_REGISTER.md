# Jurisdiction and traffic source register

Created 2026-09-17. Discovery seeds only: these links are not an ingested knowledge base or a completed jurisdiction coverage audit.

| Source | Intended use | Coverage still needed |
| --- | --- | --- |
| [FHWA MUTCD publication page](https://mutcd.fhwa.dot.gov/kno_11th_Editionr1.htm) | Discover the federal traffic-control manual and revision information; the page identifies the 11th Edition with Revision 1, December 2025 | Extract reviewed sections, especially temporary traffic control; establish applicability to each project and state adoption rather than assuming the newest national edition is the entire governing rule set |
| [VDOT Work Area Protection Manual and Field Guide](https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/work-area-protection-manual-and-pocket-guide/) | Starting point for Virginia work-zone publications | Verify governing edition, effective dates, road ownership, project specifications, locality supplements, permits, and approved forms; Virginia is a recovery starting point, not an approved default for all jobs |
| [FHWA Traffic Monitoring Guide: methodologies](https://www.fhwa.dot.gov/policyinformation/tmguide/tmg_2022/traffic-data-methodologies.cfm) | Interpret traffic count methods and distinguish measured counts from derived annual averages | Obtain project-specific state/local count datasets with segment, direction, collection period, units, and quality metadata; this guide supplies no project traffic volume or posted speed |

## Required source record

### Virginia launch authority map

Virginia is the confirmed initial customer market. FHWA issues the national MUTCD; VDOT's Virginia Work Area Protection Manual (VWAPM) serves as Part 6 of the Virginia MUTCD. The [VDOT publication page](https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/work-area-protection-manual-and-pocket-guide/) identifies version 11.0, January 2026, and applicability after January 18, 2026 with exceptions involving older contracts/permits and district approval. Record those project dates and exceptions before selecting an edition; do not treat the manual as optional advice throughout.

Add these worker-safety sources to the curation backlog:

- [OSHA highway work-zone publications](https://www.osha.gov/publications/bytopic/highway-work-zones): accessible field reference materials; separately curate the applicable standards and interpretations rather than treating a fact sheet as the entire rule set.
- [OSHA State Plan FAQ](https://www.osha.gov/stateplans/faqs): Virginia has an OSHA-approved plan covering private-sector and state/local government workers, subject to coverage exceptions.
- [Virginia DOLI VOSH program overview](https://doli.virginia.gov/wp-content/uploads/2023/03/VOSH-Media-Packet_-FINAL-DRAFT082022.pdf): identifies DOLI as the administrator of VOSH. This older overview establishes program context only; verify current VOSH standards and jurisdiction exclusions from official sources before operational use.

End-user access must cover VDOT, FHWA, OSHA, and applicable VOSH material through searchable references and source-linked answers. Local road-authority and permit requirements remain part of project resolution even within Virginia. None of these additions constitutes completed ingestion or legal applicability review.

For each adopted document or dataset store: stable ID, issuing authority, official URL, title, jurisdiction and road scope, edition/revision, publication and effective dates, supersession relationship, retrieval time, content hash, usage/retention constraints, reviewer, and validation status. Individual citations also need section/page or dataset record identifier and the supporting passage/value. Unknown dates remain unknown.

For forms additionally store: official form identifier, version, applicable activity, required fields, submission recipient/process, signature requirements, and template checksum. A website form label such as C85 does not identify its jurisdiction or current official template.

Coverage per pilot jurisdiction must include applicable federal/state/local work-zone and worker-safety sources, road-authority specifications, permit/closure requirements, forms, accessibility/pedestrian provisions, and approved project-specific conditions. Identify applicable occupational-safety authority and official sources during curation; no complete worker-safety corpus has been recovered.

## Retrieval and review rules

Filter by project jurisdiction, authority, activity, and project date before retrieval. Keep binding requirements, guidance, company policy, and project-specific approval separate. Surface conflicts for qualified resolution; do not mechanically select the strictest sounding paragraph. Require source revalidation when a revision changes, preserve the evidence used by issued packages, and prevent retrieved text from granting tools or permissions.

Traffic values and speed evidence need independent provenance and freshness checks. A posted speed must come from an applicable official record or verified field evidence; the language model must not infer it from road appearance. Historical traffic counts must retain their measurement dates and estimation methods.

## October 1 pavement-marking foundation

Preserved VDOT2020 Road and Bridge Specifications, July2022 supplement, and Virginia MUTCDv11.0. These add3714 passages; local index6332 includes historical revisions. Existing FHWA MUTCD supplies federal marking candidates. Actual-catalog planning endpoint returned200 with candidates for marking design, materials, removal and retroreflectivity; revision/page/edition evidence is in pavement-marking-20261001.json. New documents remain unreviewed; this is candidate discovery, not competent installation advice or approved layout. Broad removal keyword may retrieve unrelated removal provisions; relevance review remains necessary.

Official publication pages:
- https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/road-and-bridge-specifications/
- https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/virginia-mutcd/

Open marking gaps: September2026 special provisions/copied notes package; relevant sections234/235/246/704 and amendments; approved product lists; applicable standard drawings; material/manufacturer instructions and SDS; surface preparation/removal methods, environmental constraints, weather/cure/reopening conditions, inspection/acceptance and retroreflectivity; contract forms and training. Verify project-specific contracts before applying any numeric limits. No new source snapshot has been cloud-deployed, and no model response was evaluated this pass. Originals remain ignored local data.

Road-work coverage expansion requested by Ray: pavement marking first, followed by paving/milling/patching, utilities/excavation, signs/signals/electrical, barriers/bridges/drainage, surveying/inspection/roadside maintenance, and mobile/emergency operations. These later collections are planned, not implemented.

### October 1 relevance and amendment inventory follow-up

Marking material/removal/visibility queries now require pavement-marking terms. Regression rejects unrelated bridge removal and sign visibility fixtures. Actual-library removal candidates changed from unrelated broad matches to VWAPM physical274 and specifications physical727; visibility includes Virginia MUTCD619 and FHWA580. These remain keyword candidates, not section-complete or applicability-reviewed guidance. Evidence: marking-relevance-20261001.json.

Downloaded the publisher-linked Latest_Specs.zip (23,785,246 bytes;521 members) into ignored .local-data/marking-amendments-20261001. Inventory/hashes: marking-amendments-inventory-20261001.json. Fourteen filenames match234/235/246/704, including base sections, supplements, special provisions and copied notes. No member was executed or extracted to disk; no archive content entered the search index. These Word documents need bounded extraction, precise archive/member provenance, table/paragraph checks and contract selection review. Filename membership does not establish applicability or a complete list of relevant amendments.

Next implement controlled DOCX/archive ingestion for this verified package, review marking-specific changes, and retain base/supplement/provision relationships. Existing PDF/HTML downloader remains strict; do not rename DOCX as PDF or silently flatten tables into approved requirements.

### October 1 combined Word ingestion, retrieval and snapshot pass

Implemented operator-only pinned-archive DOCX ingestion. Catalog entries bind exact archive SHA256 and top-level member name; only matching archive bytes are accepted. The reader enforces compressed/original and expanded-size bounds, safe unique member names, XML declaration rejection, macro rejection and tracked-change rejection. It executes no Word content or external relationships. Text passages retain paragraph or table-row positions; archive member is included in search citations and original Word bytes have their own revision hash. No invented DOCX page numbers. Tables/layout, headers/footers/images and automatic numbering require visual review; none are certified by extraction.

All14 marking-related files ingested successfully,984 added passages,7316 total including history. They remain unreviewed. Member names distinguish base BK, supplemental SS, special SP/SQ and copied-note cn documents, but their applicable relationships and issue dates require contract review. Extracted text includes conditional applicability to resurfacing programs and particular contract types; never combine every file as a universal rule. Planning now transmits applicability notes and Atlas instructions require preserving this distinction.

Operator usage: `python -m services.v2.knowledge.cli ingest-archive ARCHIVE_PATH SOURCE_ID [SOURCE_ID ...]`. Ordinary `ingest all` cannot silently fetch pinned archive members; it records an unavailable attempt without deleting preserved originals. Refresh the catalog pin only after verifying a new publisher archive and retain previous originals.

Validation:195-test full suite179passed/16database skips; focused Word/planning reruns after final schema changes. Synthetic tests cover unsafe paths, expansion limit, macros, tracked changes, XML declarations, table/paragraph positions, mismatched archive hash, duplicate ingestion, retained revisions and snapshot integrity. In-process HTTP/source and search checks used all14 real documents; planning returned200 with applicability notes. Evidence: marking-word-ingestion-20261001.json and marking-word-validation-20261001.json.

Prepared `.local-data/source-deployment-20261001`:139 hashed files, verified index and original/extraction integrity, preserved missing-source states. This is local preparation only, not cloud deployment. Archive and snapshot remain ignored and are not GitHub-backed. Next visually review representative marking tables and conditional provisions, improve document-specific relevance, then transfer/verify snapshot and run bounded private Atlas citation tests within the existing approved budget. NIOSH retrieval, current federal amendments, road-authority/project applicability and final layout approval remain open.
