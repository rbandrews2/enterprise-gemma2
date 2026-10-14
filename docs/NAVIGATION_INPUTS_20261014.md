# Navigation route inputs and paragraph sizing — October 14, 2026

## Cause and change

The existing navigation renderer showed its route form only after opening a saved
job's directions. An empty job list therefore left only an overview map. This was
a UI flow limitation, not evidence of a stale deployed image.

Normal navigation now always provides start and destination addresses. Job and
assignment routing still prefill the destination and resolve it server-side from
the permitted record/frozen assignment snapshot. A manual address cannot be combined
with a job/assignment identifier to override its authorized destination. Both routes
retain verified user/organization access, bounded input, per-user/organization rate
limits and existing Google Routes provider. No schema or credentials change.

Overview's second heading is Map. Long prose beneath the map and empty-job advice
are removed. Genuine unavailable/offline/error status remains visible. Paragraph
CSS preserves each inherited/explicit base size and adds exactly1pt (1.3333 CSSpx);
non-paragraph labels, controls, card sizing and colors remain unchanged.

## Validation and release gate

Local navigation Python20:12 passed,8 PostgreSQL skips. Full Node92 passed before
the final small destination-input lock/empty-advice adjustment; final gate pending.
Browser preview: normal route fields present with no saved jobs, Map heading;
computed paragraph9px→10.3333px and16px→17.3333px. Synthetic preview has no Maps
credentials and did not call Google. Screenshot ignored under .local-data.

Required before live release: final Node suite and exact-candidate native PostgreSQL
gate, preserving source library and existing production origins/IAM/secrets. Build
only changed runtime files onto00041's immutable image. Verify new assets and auth
origin gate; user confirms real authenticated map/route behavior afterward.
