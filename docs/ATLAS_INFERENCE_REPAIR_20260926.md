# Atlas live inference repair — September 26, 2026

## Acceptance: local connection repaired; production intelligence NOT accepted

Real model requests now complete across all eight modules. The local preview at
http://127.0.0.1:8083 runs the explicitly selected 1B development model on this
computer's integrated graphics. No mock reply or paid cloud inference was used.
This is a development connection, not a production model selection or safety approval.

**Quality remains a blocker.** The smaller model sometimes omits essential steps,
hedges about known product facts, and is sensitive to prompt changes. A rejected
prompt revision incorrectly said a member could assign a crew. The backend did
not grant that permission. That revision was reverted; it was never deployed to
Cloud Run or loaded into the user-facing preview process.

## What changed

- Reduced repeated general instructions; kept invariant no-action/safety rules and
  module-specific app guidance. Related-module questions receive relevant guidance
  while retaining the user's actual role and edition.
- Added operator-only model selection (1B/4B allowlist), optional integrated-GPU
  runtime startup and a bounded preload command. No public ingestion/model-selection
  endpoint, driver changes or network exposure.
- Preserved one-request gate, cancellation, 110-second transport/120-second overall
  limits, fixed loopback destination and output bounds. Truncated model completions
  are now rejected. Chat retains loaded weights for 15 idle minutes.
- Added internal timing/token-count/error-class logs without prompt or answer text.
- Expanded real HTTP evaluation tooling with explicit model and module selection.

## Measured results

Intel N150, four CPU cores, approximately 32 GiB RAM, portable Ollama 0.34.2.
Original 4B CPU requests failed after 110-131 seconds. The runtime was skipping its
integrated Intel GPU. Opt-in Vulkan loading placed all 35 layers of the 4B model
on the GPU, but cold startup took 67.5 seconds and that request still timed out.
One warm 4B work-order request completed in 85.56 seconds with complete create/edit
instructions. This was not a full 4B quality evaluation.

The smaller model completed these **HTTP transport tests** with the retained
compact policy. Shorter latency does not establish better answer quality.

| Module | 1B CPU seconds | 1B integrated-GPU seconds |
|---|---:|---:|
| work_orders | 62.39 | 27.19 |
| time_clock | 59.28 | 20.39 |
| forms | 59.26 | 24.78 |
| schedule | 51.30 | 16.56 |
| training | 49.33 | 24.84 |
| messages | 51.25 | 13.48 |
| navigation | 53.14 | 17.03 |
| report | 55.92 | 18.03 |

Integrated-GPU preload for 1B took 22.12 seconds. These are individual observations,
not a percentile, load/concurrency benchmark or customer latency guarantee.

## Answer review

- Work orders: the 1B answer was too terse (select a job and Save); 4B provided both
  new-order fields and Save changes. Do not claim equivalent model quality.
- Clock: retained GPU test correctly required the user to click Clock in.
- Vehicle inspection: correctly said saving does not clear the vehicle, but workflow
  detail was incomplete.
- Member schedule: retained-policy test correctly denied assigning a crew. The
  rejected prompt experiment contradicted that rule; model prose is never authorization.
- Training: CPU test correctly denied certification; retained GPU test incorrectly
  hedged about organization policies despite supplied facts. NOT accepted.
- Messaging/report: retained-policy tests declined SMS sending and exact flagger
  placement. This is limited evidence, not an adversarial safety certification.
- Navigation: described the Google Maps handoff; wording remains basic.

## Browser evidence

The existing preview was restarted with `--atlas --atlas-model gemma3:1b` and its
saved records preserved. Browser displayed Atlas ready and returned a live answer
identifying the synthetic Norfolk utility crossing job and checklist version 2.
It omitted the stale-checklist conclusion in generated prose. The app-owned basis
correctly displayed job revision 5, checklist tied to job revision 3, and
**Job changed: review needed**. Therefore saved-job context transport passed;
checklist answer quality remains unaccepted.

## Regression and evidence

Full suite: 158 run, **142 passed / 16 PostgreSQL skipped locally**. Focused final
intelligence tests: 9 passed (including role/edition boundaries, related-module
facts, model allowlisting, cancellation, invalid output and truncated replies).
These tests verify application behavior, not model factual correctness.

Ignored local evidence under `.local-data/atlas-runtime/`:
- `repair-1b-modules.json` and `repair.stderr.log`: eight CPU responses.
- `repair-4b-gpu-modules.json`: cold timeout; `repair-4b-gpu-warm.json`: warm success.
- `repair-1b-gpu-modules.json`: retained-policy GPU responses.
- `repair-1b-gpu-final.json`: REJECTED prompt experiment, retained as negative evidence;
  its filename does not mean accepted/final production behavior.
- `gpu-repair.stderr.log`, `repair-regression.log`, `preview-validated.*.log`.

Model hashes and reproducible commands are in ATLAS_LOCAL_INTELLIGENCE.md. Raw local
logs/weights are not GitHub-backed. This document preserves the material findings.

## Cloud status and next step

Google Cloud Chrome tabs are at Google sign-in. A sign-in request was sent to Ray;
cloud resource/authentication state could not be refreshed. No cloud resource,
DNS, V1, public endpoint, customer message or automation schedule was changed.
The earlier one-time automation remains paused.

Next: after Google sign-in, inspect the existing inference service and prepare a
priced restricted-hosted test for a stronger model, reusing the current provider
boundary and measured evaluation cases. Existing paid staging approval excludes
additional AI capacity; do not provision a new paid inference service under that
approval. Keep local 1B available for development only. Require correct role,
training, checklist-staleness, grounded-source and adversarial answers, plus latency
and multi-user tests before calling the AI production-ready. The September 30
integrated test target remains at risk until these gates pass.
