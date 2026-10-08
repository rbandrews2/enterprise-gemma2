# Mobile access and sign-in acceptance

Ray's requirement: members primarily use smartphones; admins primarily use desktops/laptops. Both roles must work on either device. Screen size never grants permissions.

## Implemented layout increment
- Two-column glass module navigation on phones, one-column work area, wrapping controls, 44px minimum tap controls and 16px inputs.
- Scrollable desktop sidebar and bounded mobile account dialogs. Preserve native password-manager autocomplete.

## Authentication status

Persistent sessions now implemented locally in the integration candidate; not deployed or real-provider accepted. See PERSISTENT_SESSIONS.md. Passkeys are implemented in the integration candidate, disabled by default pending PostgreSQL, Google custom-token signing and device acceptance; see PASSKEYS.md.

## Required authentication acceptance
- Explicit unchecked-by-default choice: Stay signed in on this device; alternate Sign in each time. Explain expiry and shared-device use.
- Unchecked mode retains memory-only bearer/refresh tokens. Checked mode exchanges a fresh ID token for a secure HttpOnly session cookie and clears JavaScript tokens.
- Implement server-verified secure HttpOnly session cookies with CSRF protection, same-origin validation, bounded lifetime, explicit logout, revocation checks and membership revalidation on every request. Restore organization only after access is checked. No passwords or refresh tokens in localStorage.
- Define the lifetime in the UI. Firebase session cookies support a maximum of 14 days; staying signed in is not indefinite.
- Passkeys via WebAuthn: verified challenge, origin and relying-party ID, replay prevention, user verification, enrollment after recent authentication, removal and recovery. Face/fingerprint/device PIN handled by the authenticator; WZOS does not store biometric templates. Password/recovery fallback remains available.
- Browser close alone is not a reliable logout mechanism because browsers may restore sessions. Specify and test what Sign in each time means across reload, reopening, multi-tab and installed-app cases.

## Acceptance before launch
Phone widths320/360/390/430, tablets768/1024, desktop1440; portrait/landscape, keyboard/zoom, no horizontal overflow, safe areas and Atlas overlay. Real iOS Safari and Android Chrome: persistence opt-in/out, restart, expiration, logout, lost device/revocation, role/org changes, offline transitions and passkey success/cancel/recovery. Emulator preview is not biometric acceptance.

Official references:
https://firebase.google.com/docs/auth/admin/manage-cookies
https://developers.google.com/identity/passkeys

October8 desktop browser: synthetic same-origin provider verified opt-in cookie restoration after reload/new tab, logout across tabs, and opt-out login after reload. Not a full browser-process restart or real-phone/Google integrated acceptance.
