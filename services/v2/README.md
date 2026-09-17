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

Optional environment settings: `WZOS_ENVIRONMENT=local` and `WZOS_INFERENCE_BACKEND=deterministic_local`. Other values fail startup. The V1 requirements, main.py, and deployment scripts are separate and unchanged.

The pinned dependency snapshot includes HTTPX for testing. It reproduces this local milestone; it is not a production dependency approval.

The [agency reference backend](../../knowledge/README.md) adds catalog browsing and citation search. Its separate operator command must ingest sources before text search is available. Ingestion and search do not alter the draft preview or add model-generated safety guidance.
