# Atlas associate trial — November 7, 2026

User authorized Atlas operation for a 2–3 day professional associate trial and explicitly prioritized availability over cost. Associates will join the existing Molecular organization. This supersedes older no-keep-warm pilot constraints for this trial.

Fresh Cloud Shell authentication verified admin@workzoneos.org in enterprise-gemma2. Existing private wzos-atlas-inference in us-central1 retains only WZOS runtime service-account invocation. Existing model: Gemma 4 31B, one GPU, 20 CPU, 80 GiB, pinned model revision wzos-atlas-inference-00001-4gd.

Requested service minimum changed from zero to one, maximum remains one, to avoid repeated cold startup. This setting remains in place until explicitly reverted; review at trial end (November 10). Return to normal idle scaling using gcloud run services update wzos-atlas-inference --project=enterprise-gemma2 --region=us-central1 --min=0 --max=1.

General conversation switch WZOS_ATLAS_VLLM_ENABLED changed from 0 to 1 on the existing application image b85d385dd1dce8cd1debe3fd3aab25ef922794bdd517ea55294c9160778ced93. New revision wzos-v2-accounts-00073-h7m. Traffic activation and live response validation pending at this checkpoint. Prior traffic revision wzos-v2-accounts-checkout-158bea6 retained.

Ask Atlas DOT and Field Voice switches were already enabled. DOT remains restricted to the existing pilot organization; no organization access was expanded. No new IAM role, public model access, customer send, or database migration.

Cloud logs: /tmp/atlas-trial-warm.log, /tmp/atlas-trial-app.log, /tmp/atlas-trial-traffic.log. Model startup observed in Google logs; not yet claimed as a passing response.

## Verified activation
- Model service Ready=True; min=1/max=1. Existing private invoker binding unchanged.
- App revision wzos-v2-accounts-00073-h7m receives 100% traffic, Ready=True. Independent config comparison: same container image; only WZOS_ATLAS_VLLM_ENABLED changed.
- Browser PWA update offered and installed successfully; organization selection restored the workspace.
- Live floating Atlas conversational request returned an AI-generated answer. Model log confirmed POST /v1/chat/completions HTTP200. No action/customer notification was performed.
- Generic residential-street Ask Atlas questions returned a clarification request, including after a more specific follow-up; do not claim this as successful model reasoning. A fresh precise taper question is being checked separately.
- Dedicated Ask Atlas precise taper question returned a conversational answer with two source citations and a discrepancy notice. This verifies live answer delivery, not independent engineering certification. Screenshot: atlas-associate-trial-20261107.png.
- Trial operational checks complete; no unchanged full-suite rerun. Broader-question clarification behavior remains a follow-up UX item.
