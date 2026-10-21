# Black glass local review

User requested black cards, slightly wider first three menu cards, shared filled
icons and universal hover glow; moving edges limited to Enterprise options.

Implementation:
- Black glass restored across menu, hub, forms, job, meeting and account cards.
- On mobile the first three Enterprise controls remain full width; common menu
  controls have a6px inset on either side. No overflow or negative margins.
- Filled document/people/calendar/navigation/message/video/training/shield icons
  are shared via existing project icon tokens. Dashboard icons use the same masks.
- Interactive buttons/cards use consistent amber hover and keyboard-focus glow.
- Moving amber edge uses Enterprise-marked nav controls and AI hub launch cards
  only. Atlas circle is animated only in Enterprise. Reduced motion disables it.
- Enterprise grouping, badges, actual entitlements and roles remain unchanged.

Validation: changed organization-hub.js syntax and git diff --check pass. Browser
rendered black cards, white filled icons and focus glow. Core member check found
no Enterprise AI cards/badges or My jobs; Enterprise admin restored for review.
No cloud/provider/backend suites run for this reversible visual refinement.

Preview: http://127.0.0.1:8083/__simulator. Local-only, not deployed. Weather
configuration unchanged. Bronze menu experiment archived with earlier themes.
