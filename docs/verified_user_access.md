# Verified User Access

The Cloud Run service is private. A normal browser visit to the direct Cloud Run URL returns `403` because browsers do not automatically send Cloud Run identity tokens.

For a browser-friendly employee login flow, put the service behind Identity-Aware Proxy (IAP):

1. Create an external HTTPS load balancer with a serverless NEG pointing to `gemma-assistant-api`.
2. Enable IAP on the backend service.
3. Allow `workzoneos.org` users in IAP.
4. Grant Cloud Run Invoker to the IAP service agent:

```bash
bash scripts/restrict_workzoneos_access.sh
```

5. Point `app.workzoneos.org` at the load balancer IP with an `A` record.
6. Wait for the Google-managed certificate to become `ACTIVE` before testing the browser login flow.

The app validates IAP's verified identity header:

- `AUTH_PROVIDER=iap`
- `ALLOWED_EMAIL_DOMAIN=workzoneos.org`

Do not rely on a typed email field or a client-side flag for authorization.
