# Enterprise AI cyan styling preview

Local preview only; no live deployment requested for this styling experiment.

User selected the High-Viz Safety Cyan direction. Scope is limited to Smart Field
Voice, Ask Atlas / Work Zone Guardian and the Enterprise Atlas floating button.
Charcoal glass, existing module layouts and standard amber controls are retained.

Implementation: scoped additive rules in workspace-layout.css; cyan #00E5FF left
edge and restrained gradient/glow, ENTERPRISE AI pill, visible focus treatment,
cyan interaction glow, and a cyan ring around the existing floating Atlas image.
No pulsing animation. Reduced-motion preferences disable the added transitions.
The selectors require Enterprise launch controls, so Core's ordinary Atlas helper
does not receive the premium styling. This is visual branding, not a listening or
availability indicator. Feature activation, permissions and weather are unchanged.

Preview: http://127.0.0.1:8083/__simulator. Select an Enterprise identity. The owned
loopback server was started hidden (PID20008); stdout/stderr under the ignored
.local-data/mobile-simulator/cyan-preview.*.log paths.

Checks: simulator and stylesheet return200; expected cyan/badge rules served;
balanced CSS blocks and git diff --check pass. Browser control timed out/reset,
so screenshot, mobile/desktop visual acceptance and live acceptance are NOT claimed.
No Python/PostgreSQL/provider suites were rerun for this reversible CSS-only change.

Superseded locally by Theme 2 (silver/platinum). Original cyan rules are retained
in design/theme-previews/enterprise-ai-cyan.css for comparison; not auto-loaded.
