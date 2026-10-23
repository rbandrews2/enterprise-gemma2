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

NOT DEPLOYED. Cloud Shell project enterprise-gemma2 verified, but auth list empty;
Authorize UI did not restore CLI credentials. gcloud auth login started in tab1.
Remaining: restore CLI authentication; inspect service scaling/startup logs without
printing secrets or private request data; browser evidence; required cloud gate,
isolated release preflight/build/deploy and installed-phone launch acceptance.
Do not claim the underlying minute-long delay has been fully diagnosed. Do not
change paid minimum instances without a concrete cost/scope decision.

Rollback when deployed: wzos-v2-accounts-ui-b1bc598, image
5d4f65627f800637abf23315bacf2b5b703ac3d388e6f9af799764240512dcf3.
Bulk account feature remains separate and undeployed.
