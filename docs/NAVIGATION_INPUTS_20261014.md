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

## Accepted deployment

Exact9ef9ac4bd2340d0ffc5ddb2932100bc899452ea3: final full Node92 PASS;
native PostgreSQL555 PASS in173.602s, no skips/failures/errors. Test database
cleanup verified before build. Buildc0544f8c-b6ac-4ec3-af1b-ba09c9ddd90f SUCCESS;
seven build-context files91.4KiB including Dockerfile, frozen sources verified.
Image sha256:37045d3a9076c38e76a1c900546517fffc3faac07d7778cff91757bf87a31111.
Revision wzos-v2-accounts-00044-xim deployed and moved to100% after candidate
configuration comparison. No schema, new key, IAM, load-balancer or AIRA changes.
All existing environment/configuration preserved except Twilio version pinning below.

Live five JS/CSS assets match exact committed Git bytes. First byte comparison
against the Windows working copy found CRLF differences; canonical Git comparison
passed without code/image change. Manual route endpoint returns401 without login;
all six authentication-origin/security checks PASS after deployment. Browser preview
shows both fields with empty job list;390px viewport fields stay within width.
Actual authenticated Google manual-route response remains user acceptance, not
established by unauthenticated checks or the synthetic preview.

## Twilio credentials secured

Live metadata audit confirms three Secret Manager references, no inline runtime
credential values and no public individual-secret IAM bindings; runtime has
secret-specific accessor grants. Pinned inspected enabled versions: account SID1,
auth token1, sending-number2. No secret values read or printed. Existing SMS test
mode/recipient restriction, public URL and AIRA voice webhook unchanged. Full suite
includes signature/authorization tests; no message sent during this release.
Private service/policy snapshots: Cloud Shell $HOME/wzos-navigation-20261014.
Rollback: move application traffic back to00041-pem; its prior secret references
remain part of that revision. Do not modify data or the auth-origin repair.
