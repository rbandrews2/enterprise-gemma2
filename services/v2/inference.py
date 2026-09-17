"""Provider boundary; local implementation intentionally supplies no safety advice."""

from typing import Protocol

from shared.contracts import DraftRequest, DraftResponse


class InferenceProvider(Protocol):
    async def preview(self, request: DraftRequest) -> DraftResponse: ...


class LocalProvider:
    async def preview(self, request: DraftRequest) -> DraftResponse:
        return DraftResponse(
            project_name=request.project_name,
            summary="Local workflow preview only. No model or agency retrieval was called.",
            missing_capabilities=[
                "Verified jurisdiction sources and forms",
                "Verified traffic and speed observations",
                "Real site imagery and reviewed annotations",
                "PDF rendering and durable package storage",
                "WZOS identity, organization authorization, and qualified review",
                "Authorized email delivery",
            ],
        )
