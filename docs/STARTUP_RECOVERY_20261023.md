# Installed-app slow launch investigation

User reports four to five days of intermittently minute-long launch waits on an
installed Samsung Android PWA. Repeated Try again eventually reaches sign-in.
Voice later generated accurate work-order/report details, but an initial attempt
still appeared frozen. Do not mark device Voice acceptance fully passed.

## Findings and repair

- Startup configuration/session/order reads had no deadline. Added a 20-second
  deadline covering headers, fetch and JSON parsing, with cancellation.
- Try again used location.reload, discarding in-memory sign-in unless the user
  had opted into persistent sign-in. It now reconnects in place, preserves the
  selected identity after authorization, and prevents overlapping retries.
- Saved-session network failure was presented as Sign in to continue. Now a
  failed connection offers Retry saved sign-in; only401 is treated as sign-in
  required. Authentication, authorization and opt-in persistence remain intact.
- Service-worker reload bypassed its public-shell fallback and could hang behind
  the OS splash. Reload now uses the existing1.5-second cached public-shell
  fallback when available, still preferring fresh HTML. No private/API caching.
- One public live measurement: HTML first byte1.103s,total1.127s;
  /api/identities first byte0.287s. These warm observations do not reproduce or
  rule out intermittent mobile/network/server cold-start latency.

## Evidence and scope

Integration a7c2722:196Node PASS. Isolated release8cb99c2 based on liveb1bc598:
192Node PASS, zero failures/skips. Four new regressions cover in-place retry,
ignored-abort deadlines, stalled reload fallback, and saved-sign-in network retry.
Local logs in TEMP/wzos-startup-node.log and wzos-startup-isolated-node.log.
No paid AI calls, customer sends, IAM, capacity, schema or persistence changes.

Cloud CLI authentication restored by user. Synthetic browser retry check PASS:
the shipped startup script recovered without page reload. Screenshot is ignored
at .local-data/startup-recovery-release/.local-data/startup-recovery.png relative
to the integration checkout; synthetic harness does not authenticate a real user.

Five-day Cloud Run launch-route query found32 responses over5s, maximum89.661s.
The89.661s and35.284s responses occurred on older ui-bc0f30a, not currentb1bc598.
Currentb1bc598 system events show about8–16s between autoscaling instance start
and successful startup probe. No configured minimum warm instance; revision
max2, service max20, CPU throttling true, startup CPU boost true. This supports a
cold-start contribution, not a claim that every reported delay has one cause.
No infrastructure settings changed. Evidence files contain timings/revisions,
not request bodies, credentials or customer identifiers.

## Live release accepted

937 PostgreSQL checks PASS in436.671s;192Node PASS; zero failures/errors/skips.
Build d5cf322a-382a-4133-842f-120930787854 succeeded. Preflight/schema/configuration
drift/no-traffic staging/public assets/anonymous boundaries/traffic checks PASS.
Independent readback: wzos-v2-accounts-ui-8cb99c2 at100%; version
198c9e683b53fc65521a7139; image SHA256
e726e890bc116b5c5db5025b10ce9b72ba037c7e1ee14c79e3c4e50a79490f1d.
Public warm HTML first byte0.238s,total0.261s after deployment; this does not
measure Android startup or eliminate the known cold-start contribution.
Evidence:$HOME/wzos-startup-evidence-20261023. Cloud pointer:
$HOME/wzos-startup-path.txt. Installed-phone launch acceptance remains open.
Do not claim the underlying minute-long delay has been fully diagnosed. Do not
change paid minimum instances without a concrete cost/scope decision.

Rollback when deployed: wzos-v2-accounts-ui-b1bc598, image
5d4f65627f800637abf23315bacf2b5b703ac3d388e6f9af799764240512dcf3.
Bulk account feature remains separate and undeployed.
