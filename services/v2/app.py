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
from shared.intake import IntakeRequest, IntakeAssessment
from services.v2.intake import assess
from services.v2.planning import discover
from shared.planning import PlanningReferences
from services.v2.projects import ProjectStore, ProjectMissing, ProjectConflict, project_router
import sqlite3
from services.v2.imagery import StreetViewMetadata, ImageryAvailability
from shared.intake import JobLocation
from pathlib import Path
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, provider: InferenceProvider | None = None,
               knowledge_store: Store | None = None, project_store: ProjectStore | None = None,
               imagery_provider: StreetViewMetadata | None = None):
    settings = settings or Settings.from_env()
    provider = provider or LocalProvider()
    knowledge_store = knowledge_store or Store()
    app = FastAPI(title="WZOS Gemma V2 — local scaffold", version="0.1.0")
    imagery_provider = imagery_provider or StreetViewMetadata()

    @app.get("/v2/workspace", include_in_schema=False)
    def workspace():
        return FileResponse(Path(__file__).with_name("workspace.html"), headers={"Cache-Control": "no-store"})

    @app.get("/v2/workspace.js", include_in_schema=False)
    def workspace_script():
        return FileResponse(Path(__file__).with_name("workspace.js"), media_type="text/javascript")

    @app.post("/v2/imagery/streetview/availability", response_model=ImageryAvailability)
    def imagery_availability(location: JobLocation):
        return imagery_provider.lookup(location)

    app.include_router(router(knowledge_store))
    app.include_router(project_router(project_store or ProjectStore(), knowledge_store))

    @app.exception_handler(ProjectMissing)
    async def missing_project(request, error):
        return JSONResponse(status_code=404, content={"error": "project_or_revision_not_found"})

    @app.exception_handler(ProjectConflict)
    async def changed_project(request, error):
        return JSONResponse(status_code=409, content={"error": str(error)})

    @app.exception_handler(sqlite3.DatabaseError)
    async def unavailable_store(request, error):
        return JSONResponse(status_code=503, content={"error": "local_storage_unavailable"})

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        if not request.client or request.client.host not in {"127.0.0.1", "::1", "testclient"}:
            return JSONResponse(status_code=403, content={"error": "local_only"})
        return await call_next(request)

    @app.get("/health/live")
    async def live():
        return {"status": "alive"}

    @app.post("/v2/intake/assess", response_model=IntakeAssessment)
    async def assess_intake(request: IntakeRequest):
        return assess(request)

    @app.post("/v2/planning/references", response_model=PlanningReferences)
    def planning_references(request: IntakeRequest):
        return discover(request, knowledge_store)

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
