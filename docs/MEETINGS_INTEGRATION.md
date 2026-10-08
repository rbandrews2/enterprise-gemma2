# Google Meet integration

Ray selected Google Meet; only WZOS admins create/manage meeting records. Members view and join organization meetings. This increment stores validated Meet links on existing schedule records, with existing organization scoping, admin writes, revision conflicts and history. No new DDL; optional JSON payload field meeting_url, absent on older records.

Admins create a real space in Google Meet and paste its link in Schedule management. Members open the saved schedule and select Join Google Meet. Cancelled records hide Join. Cancellation changes WZOS scheduling only; it does not terminate the Google meeting. Google host admission controls still apply. No invitations or external messages are sent. WZOS permissions do not prevent a user independently creating meetings on Google's website.

Automatic space creation remains pending. Google documents user OAuth authorization and meetings.space.created scope for POST https://meet.googleapis.com/v2/spaces. Configure an approved OAuth client, exact redirect origins, consent, secure per-organizer token storage and refresh/revocation before enabling this. Do not use the Maps key or treat Firebase sign-in as Meet authorization. Do not share one organizer identity across customer organizations.

Sources: https://developers.google.com/workspace/meet/api/guides/authenticate-authorize and https://developers.google.com/workspace/meet/api/reference/rest/v2/spaces/create

Acceptance: run test_modules.py; combined PostgreSQL and real Google browser meeting acceptance remain required. No live meeting was created during automated tests.
