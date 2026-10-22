# Form signatures

Deployed October22 as wzos-v2-accounts-ui-358cf45 with eight focused PostgreSQL
checks passing. This supersedes the historical local-only status below. See
FORMS_WEATHER_RELEASE_20261022.md; phone handwriting/PDF acceptance remains open.

Scope: optional signing pad on WZOS printable forms, with signer name, Clear,
touch/mouse/pen input and typed-name alternative. Printed/downloaded forms and
immutable office review display the same signature. Does not edit uploaded PDFs.

API: CompletedForm gains optional signature object, version1, mode drawn/typed,
signer_name and normalized point strokes. Strict server validation rejects markup,
non-finite/out-of-range points, oversized input and inconsistent modes. Server
stores only validated vector points/name in the existing organization-scoped JSON
snapshot; no tables/columns/startup migrations. Existing no-signature records remain
compatible. Existing submission IDs, retries and immutable payload hashes apply.

Rollback: disable new capture UI while preserving saved signature JSON. Older
readers may omit displaying it, so retain the new renderer for signed-report review.
This is a captured mark, not an identity-verified or cryptographic signature.

Implemented locally in forms-hub.js/CSS, form_submissions.py and the existing
office reviewer. Four Node tests PASS (pointer lifecycle/clear/typed escaping and
print geometry), eight SQLite-backed form-submission tests PASS (including signed
snapshot/retry/isolation and geometry/size validation). No skipped cases in those
focused runs. JS syntax and diff checks PASS.

Simulator: incident form shows the responsive white signing area, signer name,
Clear and typed alternative. A synthetic typed signature submitted successfully
and produced the office receipt/alert. A real browser click generated a visible
vector mark; coordinate drag is unavailable, so continuous handwriting was exercised
through pointer-event tests. Real-phone finger/stylus acceptance remains open.
Print/download use the same tested document
renderer; no claim of an actual exported PDF visual check yet.

Local-only; not deployed. PostgreSQL validation of the affected submission tests
and real-device check remain before release. No new startup DDL or cloud access.
No customer messages sent; synthetic records only. Existing live design unchanged.

Screenshot: ignored .local-data/mobile-simulator/signature-pad-review.png.
Preview running on8083 (launcher14828/worker13988). No external dependency added.
