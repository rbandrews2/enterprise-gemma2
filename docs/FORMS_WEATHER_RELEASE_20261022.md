# Forms, weather and voice review release

Authorized: deploy the previously local signature pad; compact the weather card
using the supplied crop; fix silent Smart Field Voice/form review actions; create
prelaunch checklist. See PRELAUNCH_REQUIREMENTS_20261022.md.

Changes: optional validated signatures in existing JSON submissions (no DDL);
six static assets for signing/office preview, compact weather and visible voice
review. Weather remains location-based and retains permission/watch configuration.
Blank extra metrics omitted; populated details/forecast collapse behind disclosure.
Severe alert headlines and stale/unavailable feedback stay visible.

Office Review received form now opens a labelled on-page modal, with separate print
and download actions; close/view/account transitions remove it. Mark reviewed and
request changes have success feedback. Reopened voice drafts scroll/focus the review
editor, explain what opened and retain office receipt protections.

Release overlays six reviewed static files and form_submissions.py onto the live
immutable image. No model, secret, IAM, service resource or weather monitor changes.
Stage without traffic, verify unchanged runtime policy, then cut over with automatic
rollback to captured prior revision if public asset checks fail. Schema unchanged;
backward-compatible JSON field documented in FORM_SIGNATURES_20261020.md.

Validation: focused Node checks, SQLite submission tests and disposable PostgreSQL
signature/submission class. Browser review/phone/PDF acceptance tracked separately;
never submit a customer's draft during acceptance. Actual results recorded below.

## Deployed results

- First60f7b99 release passed, then a frontend-only office-alert scroll/focus
  correction358cf45 was deployed. It does not alter the signature backend.
- Final revision wzos-v2-accounts-ui-358cf45 receives100% traffic.
- Build0e7a95d0-e79d-4818-aabc-700c218c0f5f SUCCESS.
- Image digest d1f7e2009eb186e2d9b9c36be732c7ed8baada8be93bdd50b66f2fe4646705a1.
- Version bd666b58478cbe553f66dd85. Deploy exit0; preflight/build/drift/staged runtime,
  public6asset hashes, CSP, version and traffic PASS. No rollback required.
-18focused Node checks PASS;8SQLite submission checks PASS;8disposable PostgreSQL
  signature/submission checks PASS in4.758s. No skipped cases. Final frontend-only
  change reran6related Node checks. Backend/test byte comparison verified before
  reusing PostgreSQL evidence; no duplicate database suite/model calls.
- Local synthetic signed form received office receipt; preview modal opens and
  Mark reviewed shows success. Live read-only acceptance confirms signing controls,
  modal review of an existing received form, office alert scroll/focus (top0) and
  explicit message. No real customer form sent, signed or marked reviewed.
- Final evidence /tmp/wzos-office-focus-20261022.cONJeqXR; database evidence source
  /tmp/wzos-forms-weather-20261022.t738Urx7. Pointer $HOME/wzos-forms-weather-release-path.txt.
- Immediate rollback revision wzos-v2-accounts-ui-60f7b99; original design baseline
  wzos-v2-accounts-ui-bc0f30a retained. No schema migration or runtime policy changes.

Real-phone handwriting and actual exported PDF acceptance remain prelaunch items.
Live screenshot (blank editor only) saved under ignored
.local-data/mobile-simulator/live-signature-20261022.png.
