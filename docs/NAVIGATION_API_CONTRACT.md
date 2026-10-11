# In-app Navigation contract

Admin and member, Core and Enterprise, share Navigation. Existing Google Maps
links remain fallback controls. Routing is read-only and does not acknowledge an
assignment, edit a job or collect background employee tracking.

## API

- `GET /api/navigation/config`: authenticated availability flags; never returns
  a server Routes credential.
- `POST /api/navigation/route`: exactly one permitted `order_id` or own active
  Enterprise `assignment_id`, plus an origin (address or latitude/longitude).
  Destination is resolved on the server. Assignment destinations use the frozen
  dispatched snapshot, not another employee's private work-order details.
- Returns one route's encoded line, distance, duration, bounded plain-text
  directions, generation time and destination/access basis. Explicit disabled,
  missing route, provider failure, invalid input and throttled states.

Use a fixed Google Routes API HTTPS endpoint, explicit field mask, single request
and bounded response/timeout. No retries or polling. Server key:
`WZOS_GOOGLE_ROUTES_API_KEY`; operator opt-in `WZOS_NAVIGATION_ROUTES_ENABLED=1`.
Never reuse/expose the browser Maps key as the server credential. Requests are
limited per actor/organization/process; Google project quotas are additionally
required for aggregate billing control across runtime instances.

## UI / privacy

Each permitted destination has an in-app route control. User explicitly enters an
origin or requests browser location, and clicks Calculate route after the visible
notice that origin and destination go to Google. No location read on page load,
continuous tracking, voice/background navigation or offline-route claim. Routes
stay in memory and clear on organization/session/view changes; stale asynchronous
responses cannot repopulate another scope. Live estimates are timestamped.

Reuse the nonce-aware Maps JavaScript loader and existing glass cards, map styling,
destination download and offline wording. Text directions remain usable when map
rendering fails. This is a web route viewer; native navigation SDK integration is
a separate product/architecture decision.

No DDL or additional package dependency. Cloud API enablement, secret creation,
least-privilege binding, billing/quotas and live Android/provider acceptance remain
explicit gates; local fake transport does not establish provider readiness.
