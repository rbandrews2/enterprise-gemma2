# Smart Field Voice activation scope

User goal: make the deployed Enterprise Smart Field Voice operational. Existing runtime source c944173 passed831 PostgreSQL/148 Node checks. Activation is separate from those mocked/provider-independent checks.

## Speech setup — approval required

In enterprise-gemma2, enable speech.googleapis.com. Create custom role wzosFieldVoiceSpeech with exactly speech.recognizers.recognize and bind it only to wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com. This is an ongoing project-scoped recognition permission, not secret, storage, database or administrator access. Use US Speech V2 synchronous short/en-US, no logging opt-in, no GCS audio objects. Rollback removes that one binding and disables the feature flags; do not disable shared APIs without impact review.

## Private model pilot — approval required

Restore only wzos-atlas-inference with the existing pinned Google vLLM image sha256:3fbc0e08c46e7736145c9effbcc8839682c80b15b413335146f4428fc3523c8a, retained checksum-verified GCS Gemma4 31B weights, dedicated wzos-atlas-inference identity and existing isolated network/subnet. One RTX PRO6000,20CPU/80GiB,min0/max1,concurrency2,no public invocation. Grant only the WZOS application identity service-scoped roles/run.invoker. No HF secret binding needed.

One-hour independently owned cleanup guard; $5 pilot target including at most ten synthetic speech requests (30seconds each) and ten corresponding structured extractions, no automatic paid retries. Current listed us-central1 resources imply about $3.19 per instance-hour before allowances; speech five minutes about $0.08. These are estimates, not guaranteed billing caps; builds/storage/network/logging separate. Remove model at pilot end unless separately approved for ongoing operation. No production enablement in this pilot approval.

Pilot execution workload/image and production operation will be separately documented and approved after their commands/harness are reviewable. No customer audio, data or SMS in synthetic acceptance. Raw audio/transcripts are not persisted by WZOS; only reviewed structured report fields may be saved. Test metadata excludes raw transcripts/audio.

## Remaining acceptance / activation

Validate actual schema-constrained output on pinned model, negation/corrections/incidents/unknown quantities/irrelevant speech/injection, transient transcription, review/edit/idempotent atomic office submission and zero SMS. Silence/noise and device permission/microphone shutdown checks supplement the ten spoken fixtures. Installed Android retained permission must be checked by the user; no autonomous microphone recording.

Live activation preserves ordinary Atlas chat configuration and existing database/storage/secrets/ingress/billing/weather. It must not accidentally enable unreviewed general Atlas chat. Prepare a feature-specific model transport switch if the existing shared flag would enable it. Ongoing resource budget and activation scope require review before changing production flags.

Sources: https://cloud.google.com/run/pricing ; https://cloud.google.com/speech-to-text/pricing ; https://docs.cloud.google.com/iam/docs/roles-permissions/speech
