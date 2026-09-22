"""Private Cloud Run review environment; explicitly ephemeral synthetic data."""
import os
from pathlib import Path
from services.workspace_preview.app import create_app
from services.v2.knowledge.store import Store

class UnavailableCloudModel:
    async def ready(self): return False
    async def reply(self, payload, context):
        from services.workspace_preview.intelligence import ModelUnavailable
        raise ModelUnavailable("Atlas conversation is not connected in cloud staging. Quick guides remain available.")

def app_factory():
    return create_app(Path("/tmp/wzos-staging/orders.sqlite"),
                      Store(Path("/tmp/wzos-staging/sources")),
                      UnavailableCloudModel(), private_staging=True)
