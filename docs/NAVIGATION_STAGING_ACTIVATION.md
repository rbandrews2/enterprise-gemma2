# Navigation staging activation — review before execution

Local implementation: `NAVIGATION_API_CONTRACT.md`. No startup DDL, dependency,
public access, production DNS or V1 change. Routes remain disabled until the
server opt-in and private credential are both configured.

## Proposed security changes

1. Enable `routes.googleapis.com` in `enterprise-gemma2`.
2. Create a dedicated key, ID `wzos-v2-server-routes`, restricted to only
   `routes.googleapis.com`. Never change/reuse the browser Maps key.
3. Save the generated value directly into Secret Manager secret
   `wzos-v2-google-routes-api-key`; do not print, copy into chat, or save in Git.
4. Grant `roles/secretmanager.secretAccessor` on only that secret to
   `wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com`.
   No project-wide secret access or new public invoker binding.
5. After the exact candidate PostgreSQL gate passes, build a candidate image and
   deploy it only as a private zero-main-traffic tag on `wzos-v2-accounts` with
   `WZOS_NAVIGATION_ROUTES_ENABLED=1` and the secret mapped to
   `WZOS_GOOGLE_ROUTES_API_KEY` at a pinned version. Retain all current secrets,
   identity, resource limits, auth settings and rollback revision.

Cloud Run's current outbound address is not assumed fixed. The server key is
API-restricted and stored privately; IP restrictions require a separately priced
egress design. Browser-control policy requires approval for the new credential
and scoped runtime access before these actions. User-entered credentials require
user handoff; automatically generated credentials must never be displayed.

## Cost and acceptance limit

`TRAFFIC_AWARE` uses Compute Routes Pro. Google's published first paid tier is
$10/1,000 requests (5,000 monthly free usage cap). Twenty controlled route calls
cost $0.20 at that tier before any available free allowance. Dynamic Maps
first paid tier is $7/1,000 loads: twenty loads cost $0.14. Cap this acceptance
run at twenty routes and twenty map loads ($0.34 combined before allowances).
Verify current SKU usage and spending before activation. Free allowances
are not assumed available. Stay within the existing $150/10-day approval.

Before enabling routing on the candidate, inspect available Google project quota
controls and apply a low supported aggregate quota. Application bounds are six
requests/actor/minute, twenty/org/minute, sixty/process/minute and four concurrent;
these are process-local, not a global spending cap. No retries/polling. The
controlled acceptance run is capped at twenty calls; stop and disable routes
after evidence collection if aggregate quota cannot be bounded satisfactorily.
Budget alerts alone are not a hard spending cap.

Test public/synthetic origins and destinations only: admin/member own jobs,
active assigned snapshot, directions/map/distance/traffic duration, no automatic
location access, Android permission denial/manual origin, cancellation/session
switch, unavailable provider. Test role denials without contacting Google.
No real employee location, SMS/MMS or customer delivery.

## Rollback

Leave main traffic on its existing accepted revision. Disable the candidate's
`WZOS_NAVIGATION_ROUTES_ENABLED` first to stop app routing, remove its test tag
when no longer needed, and revoke only the newly added secret-access binding.
Disable the Routes key through its recoverable API-key lifecycle. Do not disable
a shared project API without checking other consumers. Preserve the tested source
commit and current accepted revision/image/configuration before any deployment.

## References

- [Routes billing](https://developers.google.com/maps/documentation/routes/usage-and-billing)
- [Google pricing](https://developers.google.com/maps/billing-and-pricing/pricing)
- [Key creation flags](https://docs.cloud.google.com/sdk/gcloud/reference/services/api-keys/create)

Status: approved by Ray. The scoped setup command was submitted; Ray reported
`ROUTES_SETUP_COMPLETE` after browser control timed out. Independently verify
API/key/secret/IAM metadata before considering setup accepted. No routing
deployment or live provider call has occurred for this increment.
