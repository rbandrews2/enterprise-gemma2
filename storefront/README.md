# Local activation integration (October 31, 2026)

Core/Enterprise now route through authenticated WZOS checkout; corresponding app changes must be deployed first. Monthly/annual selection and seats transfer automatically. Verified payment fills the activation code inside WZOS; no activation email is sent. Stand-alone Tracker link remains separate and not activation-integrated. No live deployment or payment test performed.

Prior configuration notes below are historical for Core/Enterprise Payment Links.

# WZOS storefront and Stripe configuration

Updated October 31, 2026. The local sales page and order review link to five active Stripe Payment Links in Molecular Project Development LLC's live account. The supplied original HTML and Luxury Choice Render service remain unchanged. No website deployment or customer charge was performed.

## Prices

| Edition | Monthly base | Annual base | Included users | Additional users | Setup |
| --- | --- | --- | --- | --- | --- |
| Core | $59 | $600 | 15 including admins | $3/month or $36/year | $99 once |
| Enterprise | $249 | $2,688 | 25 including admins | $7/month or $84/year | $999 once |
| Time Tracker | $9.99 | Not offered | 1 | $4/month | None added to the link |

The owner approved annual add-ons billed annually at the monthly-equivalent rate. All standard offerings stop at 30 users per organization. Above 30 routes to Enterprise with custom pricing. Established Core customers' one-time $20 Enterprise upgrade credit is noted but not automatically applied by these new-organization links.

## Created in Stripe

| New price | Stripe price ID |
| --- | --- |
| Core $600/year base | price_1UWV4NCTCYI3n5kZGFvSr5fT |
| Enterprise $2,688/year base | price_1UWV5YCTCYI3n5kZ3Gv5BSo3 |
| Time Tracker $4/month extra user | price_1UWV6ZCTCYI3n5kZykkJ6tjJ |
| Core $36/year extra user | price_1UWV8JCTCYI3n5kZ6ZIIozro |
| Enterprise $84/year extra user | price_1UWV9ACTCYI3n5kZLeMb3f0Y |

Product and original monthly/setup price IDs are in catalog.js. Payment-link URLs are in catalog.js and stripe-links.json:

- Core monthly: https://checkout.superiorllc.org/b/9B6bJ09xB7ik8bg5Ls2cg0c
- Core annual: https://checkout.superiorllc.org/b/bJefZgdNR324dvA4Ho2cg0d
- Enterprise monthly: https://checkout.superiorllc.org/b/5kQ00i6lpauw8bgddU2cg0e
- Enterprise annual: https://checkout.superiorllc.org/b/7sYaEW4dh9qsgHM6Pw2cg0f
- Tracker monthly: https://checkout.superiorllc.org/b/28E14m7ptfOQgHM5Ls2cg0g

These use the account's existing Stripe custom domain and existing merchant branding. Customer-facing Core checkout was verified to show WZOS and Molecular Project Development LLC. Global account branding and the other storefront were not changed.

## Quantity behavior

Each link fixes organization base quantity at 1. Core/Enterprise links also fix setup quantity at 1. Only additional-user quantity is adjustable: 0–15 Core, 0–5 Enterprise, 0–29 Tracker. Stripe requires the initial configured line quantity to be at least 1, so all links initially show one extra user. The HTML prominently tells the customer the exact extra-user count to set in Stripe, including removing the extra-user line when zero are needed. The selected HTML quantity is an estimate and is not automatically transferred to Stripe.

For exact quantity transfer without a second customer selection, replace Payment Links with a server-side Checkout Sessions endpoint that uses allowlisted price IDs and quantities. Do not accept client-supplied amounts.

## Verification

- Created and verified all five new prices and all five Payment Links through the signed-in Chrome dashboard after the Stripe connector reported reauthentication required.
- Verified link line items, fixed base/setup quantities, adjustable bounds and business-name collection.
- Opened the real Core checkout without entering payment/customer information. Removed the extra-user cart line and verified $158 initially, then $59/month. No purchase was submitted.
- Programmatic checks passed for every link route, annual/monthly totals, setup fees, included/additional-user calculations, annual Tracker fallback, custom Enterprise routing, URL allowlist and user-requested option labels. Local HTML browser QA was unavailable after file navigation was blocked.
- Removed Operations Plus and the Tidewater Field Team reference. Added Smart Field Voice, Ask Atlas -- Work Zone Guardian, Video Training and Messaging to the hero option tiles.

## Remaining launch work

- Confirm Stripe Tax registrations and tax treatment. Automatic tax is OFF on these new links because active registrations were not verified. Product tax behavior is exclusive; the HTML does not claim tax collection is enabled.
- Verify signed, durably idempotent payment/subscription webhooks and access provisioning, including asynchronous payment outcomes, renewals, failures, cancellation, disputes/refunds and fraud signals. These payment links do not establish automatic app activation. Activation-delivery claims were softened in the local page.
- Confirm sales/support destinations, app URLs and business privacy/terms/refund URLs; the source's original contact/app destinations remain for review. Custom Enterprise routes to the local contact section and sends no inquiry automatically.
- Review remaining product/integration/security claims before publication, including SOC 2 readiness, ISO control mapping, SSO and integration availability.
- Stripe displays an account-information task needed to keep payouts enabled; account remediation was not inspected or changed.
- Run a complete sandbox purchase/renewal/activation test before describing the whole subscription integration as production-verified. Choose a separate WZOS hosting destination when deployment is requested.
