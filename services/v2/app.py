"""Separate loopback-only V2 scaffold; never imports the V1 application."""

import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from services.v2.inference import InferenceProvider, LocalProvider
from services.v2.settings import Settings
from shared.contracts import DraftRequest, DraftResponse
from services.v2.knowledge.api import router
from services.v2.knowledge.store import Store

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, provider: InferenceProvider | None = None,
               knowledge_store: Store | None = None):
    settings = settings or Settings.from_env()
    provider = provider or LocalProvider()
    app = FastAPI(title="WZOS Gemma V2 — local scaffold", version="0.1.0")
    app.include_router(router(knowledge_store or Store()))

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        if not request.client or request.client.host not in {"127.0.0.1", "::1", "testclient"}:
            return JSONResponse(status_code=403, content={"error": "local_only"})
        return await call_next(request)

    @app.get("/health/live")
    async def live():
        return {"status": "alive"}

    @app.get("/health/ready")
    async def ready():
        return {
            "status": "ready_for_local_preview",
            "environment": settings.environment,
            "backend": settings.backend,
            "production_ready": False,
            "cloud_dependencies_checked": False,
        }

    @app.post("/v2/drafts/preview", response_model=DraftResponse)
    async def preview(request: DraftRequest):
        try:
            return DraftResponse.model_validate(await provider.preview(request))
        except Exception:
            correlation_id = uuid4().hex
            logger.error("Preview failed; correlation_id=%s", correlation_id)
            return JSONResponse(
                status_code=502,
                content={"error": "preview_unavailable", "correlation_id": correlation_id},
            )

    return app
