# Shared header notifications — local candidate

The header expands to hold a dedicated Notifications area only when a notice is
present. On mobile Home the same area sits in the WZOS header section beneath the
organization/account controls; module pages and desktop use the normal topbar.
The old form-review panel is no longer inserted before content or among menu cards.
Training now uses the same header notification area as every other page.

Form-review, assignment and Atlas Security notices use the shared area and existing
actions/access boundaries. Their text/border pulse amber without hover until clicked.
The message and action remain after acknowledging the visual effect; a click never
marks a form reviewed, accepts a job or resolves a security incident. Existing
explicit review/confirmation actions remain required. Reduced motion uses a steady
amber indicator. Empty areas collapse; no form-review notice is shown to members.

A notification's visual acknowledgement survives navigation and routine polling
within the current session. Changed notice content/count reactivates its effect;
changing account or restarting the page resets this local visual state. The form
summary API supplies an aggregate count, not an individual-notification history.
No database/schema/API change, notification send, customer record change or new
permission. App-update/install prompts retain their separate existing workflows.

Validation: 21 focused Node checks PASS, zero skips/failures, covering receipts,
notification refresh/acknowledgement/rearming, role/session changes, assignments,
security explicit actions, received-form preview and mobile Home. Browser confirms
static in-header placement, active animation without hover, Review forms opening
office forms and stopping animation without changing form review status; desktop
header placement and mobile Home/training placement accepted. Screenshot:
.local-data/header-notifications-mobile.png (synthetic, ignored). Local simulator
http://127.0.0.1:8081/__simulator. Not deployed.
