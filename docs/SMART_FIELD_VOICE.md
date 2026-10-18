# Smart Field Voice implementation contract

Enterprise only; selected permitted job required. One-time first-run microphone
and location setup; browser grants remain authoritative. Setup starts no recording
or background location watch and uploads no coordinates. Record starts with one
tap while permission remains granted. Audio becomes mono16kHz PCM16 WAV in browser,
is verified server-side (30s/6MiB limits), transcribed in Google US Speech V2 short,
then discarded. Transcript remains only in the review session; never persisted
or logged. A typed transcript uses the same structured extraction path.

Default-off WZOS_FIELD_VOICE_ENABLED and WZOS_FIELD_VOICE_SPEECH_ENABLED flags.
WZOS_FIELD_VOICE_MODEL_ENABLED and WZOS_FIELD_VOICE_MODEL_URL are additionally required for real extraction, independently of ordinary Atlas chat. Speech uses
workload ADC, no browser key; activation/IAM/budget and ten-recording live pilot are
separate approval gates. No new cloud resources or permissions from implementation.

New endpoints under /api/field-voice: config, jobs, transcribe, extract, drafts,
drafts/{id} GET/PATCH, drafts/{id}/send-to-office. Body versions and UUID request
IDs protect retries/stale job/draft conflicts. All routes require authenticated
Enterprise membership, org scope and current job authorization. Assigned members
can use dispatched jobs; draft work orders remain owner/admin scoped.

Extraction returns validated JSON suggestions only. No tools/actions. Unknown
facts remain null, incident priority is a suggestion, review confirmation required.
Irrelevant/empty/invalid results create no persisted business records. Saved draft
bundles contain structured fields only; explicit send atomically creates printable
DWR/incident office receipts and one in-app notice per admin. Never enqueue SMS.

## Additive startup DDL (deployment applies migration)

CREATE TABLE IF NOT EXISTS field_voice_drafts (
 id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, owner_id TEXT NOT NULL,
 job_id TEXT NOT NULL, job_version INTEGER NOT NULL, version INTEGER NOT NULL,
 payload TEXT NOT NULL, state TEXT NOT NULL, model TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, submission_ids TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS field_voice_drafts_org_owner
 ON field_voice_drafts(organization_id,owner_id,updated_at);

Uses existing form_submissions/fixture_messages/message_receipts. No destructive
DDL, no existing schema rewrites. Rollback disables flags and new entrypoints;
preserves saved bundles and existing-compatible printable receipt snapshots.
Published Daily Work Report template revision1 is append-only.

Acceptance: focused privacy/roles/tenant/assignment/version/idempotency/atomicity
and provider failure tests, microphone/location lifecycle tests, then full Node
and disposable PostgreSQL gates. Android installed-PWA permissions and actual
Google speech/Gemma structured output require separately recorded live acceptance.
