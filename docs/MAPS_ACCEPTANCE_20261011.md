# Maps acceptance checkpoint — October 11, 2026

Twilio delivery is on hold at Ray's request while sender registration is pending.
Ray reports the corrected sender secret is saved; its new version has not been
independently revalidated. No Twilio messages are authorized by this checkpoint.

## Independently observed in restricted staging

- Revision `00032-9rw` differs from `00031-h5t` only in the environment field
  `WZOS_GOOGLE_MAPS_BROWSER_KEY`. Image, runtime identity and resources match.
- Main traffic remains 100% on `00031-h5t`; the release tag reaches `00032-9rw`
  with zero main traffic. No public invoker binding exists.
- IAM alone receives HTTP401 from `/api/maps/config`: app authentication is still
  required. `/signin` is not an application route and returned404; sign-in is
  displayed at `/`, which loaded successfully through the protected proxy.
- The authorized synthetic admin signed in and selected the Enterprise test
  organization. A clearly labelled artificial Norfolk work order with two
  reported work-limit points saved at revision1 and appeared in the report.
- Google hybrid imagery rendered, with an orange work-limit line, Google/Airbus
  attribution and the correct area. No provider/CSP errors appeared in the
  browser's captured warning/error log.
- Street View returned a nearby panorama and capture date2025-11. Controls and
  location appeared, but the embedded panorama remained black. Metadata success
  is not visual acceptance. Root cause is not established; do not claim a GPU,
  browser or provider diagnosis without evidence.

Screenshot (ignored): `.local-data/maps-staging-20261011.jpg`, showing the hybrid
imagery and black panorama. Synthetic job remains in the authorized test
organization, explicitly not a field plan. No customer data was used.

## Local improvement

Added a visible, safe external Street View fallback using Google's documented
[Maps URL parameters](https://developers.google.com/maps/documentation/urls/get-started).
It works independently of the embedded Maps loader and targets the provider's
panorama when available, with saved coordinates as fallback. Missing coordinates
produce no destination. Links use a fixed Google HTTPS origin and
`noopener noreferrer`; no API key is placed in this link.

Changed misleading shared UI wording from "Saved locally" to "Saved" and from
"Local development" to "Organization workspace". Saving still means the API
confirmed persistence, not approval or delivery. These UI improvements are local
candidate changes and are not yet deployed.

Full Node regression:49 tests passed, zero failures/skips. Two new cases verify
that the external destination remains available when embedded Maps is not
configured, and that missing coordinates produce no link. JavaScript syntax and
diff checks passed. No Python/schema change was made after the prior476-test gate.

Local visual follow-up is still open: browser control blocked the new local tab,
and the operator HTTP attempt on port8182 was correctly rejected by the existing
8081/8083 Host allowlist. That rejected request does not verify the new screen or
provider-disabled response. The temporary8182 server was stopped. Use an allowed
port for the next local browser check; do not widen the access boundary to make a
test pass.

## Remaining gates

Navigation also uses Google Maps: the live admin Navigation screen showed the
synthetic job and an `Open in Navigation` link using driving directions and
`dir_action=navigate`. The shared link helper accepts addresses or coordinates;
the module combines permitted orders with frozen assigned destinations for
Enterprise members and preserves organization boundaries. Existing full-suite
tests passed for member assigned destinations, Core limits, organization changes,
late responses, safe URL construction and unusable inputs. This handoff uses
Google's cross-platform Maps URLs; it does not require the browser imagery key.
Actual Android routing/arrival and member cloud journeys remain pilot checks.
Offline destination sheets are supported; WZOS does not claim offline turn-by-turn
navigation. Screenshot: `.local-data/maps-navigation-20261011.jpg` (ignored).

Visually accept the embedded panorama on supported browsers/Android or repair its
actual cause; test the new fallback in the browser; verify member/tenant imagery
access, representative sites and unavailable-provider behavior. Keep `00032` at
zero main traffic until acceptance. Imagery annotation, approved sign/flagger
rules, address lookup and permitted report export remain separate unfinished work.

The protected Cloud Shell proxy started with a45-minute lifetime and no automatic
restart. It does not change Cloud Run IAM or expose an anonymous workspace.
V1, DNS, production routing and Twilio delivery remain unchanged.
