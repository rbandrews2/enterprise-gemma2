Local sync status file.

The active local project folder is:
C:\Users\ray\enterprise-gemma2

Use this folder as the Windows working copy for enterprise-gemma2 and Google Cloud deployment work.

Current live Cloud Run sync:
- Project: enterprise-gemma2
- Service: gemma-assistant-api
- Region: us-central1
- Live revision: gemma-assistant-api-00008-njc
- Live image: us-central1-docker.pkg.dev/enterprise-gemma2/enterprise-gemma2/gemma-assistant-api:v17
- Auth mode: IAP with ALLOWED_EMAIL_DOMAIN=workzoneos.org
- Load balancer IP for app.workzoneos.org: 34.111.102.184
- Pending outside this repo: create the app.workzoneos.org A record and wait for the managed certificate to become ACTIVE.

Important:
- Preserve .env.local and never commit real secrets.
- Keep generated caches, backup files, and local archives out of git.
- Use scripts/export_project.py when exporting from another checkout into this folder.
