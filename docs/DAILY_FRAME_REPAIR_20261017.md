# Daily embedded frame repair - October 17, 2026

## Actual device evidence

Ray confirmed Android installed WZOS has no browser address bar or repeated install
prompt. Created one five-minute synthetic embedded meeting11:55-12:00 Eastern.
Admin room prepare/join returned and created SDK iframe. Laptop inspection showed a
blank screen/about:blank while iframe src attribute targeted tenant host
https://wzos.dailywebrtc.com. Existing root frame-src/Permissions-Policy permits
only https://wzos.daily.co. No captured console error proves the specific failure,
but the policy and observed fallback origin are incompatible.

Ray reported that the meeting appeared inside the faux TV. Device unspecified;
this is useful embedded-display confirmation, not two-way camera/audio acceptance.
A physical camera protector may obstruct the camera image; it cannot explain an
empty provider UI frame. Do not assume camera hardware is faulty. Local frame was
left and the synthetic schedule cancelled successfully at11:59 Eastern (revision2).
No further room or camera/microphone session has been started.

## Official provider evidence

Daily's CSP guide explicitly lists all three Daily Prebuilt host families and says
fallbacks must accompany each daily.co host:
https://docs.daily.co/docs/guides/privacy-and-security/content-security-policy
The SDK is served locally; no new remote script source, unsafe-eval or wildcard is
needed for this repair. Existing vendored SDK0.93.0 remains unchanged.

## Narrow policy change (DEPLOYED after approval)

When configured Daily is enabled, derive only these exact origins from the validated
tenant domain, for frame-src/connect-src and camera/microphone Permissions-Policy:

- https://wzos.daily.co (already allowed)
- https://wzos.dailywebrtc.com (new exact fallback)
- https://wzos.dailywebrtc.net (new exact fallback)

No wildcard, unrelated tenant, key access, IAM grant, recording/transcription,
public meeting, new dependency or extra paid capacity. Browser camera/microphone
permission still belongs to the user. The two additional origins could receive
participant media/metadata during an authorized call, so deployment needs explicit
confirmation for this expanded media-origin permission.

Add a30-second bounded join timeout which destroys a stalled Daily instance and
shows a recoverable error instead of leaving the screen blank indefinitely.
Five frontend lifecycle tests passed; eight route/policy tests and five provider
unit tests passed individually. Initial command used an incorrect provider-class
name; corrected class ran successfully. Focused PostgreSQL gate next; no schema DDL.

## Deployment and rollback

After PostgreSQL gate and approval, use source-only overlay on current live image
6a2312b6ca77f675398a5858621e08e0b87e7dfd878495bc25ce01b6f950a83d,
preserve runtime configuration/ingress/secret bindings/roles and stage before traffic.
Verify exact three policy origins and daily-meetings.js. Rollback traffic100% to
wzos-v2-accounts-office-8d09c4a. No additional call until Ray resumes the controlled
two-device/five-minute test. Existing-Core/Enterprise and admin/member limits remain.

## Built combined candidate ready for review

Source4e281c612169bcb86fbd3439485c1ab0395834c4 includes Ray's supplied logo,
icons and narrow frame-policy/timeout repair. Exact PostgreSQL8 PASS/no skips,
39 focused Node checks PASS;13 focused Python meeting/provider tests PASS.
Image sha256:14b89663d97726b12f5173163ba31aa94ebf8bb7be85da3c4fb2be06fda51da1
built successfully (Cloud Build03ba2173-4629-409f-9dae-08632e36cad3), not deployed.
Guarded scripts/deploy_daily_brand_repair.sh atce168ba preserves runtime config,
checks exact live origins and artwork files, and rolls traffic back tooffice-8d09c4a
on failure. No additional call/credential/IAM changes are part of the cutover.
User approved ONLY the two extra exact fallback media origins and deployment.

## Actual cutover result

Guarded helper completed with deploy.exit0. Revision wzos-v2-accounts-brand-4e281c6
is Ready and serves100% of traffic. Runtime/annotations/ingress/secret bindings were
preserved. All25 public assets matched source hashes. Live root CSP and camera/mic
Permissions-Policy contained the exact three tenant hosts; no Daily wildcard.
Version endpoint returned200. Authenticated organization selection opened dashboard;
supplied artwork loaded319x355. No new meeting/media session or SMS was started.
Two-device audio/video and Leave indicators still require controlled acceptance.
Cloud logs/config evidence remain in $HOME/wzos-daily-frame-path.txt directory;
local screenshot .local-data/release-20261017/live-logo-release.png is outside Git.
