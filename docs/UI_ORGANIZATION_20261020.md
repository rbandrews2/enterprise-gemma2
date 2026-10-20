# Workspace organization and launch update - local review

## Scope
Preserve black glass, amber accents and existing menu cards. Remove the standalone
mobile Home label while retaining the Home return button on module pages. Apply a
shared spacing/type/field grid layer across mobile and larger screens. Work-order
readiness, training administration, study review, dispatch and report limitations
use collapsible secondary sections. Shorten Forms hub, schedule and study copy
without removing consent, review/approval limits, offline or delivery truth.

## Startup
Wait until deferred modules have registered before resolving the initial session.
Select the authorized landing view before querying/opening work orders. Show a
neutral launch panel instead of Work orders while connecting. Slow/error states
have an explicit retry; no artificial delay or automatic retry loop.

Cache only the generic public HTML shell and explicitly marked, versioned public
source assets. API responses, account data, uploads, exports, audio and transcripts
remain no-store and are excluded from the service worker. Explicit reload/update
fetches fresh public HTML. Existing unsaved-work update guards stay in place.
Maps worker policy adds only same-origin workers; external origins are unchanged.
This improves repeat launch availability; real Android cold launch and OS splash
behavior still require device acceptance. No background location/media permission.

## Shortcut artwork
Source wzos-logo.png exactly matches Ray's supplied WZOS_ICON_L0GO_FAVICON.png
SHA256 de2d9bcd2828fff395a33878a0e659e57091be8af84b33d9a4c072ed5e521052.
Existing 192/512 normal and maskable Android icons, 180 Apple touch icon and 144
Windows tile use that artwork. Icon references refreshed to brand=20261020; keep
manifest ID, URL, start URL and scope stable to preserve installed identity.
OS shortcut refresh is not immediate or controllable by a web page. No forced
uninstall or app-data clearing is required.

## Evidence
- Full Node suite:152 PASS, zero skipped/failed; plus3 new startup checks PASS.
- Focused Python public-shell/shortcut checks3 PASS; simulator checks4 PASS.
- Browser observed mobile Home without stray label, Work orders, Forms hub,
  Time Tracker and schedule. Desktop dashboard, Navigation, Messaging, training,
  meetings, Work Zone Report and Forms hub inspected. Some synthetic-only APIs
  (My jobs/dispatch) return404; this is not live acceptance. Smart Field Voice,
  real media/location/install and production-account admin tools need their own
  existing acceptance rather than synthetic preview claims.
- Screenshot: .local-data/ui-sweep-20261020/forms-desktop.png (ignored synthetic).
- Simulator recovered after Ray reopened the URL. Final follow-up inspected Home,
  Forms hub, training and route planner at390px and compact Home at360px. Page
  scrollWidth equals viewport width (375/375 and345/345 after scrollbar). Route
  inputs are16px and equal306px widths. No standalone Home label. Correct logo
  resolves with brand20261020. Core member hides Enterprise/report/admin options;
  switching back restores Enterprise admin Home. No provider, recording, location
  or send actions were run. Screenshot: .local-data/ui-sweep-20261020/mobile-home.png.

## Release / rollback
LOCAL ONLY. No production cutover, cloud inference, SMS or schema change.
Keep deployed Field Voice flags and original RTX min0/max1 unchanged. Complete
final visual review, integrated Python/PostgreSQL release gate and exact build /
staged asset/auth/config checks before deployment. Reverting this increment is
schema-compatible. To retire a deployed shell worker, serve a same-origin retirement
worker that deletes only wzos-public-* caches and unregisters; do not clear private
browser storage or unrelated caches. Do not simply delete a deployed worker route.

Photo-report concept saved separately in FUTURE_PHOTO_REPORTS.md; not implemented.
