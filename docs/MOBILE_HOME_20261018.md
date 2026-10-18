# Mobile Home — October 18, 2026

Both admin and member mobile sessions open the same black/glass vertical Home card list. Existing module navigation supplies the cards; role, edition and feature visibility remain in force. Core members do not see Enterprise Work Zone Report/My jobs or organization management. Admins retain an Organization management card for the existing dashboard controls and billing. Module pages use a compact Home return instead of repeating the full menu. Desktop keeps its dashboard/sidebar.

Implementation: mobile-home.js; guarded home view in workspace.js; mobile-only CSS; one static script route. No schema, persistence, API authorization or cloud permission changes. Removing the script and CSS and reverting the home-view hook restores the prior presentation.

Validation: 11 focused Node checks passed (mobile Home plus guided dashboard), zero failures/skips; diff check passed. Simulator browser verified Enterprise admin Home, Time Tracker without the card list, Home return, and Core member filtering with no admin card. Full-size synthetic screenshot: ignored .local-data/mobile-home-member.png. Local simulator http://127.0.0.1:8083/__simulator is running in the background. Public app unchanged. Integrated release gates and real-device acceptance remain required before deployment.
