# Recovery reuse and design decisions

Confirmed direction from Ray, 2026-09-21: prioritize compatible surviving V1 files, folders and settings to shorten delivery without sacrificing quality. Use gloss black with existing WZOS colors in an organized, task-focused app.

## Applied now

- Reused existing V2 ProjectDraft, SiteContext, JobGeometry, Atlas preparation, evidence review and local reference discovery directly. The workspace adapter reads one saved work-order revision; it does not create a competing editable project.
- Inspected recovered `api-v17/static/styles.css`: dark green base, green accents, gold `#f4c542`, system/Inter font stack. Retained those palette cues with gloss-black panels, compact controls, visible keyboard focus and expandable references. Original files are unchanged.

## Next reuse candidates

- Existing V2 measured-approach/scenario editor and Maps/Street View integration: adapt to the scoped work-order API, retain source provenance and existing credential restrictions. Port 8083 is not currently an authorized Maps browser-key referrer.
- Recovered V17 has PDF/package manifest, Street View, delivery and email-preview functions. Extract isolated rendering/payload contracts with fixtures before reuse. Its fixed-position overlay is not verified geographic sign placement. Do not wire historical endpoint/bucket/auth settings into V2 unchanged.
- Preserved Core React forms, time clock, navigation and organization workflows remain the intended source import. Follow CORE_INTEGRATION_PLAN.md and existing parity/security gates; the local vanilla workspace is an interaction/API prototype.

No production or Cloud Shell changes are authorized by this styling/reuse increment. Recovery data and credentials remain outside Git; off-device backup is still an open launch gate.
