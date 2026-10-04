# Atlas concurrent trial: invocation permission failure

October 3, 2026 Eastern (request timestamps are October 4 UTC).

## Result

The bounded pair is **not accepted**. One request returned explicit busy503 in
2.660s; the other returned provider_error503 in 2.741s. Neither produced a model
reply. The improved runner correctly rejected the pair and sent no retry.
Sanitized evidence: `knowledge/atlas-concurrency-20261003.json`.

Application diagnostics identify upstream HTTP403 after0.46s. The model service
request log at00:53:25.843511Z reports the IAM principal lacks
`run.routes.invoke`. The scoped invoker grant command succeeded before enabling
the app. Policy propagation is a hypothesis, not a verified root cause; inspect
the effective caller, target/audience and binding timing before another paid run.
This is not evidence that the model lacks capacity or generates poor answers.

## Preparation and cleanup

Cloud Shell synchronized to8661653; three focused mocked-HTTP runner tests passed
there. Active operator admin@workzoneos.org. Preflight app00027-2j9 Atlas0, trial
inference absent. Preserved model directory and system SQL proxy rediscovered
after shell restart. Synthetic accounts and saved job were prepared before GPU
deployment. Controller1794 installed independent30-minute guard1922 before
deploying the approved pinned configuration, then sent exactly two requests.

Controller source hash:
`dc096c0edafaad5d317dbb384a8b6ec54abafce97a8a845cbf7aa2129c82ffd1`.
Local source `.local-data/concurrent-session.py`; remote source/evidence prefix
`/home/admin_/wzos-evidence/concurrent-20261003-`. Private fixture state is
`/home/admin_/wzos-grounding-ZCyfzy/concurrent-20261003-fixtures.json`.

Disable/delete/fixture cleanup each returned0. Controller live reads verified
Ready app00029-d6k with Atlas0, inference absent and fixtures disabled before
stopping guard/proxy. Subsequent process check found controller/guard absent;
an independent service description also reported the inference service absent.
V1, production and public DNS were unchanged. No customer delivery occurred.

Monitored cumulative billable inference time increased from4670.10753249346 to
4970.11058476146 seconds, no additional pages. Approximately$4.40 cumulative
compute, ~$0.27 increment at the previously recorded rate. Excludes storage,
builds and billing lag. Refresh usage before any further trial under the$15 cap.

## Next

1. Diagnose private invocation permissions using the saved grant and correlated
   request evidence; verify actual service identity and target/audience.
2. Add an explicit invocation-readiness check to trial setup. Keep authorization
   private; do not enable unauthenticated access or silently retry inference.
3. Run another bounded pair only after that preparation is verified, with a fresh
   budget check, independent guard and synthetic fixtures.
4. Sustained capacity and production acceptance remain open. UI waiting/Stop
   acceptance from the preceding local synthetic browser tests remains valid.
