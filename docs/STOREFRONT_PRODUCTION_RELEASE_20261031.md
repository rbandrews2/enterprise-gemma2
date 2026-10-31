# Storefront production release — 2026-10-31

Published the user-authorized Desktop storefront update to https://workzoneos.org/ through the existing Netlify Drop project zingy-snickerdoodle-799c2b.

- Published deploy: 6ae5b9b872dcf2ea3fa1adc7 (Netlify UI confirmed Currently published).
- Source: storefront update in commit 158bea6.
- Artifact: Desktop/GemmaV2_WZOS_2.0_Files/wzos-storefront-draft/netlify-release.zip.
- Updated index.html, checkout.html, catalog.js, sales.js and checkout.js; preserved existing privacy, terms and legacy return pages and their assets.
- HTTP checks: index, catalog, sales, checkout JS, privacy and terms matched packaged hashes. Checkout HTML differs only in Netlify-normalized home links (index.html to /); line comparison verified.
- Browser Core review: $59/month, $99 setup, $158 first subtotal; handoff preserved offer=core and seats=12.
- Browser Enterprise review: 25 seats, $249/month, $999 setup, $1,248 first subtotal; handoff preserved offer=enterprise and seats=25.
- Both handoffs reached app.workzoneos.org. No payment or customer record was created during this release check.
- Screenshot: storefront-production-20261031.png.

The WZOS backend invoice repair was deployed separately; see CHECKOUT_PRODUCTION_RELEASE_20261031.md. Stand-alone Time Tracker automatic activation remains deferred and is not established by this storefront release. Legacy return pages were preserved rather than treated as a new activation flow.
