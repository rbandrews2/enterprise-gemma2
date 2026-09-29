# Initial offline support

Implemented locally September 29. Not cloud-deployed or full offline/PWA acceptance.

- Navigation uses already-authorized loaded destinations during connection loss. A user can save an address-only destination sheet for later use. No map tiles, imagery, live traffic or turn-by-turn routes are cached.
- Time clock retains its last confirmed active shift and labels the disconnected view. The running timer is an estimate. Confirmed clock commands and retry are blocked while the browser reports offline; reconnection refreshes the server state without replaying attendance changes.
- Users can keep up to 50 device-timestamped offline time notes in the open tab, download them as JSON and supply them for review. These are unverified notes, not punches or payroll records. Notes are not automatically synchronized or imported.
- Clock state/notes use organization plus actor scope and clear on scope change. Tokens are not persisted. Notes require download before closing/signing out; a before-unload warning is present. Keep downloaded employee/job files private on shared devices.

This is open-session offline support. Reloading/starting the app offline is not supported: no service worker or private authenticated shell cache has been introduced. Google Maps may use its own separately configured offline capabilities; WZOS does not guarantee that behavior.

Validation: two Node behavior tests verify stale-clock preservation, offline write blocking, online refresh, separate notes and organization-change clearing. Both modified JavaScript files pass syntax checks. Twelve Atlas API/guidance tests pass after capability-copy updates. Real desktop/mobile offline browser acceptance remains pending.

Next: user-reviewed offline attendance draft synchronization with captured and received timestamps, original shift/version, idempotency, conflicts and admin review. Do not replay ordinary time commands: current backend timestamps them at server receipt. Design authenticated offline reopening and storage/retention separately. Validate real navigation offline behavior and provider imagery permissions before any map-cache work.
