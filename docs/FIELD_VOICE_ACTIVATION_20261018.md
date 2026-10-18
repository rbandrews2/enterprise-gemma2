# Smart Field Voice activation scope

User goal: make the deployed Enterprise Smart Field Voice operational. Existing runtime source c944173 passed831 PostgreSQL/148 Node checks. Activation is separate from those mocked/provider-independent checks.

## Speech setup — approved and verified

In enterprise-gemma2, enable speech.googleapis.com. Create custom role wzosFieldVoiceSpeech with exactly speech.recognizers.recognize and bind it only to wzos-v2-accounts@enterprise-gemma2.iam.gserviceaccount.com. This is an ongoing project-scoped recognition permission, not secret, storage, database or administrator access. Use US Speech V2 synchronous short/en-US, no logging opt-in, no GCS audio objects. Rollback removes that one binding and disables the feature flags; do not disable shared APIs without impact review.

## Private model pilot — approved, not yet launched

Restore only wzos-atlas-inference with the existing pinned Google vLLM image sha256:3fbc0e08c46e7736145c9effbcc8839682c80b15b413335146f4428fc3523c8a, retained checksum-verified GCS Gemma4 31B weights, dedicated wzos-atlas-inference identity and existing isolated network/subnet. One RTX PRO6000,20CPU/80GiB,min0/max1,concurrency2,no public invocation. Grant only the WZOS application identity service-scoped roles/run.invoker. No HF secret binding needed.

One-hour independently owned cleanup guard; $5 pilot target including at most ten synthetic speech requests (30seconds each) and ten corresponding structured extractions, no automatic paid retries. Current listed us-central1 resources imply about $3.19 per instance-hour before allowances; speech five minutes about $0.08. These are estimates, not guaranteed billing caps; builds/storage/network/logging separate. Remove model at pilot end unless separately approved for ongoing operation. No production enablement in this pilot approval.

Pilot execution workload/image and production operation will be separately documented and approved after their commands/harness are reviewable. No customer audio, data or SMS in synthetic acceptance. Raw audio/transcripts are not persisted by WZOS; only reviewed structured report fields may be saved. Test metadata excludes raw transcripts/audio.

## Remaining acceptance / activation

Validate actual schema-constrained output on pinned model, negation/corrections/incidents/unknown quantities/irrelevant speech/injection, transient transcription, review/edit/idempotent atomic office submission and zero SMS. Silence/noise and device permission/microphone shutdown checks supplement the ten spoken fixtures. Installed Android retained permission must be checked by the user; no autonomous microphone recording.

Live activation preserves ordinary Atlas chat configuration and existing database/storage/secrets/ingress/billing/weather. It must not accidentally enable unreviewed general Atlas chat. Prepare a feature-specific model transport switch if the existing shared flag would enable it. Ongoing resource budget and activation scope require review before changing production flags.

Sources: https://cloud.google.com/run/pricing ; https://cloud.google.com/speech-to-text/pricing ; https://docs.cloud.google.com/iam/docs/roles-permissions/speech

## Prepared implementation
Final runtime candidate95bc0f8 isolates voice from ordinary chat and adds processing notices. Prior candidate passed832 PostgreSQL/148 Node checks; final gates are running. Generated synthetic audio archiveSHA256 f70a0cdae930dc9b315d2a47660f3a7b8f54e17452b81e42373b0e545c200436; uploaded to Cloud Shell only, not Git or customer storage. Cloud validation pointer: $HOME/wzos-field-voice-path.txt. User approved scoped Speech setup and bounded private model pilot. Speech setup completed with FIELD_VOICE_SPEECH_SETUP_VERIFIED: enabled API and exact one-permission role/binding read back. No GPU/job creation or public activation yet.

## Disposable pilot job — approved and launched

Final runtime95bc0f8: PostgreSQL832/Node149 PASS, no failures/skips; mocked workflow PASS. Cloud Build0b19c5a6-5fbe-4700-88e5-bf2ee6d8b39b SUCCESS. App image sha256:798c479ccdae437d4929b0903379df598c26f7ac6e37f8977c9e5e354566ebf9. Pilot image us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/wzos-v2-field-voice-pilot@sha256:5f666853c3f6a8047e60f949d6e368abd3e4f6328e85fc7090ff7b925220276e. Immutable identities verified from build results, not mutable tags.

Prepared run_field_voice_pilot.sh creates only wzos-field-voice-pilot using the separately built synthetic harness image and existing WZOS app identity. One task,15minutes,1CPU/512MiB,no retries. Identity retains its existing effective permissions, although the reviewed harness uses no database, secret or bucket bindings and only temporary local persistence. Ten synthetic Speech attempts,8–10 structured extractions; no customer sends. Remove job and model with ownership checks and independent cleanup verification. Request exact-image approval after build; existing model approval does not authorize this job identity assignment.

User separately approved exact pilot5f666853… job identity assignment; guarded run launched in the existing Cloud Shell, PID41745. Outcomes and cleanup are not yet accepted. No automatic paid rerun if any case fails.

First pilot stopped during model startup: vLLM rejected obsolete `--disable-log-requests`; no job was created and no Speech/extraction request ran. Owned model and job absence verified (`FIELD_VOICE_PILOT_CLEANUP_VERIFIED`, pilot.exit1). Repair uses supported `--no-enable-log-requests` and checks that exact argument. Deployment/pilot helpers copied from the reviewable repair commit outside the frozen95bc0f8 source, so app and synthetic job images remain unchanged. The previous job-identity approval remains unused; request a new bounded model pilot after reviewing this repair. Same resources, $5 target, one-hour cleanup, no automatic paid retry.

Reference: https://docs.vllm.ai/en/v0.21.0/configuration/engine_args/ (request logging flags).

## Production activation — NOT yet approved

After real pilot acceptance and verified cleanup, deploy the immutable app image from runtime95bc0f8 with only four Field Voice environment changes. First stage a same-image disabled revision, then enabled revision without traffic; compare existing identity, secrets, database/storage configuration, resources and ingress. Preserve ordinary Atlas chat OFF and all unrelated integrations. Switch public traffic only after these checks; hash public assets and verify anonymous API denials. Rollback routes traffic to the same-image disabled revision and preserves drafts/submitted reports; no destructive DDL or new migration is included.

Ongoing processing requires a separately approved restoration of the same private model with existing model-read identity/network, only WZOS invocation and request logging disabled. Min0/max1 bounds instances, not spending. Listed GPU+20CPU+80GiB resources total approximately $3.19 per allocated instance-hour (about $76.48/day if continuously allocated), plus Speech $0.016/minute and other build/storage/network/logging charges before allowances. No always-warm scheduler or probes. Obtain explicit ongoing operating authorization or a time/budget-bounded live window before deployment. The one-hour synthetic pilot approval does not cover customer operation. Failed activation disables new processing and removes only the newly owned model, with absence verification. Successful activation leaves the approved model available; real installed-Android microphone permission, recording and shutdown acceptance remains user-led.
