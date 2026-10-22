# Operational follow-ups and validation reuse — October 22

User requested completing the three sweep2 findings. This authorizes the
configuration repair; new security-sensitive access still needs browser-policy
confirmation at the action. No customer cleanup or test alert is implied.

## Work and acceptance

- [ ] Connect a monitored email/channel to the four existing operational policies.
  Destination requested; no recipient assumed. Preserve existing thresholds.
- [x] Replace database/auth key `latest` references with verified version1 on the
  unchanged deployed image. Stage without traffic, compare runtime/security
  configuration and image digest, check readiness, cut over and verify matching
  HTML/API release markers, unchanged assets/auth/security directives and anonymous
  denial. Preserve prior revision for rollback.
- [ ] Resolve retired-file delete access under the prepared single-permission
  bucket scope. Approval question pending; no grant or customer cleanup performed.
- [x] Record Ray's successful Smart Field Voice incident/report notification and
  review-clear acceptance. See the [validation ledger](VALIDATION_LEDGER_20261022.md).
- [x] Consolidate passing tests, failed-run repairs, source/image provenance,
  evidence locations and reuse rules so unrelated passing tests are not repeated.

## Secret pinning scope

`scripts/pin_runtime_secrets.py --apply` reuses the immutable digest of the
currently serving revision, not the development branch's newer application code.
It changes only WZOS_DATABASE_URL and WZOS_AUTH_WEB_API_KEY secret selectors from
latest to numeric1 after fresh metadata checks establish that1is their sole
enabled/listed version. No payload access, key rotation, image build, IAM,
application source, schema or feature flag change.

If runtime/security configuration drifts, stop before traffic. If cutover fails
its public checks, restore baseline traffic and verify rollback. The deployment
marker includes K_REVISION and Maps CSP nonces rotate per response; compare
stable content while preserving all security directives. Do not rerun
891backend or174Node checks for these unchanged-image configuration selectors;
the relevant evidence is the exact diff, same digest, readiness/public acceptance
and rollback provenance. A later new application image needs its own applicable
release gates; the ledger must not blur those two cases.

## Cleanup access scope

The precise proposed role/binding/rollback and backlog risks are in
[FILE_CLEANUP_ACCESS_PROPOSAL_20261022.md](FILE_CLEANUP_ACCESS_PROPOSAL_20261022.md).
The user has been asked for action-time confirmation because granting a new
delete permission materially expands runtime access. Do not run customer
backlog cleanup to validate the grant. Use policy readback and any separately
authorized bounded synthetic workflow; preserve Atlas holds and retry behavior.

## Evidence

### Numeric selector repair completed

- Live revision: `wzos-v2-accounts-pins-1022181839`, 100% traffic.
- Rollback: `wzos-v2-accounts-ui-16d0905`, retained.
- Same image digest: `80c3819aa9e8d3ce38ccf47e87bd4015b40875768a54604e994da9674cb3c054`.
- Public release marker: `7e5e09892935f9d2ba1ba6d6` (new revision, same app bytes).
- Only the two database/auth selector keys change from latest to1. Fresh secret
  metadata showed1as their sole enabled/listed version. Other runtime spec,
  role identity, service ingress, scaling and security annotations match baseline.
- Ready condition, immutable digest, zero-traffic stage, final100% traffic,
  matching HTML/API marker, unchanged public asset/auth/security fingerprints and
  anonymous session401 PASS. Final runner `pins-resume2.exit0`.
- Two conservative verification attempts rolled back successfully: first compared
  a revision marker literally, then a rotating CSP nonce literally. Corrected
  only those dynamic comparisons; five focused tooling guard checks PASS.
  Both failed receipts are retained. Reused the same staged revision; no image
  rebuild, model/Speech call, SMS send or broad application-suite rerun.
- Application bytes and customer records are unchanged. New development UI/security code
  is not deployed by this configuration-only repair.

Alert routing remains prepared pending the monitored email; no channel/test alert
has been created. Cleanup access remains prepared pending specific approval;
no IAM grant, API enablement or queued customer-object cleanup was performed.

Private cloud pointer: `$HOME/wzos-followups-latest-path.txt`. Runtime snapshots
and command receipts stay private, outside Git. Root:
`/tmp/wzos-followups-20261022.dBAoYjzD`; durable copy:
`$HOME/wzos-followups-evidence-20261022`. Append actual results before checking
the remaining completion boxes; prepared is not completed.
