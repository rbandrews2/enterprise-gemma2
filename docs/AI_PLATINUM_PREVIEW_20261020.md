# Enterprise AI Theme 2 - Reflective Silver and Platinum

Local-only preview at http://127.0.0.1:8083/__simulator.

- Smart Field Voice and Work Zone Guardian use 1px silver borders, metallic
  gradients, gray text that transitions to white, and restrained white glow.
- Filled monochrome microphone/shield icons; badges align beneath labels.
- Enterprise floating Atlas ring uses the same silver treatment.
- Core ordinary assistant, amber utility controls, feature gates and weather
  configuration unchanged. This styling is not a listening/availability signal.
- Reduced-motion preference disables transitions.

Source: workspace-layout.css, with label-only changes in field-voice.js and
ask-atlas.js. Cyan comparison saved at design/theme-previews/enterprise-ai-cyan.css.

Validation: JS syntax and git diff checks pass. Local simulator refreshed and
rendered silver cards with updated labels; mobile icon/label wrapping corrected.
No backend/provider test suites or cloud builds needed for this reversible theme.
Not deployed; awaiting user's theme choice. Launcher PID9668; ignored log files
.local-data/mobile-simulator/platinum-preview.*.log.

Superseded locally by Midnight Amber; platinum CSS archived in
design/theme-previews/enterprise-ai-platinum.css, not auto-loaded.
