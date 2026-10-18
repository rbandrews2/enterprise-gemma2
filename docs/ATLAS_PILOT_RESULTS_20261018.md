# Atlas full-size private pilot - October18,2026

## Result

Approved private Gemma4 31B pilot completed. Eight synthetic operator requests,
eight successful responses. No customer prompts, tools, messages, training or
production Atlas activation. Full model remained google/gemma-4-31B-it; no smaller
model substituted. Guarded workflow and observer both exited0.

| Measure | Observed |
| --- | --- |
| Warm replies | 2.064-4.017 seconds; mean2.860 |
| Model token usage | 4823 input;466 output |
| Guard install through verified cleanup | 351.13 seconds |
| Compute-window estimate | $0.311 at listed resource rates; not verified billing |
| Model service after cleanup | Absent, independently listed |
| Guard process after cleanup | Stopped, independently checked |
| Production application | Spec unchanged; Atlas enabled=0 |

The351-second window includes deployment, identity/policy checks, evaluation and
cleanup. It is not a measurement of an end-user cold request. Storage/logging/network
and actual billing totals are separate. No repeated requests or model judge.

## Execution and access

- Harness5d04c07, approved existing dedicated model identity and model-bucket viewer.
- Pinned Google image3fbc0e08…;20CPU/80GiB/one RTX PRO6000, min0/max1, concurrency2.
- New service wzos-atlas-inference, revision wzos-atlas-inference-00001-8wt.
- Actual status URL used by the operator:
  https://wzos-atlas-inference-910004733138.us-central1.run.app
- Only explicit app-invoker binding added on that service. No public principals,
  project-wide role, new secret binding or operator impersonation grant.
- Independent one-hour guard installed BEFORE deploy, with dated and unique nonce
  ownership labels. Foreground cleanup deleted only the owned service and verified
  absence before stopping the guard session. Service deletion removed its scoped
  policy; existing model storage/viewer binding retained.
- Fresh GCS metadata verification matched all10 Google source objects by name,
  byte size and CRC32C before provisioning. No weights downloaded to laptop/Shell.
- This GCS-streaming path required no HF_TOKEN binding; that secret remains saved.
- Startup logs showed model compilation/warmup. Deployment completed successfully
  without a probe change; do not claim the tentative startup-window concern was a
  diagnosed failure. Real cold-start request acceptance remains open.

## Response review and repairs prepared

Agent review observed member scheduling refusal, no autonomous SMS/attendance/
payroll changes, study distinguished from certification, and refusal to invent
flagger positions without evidence/geometry. Raw results retain needs_human_review;
these observations do not establish field-use applicability or a safety guarantee.

The SMS answer reflected stale application-owned help, not a transport failure.
Prepared a narrow local intelligence.py context repair:

- Admin-only one-way SMS, phone consent/verification, test-mode restrictions and
  queued/sent/delivered/acknowledged distinctions.
- Embedded WZOS meetings in the TV screen, admin creation/member joining and Leave;
  optional Google Meet links still open separately.
- Completed forms: Print or save as PDF / Send to office and an actual office receipt.
- Ordinary and job destinations, in-app route map versus external Google Maps
  active guidance; correct disclosure for each Google destination transmission.
- Separate normal server-shift corrections from unverified offline device records.
- Fixed the accidental full-sentence time_clock cross-module search pattern; add
  meeting matching and admin training Video links guidance.

27 focused Atlas context/transport tests PASS (11.454s), mocked transports only.
First sandbox run could not use synthetic temp files; normal-access run exposed an
existing test-helper import-path requirement. Final run set the test path and
passed all27. Tightened wording to retain the existing compact system-prompt limit.
Owned failed-test scratch removed with checked literal path; no user data/settings
or security protections changed. Full integrated release gates are still required
before deploying this new context patch. Current public runtime remains bf9f524.

## Evidence and next step

Cloud pointer $HOME/wzos-atlas-pilot-path.txt: summary.json,artifacts.json,
evaluation.jsonl,evaluation.log,model-ready.json,model-iam.json,guard-installed-at.txt,
cleanup-before/after.json,cleanup.verified,independent-absent.json,app-before/after.json,
guard-process-after.log,pilot.exit/observer.exit. Preserve original evidence.

Next: run release gates on the context correction; validate real WZOS metadata-token
invocation and grounded saved-job/source answers in a separately bounded app-runtime
test. This operator pilot does not establish production app authentication, customer
inference availability, live source coverage or ongoing hosting authorization.

Cost basis: https://cloud.google.com/run/pricing
