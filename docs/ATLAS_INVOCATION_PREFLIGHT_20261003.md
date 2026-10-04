# Private Atlas invocation preflight

## Findings

The previous concurrent trial failed with upstream HTTP 403 (`run.routes.invoke`).
The saved grant in `concurrent-20261003-invoke.log` names
`wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com`, matching the current
app service identity read from Cloud Shell. Its configured target is
`https://wzos-atlas-inference-udtvm4rgca-uc.a.run.app`; Atlas remains disabled.
The adapter requests a metadata ID token with that configured origin as audience.
These facts do not prove the claims of the token used in the failed request.
The model service was already deleted after the failed trial.

Google documents eventual consistency for IAM policy changes (typically two
minutes, sometimes seven minutes or longer). Propagation is a possible cause,
not a confirmed diagnosis. A successful grant command does not prove effective
invocation access. Do not fix this by enabling public invocation.

## New operator tool

Run from the repository root in Cloud Shell:

```sh
python -m scripts.validate_atlas_invocation --output /tmp/atlas-invocation.json
```

Default mode makes only three bounded gcloud reads: app service, model service,
and model IAM policy. It checks readiness, latest-revision traffic, the expected
app identity, exact canonical target/audience, IAM-check configuration, no public
policy members, and an unconditional scoped invoker binding. It neither mints a
token nor contacts the model. Missing/deleted services fail explicitly.
This narrow policy check does not evaluate inherited deny policies or all IAM
conditions, and cannot establish propagation or effective invocation by itself.

During an authorized trial with the independent cleanup guard active:

```sh
python -m scripts.validate_atlas_invocation --output /tmp/atlas-invocation-probe.json \
  --probe-with-active-budget-guard
```

This explicit option can wake a billable GPU. The flag acknowledges the external
guard requirement; the tool does not install or verify that guard. Refresh budget
and state first, keep the app disabled during preflight, and use the existing
bounded trial controller/cleanup procedure. The tool impersonates only the exact
app service identity using permissions the operator already has, checks token
audience/email/expiry, then sends one nonredirecting GET `/health`. No model
generation, retries, IAM writes, permission grants, or public endpoint are added.
Impersonation failure stops before HTTP; never substitute an operator-user token.

HTTP 200 verifies this impersonated principal's health invocation at that moment.
It does not verify the app's metadata-token path, a generated reply, cold-start
acceptance, or sustained capacity. Record those separately in the subsequent
two-request app test. A health probe can warm the model, so that pair must not be
described as a cold-start test. Failures remain failures; do not loop probes.

Evidence omits tokens, bodies and raw subprocess errors. Local JWT claim checks
do not verify signatures; Cloud Run performs authentication.

## Validation and next checkpoint

Nine focused local tests passed: six preflight tests plus three existing
concurrent-acceptance tests. Cases include identity/target/revision mismatches,
conditional/missing/public permissions, redirects/401/403/503, mismatched/expired
tokens, unavailable impersonation, default no-probe behavior and redaction.
No new live health/inference probe, paid resource, IAM change or deployment was
performed. The last verified cleanup remains app `00029-d6k` Ready/Atlas0,
inference absent, fixtures disabled; monitored compute about $4.40, excluding
storage/builds/billing lag. Full application and PostgreSQL suites were not
rerun for this isolated operator-only addition.

Next: fresh budget/state check, guarded private trial deployment, inspect policy
and run one explicit identity health probe. If it passes, enable the app and run
the bounded concurrent pair. Otherwise preserve evidence and clean up without
automatic retry. Existing operator impersonation permission is not yet verified.

## Official references

- [IAM propagation](https://docs.cloud.google.com/iam/docs/access-change-propagation)
- [Cloud Run service identity and audience](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)
- [vLLM health implementation](https://docs.vllm.ai/en/latest/api/vllm/entrypoints/serve/instrumentator/health/)
