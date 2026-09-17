# Jurisdiction and traffic source register

Created 2026-09-17. Discovery seeds only: these links are not an ingested knowledge base or a completed jurisdiction coverage audit.

| Source | Intended use | Coverage still needed |
| --- | --- | --- |
| [FHWA MUTCD publication page](https://mutcd.fhwa.dot.gov/kno_11th_Editionr1.htm) | Discover the federal traffic-control manual and revision information; the page identifies the 11th Edition with Revision 1, December 2025 | Extract reviewed sections, especially temporary traffic control; establish applicability to each project and state adoption rather than assuming the newest national edition is the entire governing rule set |
| [VDOT Work Area Protection Manual and Field Guide](https://www.vdot.virginia.gov/doing-business/technical-guidance-and-support/technical-guidance-documents/work-area-protection-manual-and-pocket-guide/) | Starting point for Virginia work-zone publications | Verify governing edition, effective dates, road ownership, project specifications, locality supplements, permits, and approved forms; Virginia is a recovery starting point, not an approved default for all jobs |
| [FHWA Traffic Monitoring Guide: methodologies](https://www.fhwa.dot.gov/policyinformation/tmguide/tmg_2022/traffic-data-methodologies.cfm) | Interpret traffic count methods and distinguish measured counts from derived annual averages | Obtain project-specific state/local count datasets with segment, direction, collection period, units, and quality metadata; this guide supplies no project traffic volume or posted speed |

## Required source record

For each adopted document or dataset store: stable ID, issuing authority, official URL, title, jurisdiction and road scope, edition/revision, publication and effective dates, supersession relationship, retrieval time, content hash, usage/retention constraints, reviewer, and validation status. Individual citations also need section/page or dataset record identifier and the supporting passage/value. Unknown dates remain unknown.

For forms additionally store: official form identifier, version, applicable activity, required fields, submission recipient/process, signature requirements, and template checksum. A website form label such as C85 does not identify its jurisdiction or current official template.

Coverage per pilot jurisdiction must include applicable federal/state/local work-zone and worker-safety sources, road-authority specifications, permit/closure requirements, forms, accessibility/pedestrian provisions, and approved project-specific conditions. Identify applicable occupational-safety authority and official sources during curation; no complete worker-safety corpus has been recovered.

## Retrieval and review rules

Filter by project jurisdiction, authority, activity, and project date before retrieval. Keep binding requirements, guidance, company policy, and project-specific approval separate. Surface conflicts for qualified resolution; do not mechanically select the strictest sounding paragraph. Require source revalidation when a revision changes, preserve the evidence used by issued packages, and prevent retrieved text from granting tools or permissions.

Traffic values and speed evidence need independent provenance and freshness checks. A posted speed must come from an applicable official record or verified field evidence; the language model must not infer it from road appearance. Historical traffic counts must retain their measurement dates and estimation methods.
