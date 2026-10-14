# Embedded WZOS meetings investigation — October 14, 2026

## Request and existing implementation

Ray wants an interactive meeting inside the existing faux TV, preserving admin-only
meeting creation and member joining. He authorized investigation of an embedded
engine. No provider account, subscription, media transmission or provisioning has
been requested or performed in this investigation.

Current UI: static/index.html meeting-screen, modules.js loadMeetings; links open
Google Meet separately. modules.py ModuleRecord validates only Meet URLs; existing
organization-scoped schedule records and admin edit checks should be reused.
The existing Meet URLs must remain usable through an explicit external option.

Google's documented SDK embeds an app inside Meet; REST manages meetings. Its Media
API consumes conference media, is a developer preview and is closed to new signups.
No supported standard Meet meeting-UI embed was identified. Public Meet homepage
header inspection did not itself prove iframe blocking; do not cite that probe as
proof that every Meet response has X-Frame-Options DENY.

## Compared options

**Daily Prebuilt — recommended first implementation (engineering judgment).**
Embeddable video UI plus customizable prejoin/lobby/controls and server-issued,
room-bound expiring meeting tokens. Reuse faux TV container. No media VM to operate.
WZOS app/auth/database remain in Google Cloud; call audio/video uses Daily's media
infrastructure. This is a provider change, not a Google Meet embed. Actual Android,
iOS and laptop camera/microphone/network behavior must be tested before acceptance.

Published video pricing: first10,000 participant-minutes/month free; next tier
$0.004 per participant-minute.10 people ×60 minutes =600 participant-minutes;
$2.40 marginal cost once free allowance is consumed.20,000 participant-minutes
in a month = approximately$40 video transport after the10,000 free allowance.
Recording, transcription and other add-ons are separate; keep them disabled.
This is current published pricing, not a negotiated quote or purchase commitment.

**Self-hosted Jitsi — option for Google Cloud media ownership.**
Documented iframe API and self-hosted Docker deployment. Proposed Compute Engine
host with its required media networking and JWT authorization; operations include
TLS, firewall, upgrades, moderation configuration, TURN/network testing and capacity.
Software availability does not make hosting free. Need a workload-specific VM,
egress and operations quote before provisioning. Do not use a public shared room
as tenant isolation, and do not assume a token automatically enforces admin moderation.

**LiveKit self-hosted — viable for a more custom future call interface.**
Documented VM deployment tested on Google Cloud; requires media UDP/TCP networking.
More client UI implementation than a ready prebuilt call interface. Not the first
recommendation for this narrowly scoped faux-TV requirement.

## Proposed integration contract

1. Preserve existing organization/member/admin and edition boundaries. Only admins
   create/cancel meetings; authenticated authorized members can join their meetings.
2. Add provider/opaque-room metadata to approved schedule records through a reviewed
   migration/compatibility plan. Do not accept arbitrary iframe hosts or tokens from
   browser input. Preserve existing external Meet records without rewriting them.
3. Backend creates private rooms and issues per-user room-bound, short-lived join
   tokens after fresh tenant/membership/meeting-status checks. Daily is_owner is an
   internal provider flag derived from WZOS admin role, not a new WZOS owner role.
   Recording/transcription off; prejoin camera/mic check; bounded participants/time.
4. Store provider API key only in Secret Manager, with scoped runtime access. Browser
   receives only its short-lived join authorization; no token in logs/localStorage.
5. Mount iframe/SDK in meeting-screen; keep responsive TV bezel/cards, fullscreen
   and Leave controls. Camera/mic requested only after explicit Join. Destroy call
   on leaving/canceling/sign-out/organization switch; keep cancellation failures visible.
6. Cancellation blocks new tokens and ends/ejects an active provider meeting. Token
   expiration alone is not proof of immediate revocation for an already joined call.
   Track participant usage and enforce room expiry/limits to bound costs.
7. Test admin/member/tenant denial, expiration/cancellation, double-click races,
   failed provider responses, denied permissions, phone rotation/fullscreen, network
   reconnection and actual Android-to-laptop audio/video. A simulated iframe is not
   live call acceptance. No real meeting created during this investigation.

## Next decision

Choose managed Daily media or self-hosted Google Cloud media before implementation.
Then prepare local adapter/UI/contracts and review exact provider setup, recurring
cost and data flow before account/credential/cloud changes. Investigation does not
authorize accepting provider terms or creating credentials. Live Google Meet option
and production meeting page remain unchanged.

## Verified primary sources

- Google APIs: https://developers.google.com/workspace/meet/overview
- Media preview: https://developers.google.com/workspace/meet/media-api/guides/overview
- Daily embed/customization: https://docs.daily.co/docs/prebuilt/customizing-daily-prebuilt
- Daily pricing: https://www.daily.co/pricing/video-sdk/
- Daily tokens: https://docs.daily.co/reference/rest-api/meeting-tokens/create-meeting-token
- Jitsi iframe: https://jitsi.github.io/handbook/docs/dev-guide/dev-guide-iframe/
- Jitsi deployment: https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-docker/
- LiveKit VM deployment: https://docs.livekit.io/transport/self-hosting/vm/

Provider discovery skill inspected first. Directory CLI is unavailable locally;
public Directory setup page was consulted, but no Directory search was performed.
Comparison uses the primary sources above, not a claimed directory/catalog result.
