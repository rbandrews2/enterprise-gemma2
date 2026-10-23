# Smart Field Voice unresponsive controls repair

User reported all controls freezing after one recording. Code inspection and
synthetic reproduction found an unbounded browser wait while `busy` blocks the
global navigation guard. Recording conversion, auth refresh and fetch/JSON reads
could hang; no processing cancellation was exposed. Cancellation/session changes
could also retain an aborted controller or allow a late microphone result to
interfere with the next attempt. This reproduces a lock path; the specific phone's
network/provider failure is not independently established.

## Repair

- Bound permission lookup (10s), microphone acquisition (20s), audio decode and
  resampling (15s each), recorder stop event (5s), ordinary requests (30s), Speech
  (60s) and extraction (300s, allowing the existing server's 290s ceiling).
- Keep Cancel action available while processing. Navigation can explicitly cancel
  instead of silently refusing every click. No automatic provider retries.
- Keep transcript/structured fields when cancelling or timing out. Saving/sending
  an interrupted request is explicitly uncertain; check saved reports before retry.
- Release tracks, ignore stale recorder events, stop late microphone grants, and
  detach the aborted controller before another session or attempt.
- Pending promises cannot prevent local cancellation even if fetch ignores abort.
  Cancelling browser work does not guarantee a provider operation already accepted
  by the server has stopped or that a submission did not commit.

## Scope / acceptance

Voice-only hotfix branch `codex/voice-freeze-recovery`, b1bc598, based on live
7a674b3. Only field-voice.js and its test file change. No schema, IAM, model,
microphone permission policy, retention or billing configuration changes.
Same fix retained in integration branch 4af6253; bulk account release stays separate.

12 focused Voice/receipt checks PASS; all 188 hotfix Node checks PASS locally.
Browser synthetic stalled extraction: cancel restores controls and retains text.
No real recording, employee data, paid Speech/Gemma call or customer send used.
Screenshot outside Git in voice-freeze-release/.local-data/voice-recovery-preview.png.
Cloud gate runs in path recorded by $HOME/wzos-voice-recovery-path.txt.
## Live release

Cloud gate: 937 PostgreSQL tests PASS in 432.587s, zero failures/errors/skips;
188 Node checks PASS. Build 9e2c60bb-4bb6-4084-bed3-a7a2ca898da3 SUCCESS.
Preflight, schema, configuration drift, no-traffic staging, public assets and
anonymous access boundaries PASS. Independent traffic readback confirms
`wzos-v2-accounts-ui-b1bc598` at 100 percent.
Version `a325abc4daf59053d4f10e85`; image SHA256
`5d4f65627f800637abf23315bacf2b5b703ac3d388e6f9af799764240512dcf3`.
Rollback target `wzos-v2-accounts-ui-7a674b3` retained.
Evidence saved at `$HOME/wzos-voice-recovery-evidence-20261023` in Cloud Shell.
Real-phone recording/recovery acceptance remains human validation. No automatic
paid retest was performed. Bulk managed accounts remain undeployed.
