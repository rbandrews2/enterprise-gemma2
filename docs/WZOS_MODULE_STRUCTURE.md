# WZOS module structure

## Product direction confirmed by Ray

WZOS is one application with distinct modules, shared organization and user access, and Atlas assistance throughout. Integrating a previously standalone app does not remove its identity as a module.

| Module | Purpose |
| --- | --- |
| Work orders | Basic job details and everyday work-order management |
| Forms hub | Find, complete and manage operational and safety forms |
| Video training | Training videos, courses and completion workflows |
| Time clock | Its own clock, task, break and time-history workspace |
| Navigation | Maps, routes and navigation workflows |
| Messaging | Crew and organization communication |
| Schedule management | Work schedules, assignments and coordination |
| Work Zone Report | Comprehensive job package combining a basic work order, detailed imagery, Atlas recommendations, diagrams, required forms, recommended forms and supporting material |

Atlas is a cross-module assistant, not solely a report generator. Organization/admin tools and edition/role permissions are shared foundations. Existing plans place advanced report/planning capabilities in Enterprise; final entitlement details remain to be finalized. Production branding: WZOS powered by Atlas AI Assistant.

## V1 inspection

Read the user-opened signed-in https://app.superiorllc.org application. The organization page navigation separately lists Admin Dashboard, Time Clock, Work Orders, Navigation, Forms, Messages, Training and Scheduling. The home page's Access modules cards separately link Organization, Forms Hub, Time Clock, Work Orders, Messages, Training / Video Center, Navigation / Maps, Scheduling and Video Conference. These are observed navigation entries, not proof every backend function currently works. No customer records, organization settings or production code were changed.

Reuse that module separation in V2's more app-like interface. Marketing/module explanations remain on workzoneos.org; the eventual unified functional app is app.workzoneos.org. Do not copy V1's promotional homepage or unverified headline metrics into the app.

## Current implementation and next structural work

Time clock already has its own sidebar entry and dedicated view. Both editions share its implementation while retaining scoped data. Work orders remain a separate view. Other module names are shown as unavailable until functional integration is complete.

Work Zone Report is now explicitly represented in navigation but is not enabled as a complete report module. Current source preparation inside work orders is a reusable report component, not the entire report. Next structural increment should give the report its own workspace, select/link an existing work order, and compose the existing planning, source and geometry components before adding imagery, diagrams, forms and package delivery.

Keep one authoritative work-order record. Reports reference a specific work-order revision and preserve the basis of recommendations; changing a work order must mark dependent report material for review. Time entries may link the same work-order ID without requiring a report. Forms should be accessible directly from the hub and linkable into a report. Avoid separate copies of job details in every module.
