"""Separate verified-account workspace factory. Never changes the V1/staging factory."""
import os
from services.workspace_preview.app import create_app
from services.workspace_preview.files import GoogleFiles


def application():
    return create_app(account_workspace=True, file_store=GoogleFiles(os.environ['WZOS_FILES_BUCKET']))
