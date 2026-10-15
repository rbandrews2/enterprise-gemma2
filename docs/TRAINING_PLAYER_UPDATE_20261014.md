# Training player and collapsible admin video links

## Scope

Reuses the existing organization training module/draft/version/assignment APIs.
Admins expand Video links to paste, replace or remove links, then collapse the
same control. All existing media entries (up to10) are preserved, rather than
silently discarding entries after the first. Save draft retains optimistic
version checks; publish makes the new links visible. Older published versions
and completion history remain unchanged. Members have no editor access.

Learners open a compact responsive in-app player for standard YouTube/Vimeo
links or direct HTTPS MP4/WebM/OGV media. Other HTTPS documents remain ordinary
links. Players load only after a click, with no autoplay; closing the player,
leaving the module or switching accounts unloads it. Native video has controls
and playsinline; provider restrictions may still prevent embedding, so an
original-link fallback remains available. Viewing is not assessment completion.
No video hosting, provider SDK/account/key or new database table is introduced.

Uses existing license/ownership attestation, admin/member checks and tenant
boundaries. URLs containing login credentials or nonstandard ports are rejected
server-side. Browser player selection additionally rejects HTTP, local hostnames
and IP literals; arbitrary third-party HTML is never embedded. Only fixed
youtube-nocookie.com and player.vimeo.com iframe origins are added to the root
page policy. HTTPS media sources are permitted for the native video element;
scripts/connect/auth/Maps/Daily policies remain otherwise unchanged. The server
does not download or proxy submitted media. External media loads disclose the
viewer's network information to that host when the user opens the player.

## Parallel integration

SMS_READINESS_HANDOFF_20261014.md records the independent outbox access repair.
It prevents queued sends/retries after recipient/admin/org access revocation.
Existing consent, verified-number and test-mode restrictions remain.
No real messages, provider credentials or new runtime permissions are involved.

## Validation and release

Six focused Node tests PASS: provider parsing, unsafe URL rejection, lazy load,
close/session/view cleanup, native stop behavior, all-link preservation and
bounded admin replacement/removal. New Python cases cover versioned removal,
credential-bearing links, policy and static route. Exact-source cloud Node suite:
102 passed, no failures/skips, directly inspected. Ray reported the PostgreSQL
gate:606 passed, no failures/skips. Direct final log/exit and disposable database
cleanup inspection remain pending; browser control repeatedly times out.
Browser rendering and real media acceptance remain pending. No DDL/dependency change.
This source is not yet deployed. Live remains hub-5a3ac86 until a tested release.

Real permitted-media playback on Android and desktop remains acceptance work;
the screenshot/written interaction request guided the editor. The attached
recording has not been played/transcribed in this increment. Do not claim a
provider-restricted video works merely from URL parsing or mocked tests.

Reference: [YouTube embedding parameters](https://developers.google.com/youtube/player_parameters).
