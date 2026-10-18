# Personal weather and mobile cards — October 18, 2026

## Implemented locally
- Personal weather follows foreground device location with an existing grant; job selection cannot replace its readings. Independent job-site alerts/monitoring remain in a separate section.
- NWS current conditions plus up to four local-date forecast rows, high/low values and explicit missing values. No invented readings; source/stale information retained. Forecast failure does not discard official hazards.
- Weather resume, navigation and Time Tracker check location permission before calling geolocation. Only explicit device setup requests missing permissions. Browser/OS revocation and temporary grants remain authoritative. Browsers without a readable permission state need explicit setup in that session; WZOS cannot promise permanent permission.
- One-time setup explains local weather and microphone/location use; stores completion only, not coordinates. Time Tracker retains unavailable-location evidence rather than blocking clock actions.
- Mobile uses a visible vertical list of glass cards, matching the desktop sidebar. The landing launch cards also use one column; its duplicate top navigation stays hidden. The proposed drawer was removed at Ray's request. Desktop layout unchanged.

## Validation
- Weather/device/navigation focused Node checks: 23 PASS, no skips.
- Offline clock Node checks: 27 PASS, no skips (retained-permission fixture updated).
- Provider/time-location Python focused checks: 11 PASS, no skips outside sandbox. Earlier temporary-database sandbox access errors were environmental, not a passing result.
- NWS four-day high/low extraction checked with synthetic provider responses; no real device coordinates requested by the operator.
- Local browser confirmed personal weather is separate from job tools and prompts were not triggered without permission. Real Android permission lifetime and vertical mobile card visual acceptance remain open.
- No DDL, new dependency, IAM or provider account changes. No public deployment this increment. Integrated PostgreSQL/Node release gate remains required.

## Native app discussion
Retain the PWA and shared Google-backed backend. Ray confirmed: retain the PWA, then Android first, then iOS. Recommended implementation is Capacitor after an audited device/API compatibility pass. This reuses the UI while enabling native plugins; it is not the same as a fully native rewrite. Store distribution, signing, device testing and platform updates are extra work. iOS build/test tooling must be planned. No native packaging, paid provisioning or store enrollment started.
Reference: https://capacitorjs.com/docs and https://capacitorjs.com/docs/getting-started/environment-setup.

## Existing pending work
Smart Field Voice remains feature-flagged/off in production. Prior f176c53 cloud gate launched at $HOME/wzos-smart-voice-gate-path.txt; result unread after Cloud Shell attachment became stale. Do not report that gate as passed or repeat it before reading its exit files. New weather/menu changes are not covered by that old candidate gate.
