# Account and private-file browser validation

2026-09-24. Synthetic accounts and records only. Google Authentication Emulator
15.31.0, Firebase Admin SDK verification, SQLite and LocalFiles on loopback.
No production identity provider, email delivery or Google Cloud Storage was used.

## Confirmed results

| Check | Evidence |
| --- | --- |
| Signup | In-app browser created synthetic owner; emulator emitted verification action |
| Unverified sign-in | Workspace denied access with verify-email message; API 403 |
| Resend verification | Browser action produced a new emulator verification code |
| Verified owner sign-in | After local verification, browser displayed organization creation/selection |
| Organization creation | Operator activation consumed; organization displayed owner and Enterprise entitlement |
| Password-reset request | Browser displayed acknowledgment; emulator recorded PASSWORD_RESET; no actual email |
| Sign-out and reload | Login screen returned; fresh sign-in required |
| Invitation/member access | Owner invited synthetic member; member joined using email-bound token; no Team access button and no owner work order visible |
| Saved work order | Browser created draft and reopened it after reload and application restart |
| Private attachment upload | In-app browser uploaded synthetic PNG to saved work order and showed Attachment saved |
| Private attachment download | Chrome fetched authorized file and wrote a 68-byte local download; downloaded bytes matched original SHA-256 |
| File access boundary | Real HTTP: anonymous 401; unrelated unverified account 403; existing unit tests also cover verified cross-organization 404 |
| Forms hub | Browser created and saved synthetic incident draft; additional Chrome form-upload automation blocked by extension file-URL permission |

Download SHA-256:
`53c90da2a16e00ba48fcb96fb94f48661c98b7602fee64423b36e150a1e6db95`.
Evidence copy: ignored `.local-data/browser-validation/browser-downloaded-attachment.png`.
Browser download-event waiting timed out; filesystem bytes, not that event API,
establish successful Chrome download. Final visual screenshot attempt was blocked
when the Chrome connection became unavailable. Responsive visual QA remains open.

## Defects corrected during this pass

- Renamed global `open()` to `openWorkOrder()`: the editor did not open in the
  controlled browser until the conflict with browser window opening was removed.
- Permit top-level GET navigation to the account login shell from another site.
  Loopback host/client restrictions remain; cross-site API requests still fail.
- Clear stale verification messages when organization selection opens and repair
  garbled account separators.
- Provide a visible Save file link after fetching an attachment, with a bounded
  blob lifetime, for browsers that do not start the download automatically.
- Add explicit demo-only emulator configuration, fixed loopback endpoint and
  hosted-runtime rejection. Never enable this in a deployed account workspace.

## Reproduction

Install requirements-accounts.txt and Firebase CLI (validated version 15.31.0).
From repository root, in separate terminals:

```text
firebase emulators:start --only auth --project demo-wzos-validation --config scripts/firebase-auth-emulator.json
.venv/Scripts/python.exe scripts/start_account_validation.py
```

Open http://localhost:8083. Use synthetic email/password accounts only. The
emulator produces email-action links instead of delivering email. The operator
activation code is in ignored `.local-data/browser-validation/activation.txt`;
it expires and is single-use. Existing SQLite accounts refer to emulator UIDs:
preserve/export the emulator state for repeated sessions or use a fresh isolated
fixture directory after intentionally resetting test data. Do not confuse these
records with the ordinary workspace preview or customer data.

Official emulator behavior: [Firebase Authentication Emulator](https://firebase.google.com/docs/emulator-suite/connect_auth).

## Remaining acceptance

Live Google sign-up/verification/reset delivery, token revocation in production,
private GCS integration and bucket policies, upload scanning/quarantine, real
provider outage handling, and responsive visual checks remain launch gates.
Chrome's additional form-upload test requires the extension's Allow access to
file URLs setting. No cloud configuration or production readiness is claimed.

Final local suite: 141 total, **131 passed and 10 PostgreSQL cases skipped**.
Node syntax checks passed for account.js, files.js and workspace.js. The previous
isolated PostgreSQL run passed its seven integration cases; new emulator/navigation
checks ran locally and do not constitute a new PostgreSQL run.
