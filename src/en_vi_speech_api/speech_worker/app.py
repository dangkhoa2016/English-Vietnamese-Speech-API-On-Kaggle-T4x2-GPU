from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Annotated, Any, Protocol

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status

from en_vi_speech_api.speech_worker.models import StubSpeechModels
from en_vi_speech_api.speech_worker.schemas import TranscriptionResponse


class SpeechModelState(Protocol):
    ready: bool
    load_metadata: dict[str, object]


class ASRState(Protocol):
    async def transcribe(self, wav_path: Path, language: str = "en") -> Any: ...


def create_app(models: SpeechModelState, *, asr_service: ASRState | None = None) -> FastAPI:
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

    @app.post("/internal/transcribe", response_model=TranscriptionResponse)
    async def transcribe(
        file: Annotated[UploadFile, File()],
        language: Annotated[str, Form()] = "en",
    ) -> TranscriptionResponse:
        if asr_service is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "worker_unavailable", "message": "ASR service is not ready."},
            )
        suffix = Path(file.filename or "audio.wav").suffix or ".wav"
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(prefix="asr-", suffix=suffix, delete=False) as handle:
                temp_path = Path(handle.name)
                while chunk := await file.read(1024 * 1024):
                    handle.write(chunk)
            result = await asr_service.transcribe(temp_path, language=language)
            return TranscriptionResponse(
                text=result.text,
                language=result.language,
                chunk_count=result.chunk_count,
                inference_ms=result.inference_ms,
                model=result.model,
            )
        finally:
            await file.close()
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    return app


def _default_app() -> FastAPI:
    if os.getenv("SPEECH_BACKEND", "stub").strip().lower() != "real":
        return create_app(StubSpeechModels())

    from en_vi_speech_api.speech_worker.asr import (
        ASRService,
        build_whisper_infer,
        load_whisper_processor,
    )
    from en_vi_speech_api.speech_worker.models import (
        WHISPER_MODEL_BASE,
        build_real_speech_models,
        discover_versioned_model,
    )

    models = build_real_speech_models()
    models.load()
    whisper_path = discover_versioned_model(
        WHISPER_MODEL_BASE,
        required=("config.json", "model.safetensors", "preprocessor_config.json"),
    )
    processor = load_whisper_processor(whisper_path)
    asr_service = ASRService(models=models, infer=build_whisper_infer(models, processor))
    return create_app(models, asr_service=asr_service)


app = _default_app()
