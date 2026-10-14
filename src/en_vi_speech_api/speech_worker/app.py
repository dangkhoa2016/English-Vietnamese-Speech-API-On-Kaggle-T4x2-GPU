from __future__ import annotations

import os
from typing import Protocol

from fastapi import FastAPI, HTTPException, status

from en_vi_speech_api.speech_worker.models import StubSpeechModels


class SpeechModelState(Protocol):
    ready: bool
    load_metadata: dict[str, object]


def create_app(models: SpeechModelState) -> FastAPI:
    app = FastAPI(title="Speech Worker", docs_url=None, redoc_url=None)

    @app.get("/internal/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "worker": "speech"}

    @app.get("/internal/ready")
    def ready() -> dict[str, object]:
        if not models.ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "worker_unavailable", "message": "Speech worker is not ready."},
            )
        return {
            "ready": True,
            "worker": "speech",
            "metadata": dict(models.load_metadata),
        }

    return app


def _default_models() -> SpeechModelState:
    if os.getenv("SPEECH_BACKEND", "stub").strip().lower() != "real":
        return StubSpeechModels()

    from en_vi_speech_api.speech_worker.models import build_real_speech_models

    models = build_real_speech_models()
    models.load()
    return models


app = create_app(_default_models())
