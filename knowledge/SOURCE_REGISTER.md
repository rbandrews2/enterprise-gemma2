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
