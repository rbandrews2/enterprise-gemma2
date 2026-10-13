# Public V2 rollback

Use the release snapshots in Cloud Shell `$HOME/wzos-release-20261012`.
Do not remove additive seat tables or customer records during rollback.

1. Restore app routing first: import `cutover-before-urlmap.json` into
   `app-workzoneos-org-url-map` after reviewing its current fingerprint. This
   returns app.workzoneos.org to the preserved V1 backend.
2. Restore accounts traffic to `wzos-v2-accounts-00031-h5t=100` if needed.
3. Re-enable the service Invoker IAM check using `--invoker-iam-check`; restore
   ingress and origin/passkey settings from `cutover-before-service.json`.
4. Remove the three newly added secret-specific runtime accessor bindings if
   reverting Twilio, and disable SMS. Never change AIRA voice webhooks.
5. Verify the public hostname, private APIs and direct run.app boundary again.

The organization-wide domain restriction was not changed. It rejected the
allUsers binding; the approved app-only public exposure uses Google's documented
service Invoker IAM check setting with load-balancer-only ingress instead.
This setting also must be reverted when restoring a fully private service.
