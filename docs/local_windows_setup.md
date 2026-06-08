# Local Windows Setup

Use `C:\Users\ray\enterprise-gemma2` as the local working copy for this project.

## Export From An Existing Checkout

From Windows PowerShell:

```powershell
python scripts/export_project.py C:\Users\ray\enterprise-gemma2
```

From WSL:

```bash
python scripts/export_project.py /mnt/c/Users/ray/enterprise-gemma2
```

The exporter copies tracked project files, preserves an existing `.env.local`, skips runtime folders, and creates a starter `.env.local` from `.env.example` when one is available.

## Google Cloud Notes

This project is intended to run on Google Cloud products, including Cloud Run and Vertex AI. Keep secrets in Google Secret Manager or local `.env.local`; do not commit real secret values to GitHub.

Suggested local folder layout:

```text
C:\Users\ray\enterprise-gemma2
|-- cloudrun-service.yaml
|-- deploy.sh
|-- Dockerfile
|-- docs\
|-- main.py
|-- scripts\
|-- .env.local
```

Before deploying, confirm the active Google Cloud project, service account permissions, Cloud Run region, and Vertex AI endpoint configuration.
