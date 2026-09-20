# Local V2 service

From the repository root, using Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-v2.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m uvicorn services.v2.app:create_app --factory --host 127.0.0.1 --port 8081 --no-proxy-headers
```

Open http://127.0.0.1:8081/docs to try the preview. Use invented demonstration inputs, not sensitive customer data. The preview does not save records, call a model, retrieve agency guidance, generate a PDF, or send email.

`POST /v2/intake/assess` now supports address/coordinate intake, requested outputs, a proactive JSA recommendation, and missing-context prompts. See [customer workflow](../../docs/CUSTOMER_WORKFLOW.md). These are product intake rules; they do not establish legal requirements or produce sign/flagger placements.

`POST /v2/planning/references` accepts the same intake and returns that assessment plus job-related source passages and explicit coverage gaps. See [planning reference API](../../docs/PLANNING_REFERENCES.md). The source library must be ingested and indexed first; missing indexes produce a partial response with the intake assessment preserved.

Optional environment settings: `WZOS_ENVIRONMENT=local` and `WZOS_INFERENCE_BACKEND=deterministic_local`. Other values fail startup. The V1 requirements, main.py, and deployment scripts are separate and unchanged.

Visit `/v2/workspace` for the [local annotation editor](../../docs/LOCAL_WORKSPACE.md). It edits existing project markers with a coordinate preview; Google imagery is not connected.

`POST /v2/imagery/streetview/availability` accepts an address or coordinates. Default Google access is disabled; see the [imagery backend](../../docs/IMAGERY_BACKEND.md) for provider injection, response states and remaining image-display work.

The pinned dependency snapshot includes HTTPX for testing. It reproduces this local milestone; it is not a production dependency approval.

The [local project workspace](../../docs/PROJECT_WORKSPACE.md) adds saved intake, typed evidence references, pending applicability notes, version history, and conflict-safe edits. Use only development data until WZOS identity and organization authorization are implemented.

The [agency reference backend](../../knowledge/README.md) adds catalog browsing and citation search. Its separate operator command must ingest sources before text search is available. Ingestion and search do not alter the draft preview or add model-generated safety guidance.
