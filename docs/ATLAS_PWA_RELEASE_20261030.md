# Atlas and PWA release evidence

## Atlas repair and PWA update release deployed - October 30, 2026

Live: wzos-v2-accounts-atlas-2992d86, 100% traffic, app version
106c379b7fa757dfe873e77b. Code commits: 46c0a13 (Atlas), 2992d86 (PWA).
Image digest: e9872ccadc1f9b4f53b5c4401537d30cd32c5868c163fabd58fe0f667548138d.
Cloud Build f6679e61-98b2-4a60-ad93-b262190f9439 SUCCESS.

Validation: 977 PostgreSQL/backend tests passed in 441.307s, zero skips/errors/
failures; temporary database cleanup verified. Full Node suite 200 PASS. A live
browser check found explicit updates could load a stale shell via the 1.5-second
startup fallback. Repaired only app-updates.js to navigate to a versioned query
URL, which the worker does not intercept. Reran all 200 Node tests successfully;
reused the unchanged backend gate. Browser synthetic stale-cache check: one click
loaded the new release and removed the update prompt. Live original session
showed the update banner; final live update URL loaded the exact latest version
with no repeated prompt. Installed Android-specific acceptance was not run here.

Live API/HTML/worker release IDs match; version endpoint and shell are no-store.
Atlas JS matches the committed archive; updater JS matches the tested patched
file byte-for-byte. Initial raw working-file mismatch was CRLF normalization,
not deployed content drift. Existing identity, resources, secrets, environment,
private model settings, source package and ingress preserved during staging.
No migrations, IAM grants, customer sends or paid inference calls. Ask Atlas's
actual answer quality on Ray's questions remains for in-app acceptance.

Rollback: route traffic to wzos-v2-accounts-atlas-061900a (pre-repair), or
wzos-v2-accounts-atlas-46c0a13 (Atlas repair without PWA fix).
Cloud evidence: ~/wzos-release-46c0a13 and ~/wzos-release-2992d86.
Local evidence: .local-data/release-46c0a13 (Node logs, candidate ZIP, live-version,
update-prompt.png and pwa-one-click-pass.png). Source ZIP SHA256:
31f26287e70a953dfbc01d9e932cd58b6e1fa6ae9fe15e14701393ed745a138a.
Browser returned to sign-in on reload because Stay signed in was unchecked;
this was the existing shared-device policy, not a failed installation.

