"""Fail closed until cloud identity and provider adapters exist."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str = "local"
    backend: str = "deterministic_local"

    def __post_init__(self):
        if self.environment != "local" or self.backend != "deterministic_local":
            raise ValueError("Only local execution with deterministic_local is implemented")

    @classmethod
    def from_env(cls):
        return cls(
            environment=os.getenv("WZOS_ENVIRONMENT", "local"),
            backend=os.getenv("WZOS_INFERENCE_BACKEND", "deterministic_local"),
        )
