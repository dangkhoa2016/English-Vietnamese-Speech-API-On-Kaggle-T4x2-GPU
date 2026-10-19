from __future__ import annotations

import os
import time
from typing import Protocol

from fastapi import FastAPI, HTTPException, status

from en_vi_speech_api.translation_worker.schemas import TranslationRequest, TranslationResponse

MAX_TRANSLATION_TEXT_BYTES = 100 * 1024


class TranslationBackend(Protocol):
    ready: bool

    def translate(self, text: str, source_language: str, target_language: str) -> str: ...


class StubTranslator:
    ready = True

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        return text


def create_app(translator: TranslationBackend) -> FastAPI:
    app = FastAPI(title="Translation Worker", docs_url=None, redoc_url=None)

    @app.get("/internal/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "worker": "translation"}

    @app.get("/internal/ready")
    def ready() -> dict[str, object]:
        if not translator.ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "worker_unavailable",
                    "message": "Translation worker is not ready.",
                },
            )
        payload: dict[str, object] = {"ready": True, "worker": "translation"}
        model_id = getattr(translator, "model_id", None)
        metadata = getattr(translator, "load_metadata", None)
        if model_id:
            payload["model"] = model_id
        if isinstance(metadata, dict) and metadata:
            payload["metadata"] = {
                key: value for key, value in metadata.items() if key not in {"model_path", "path"}
            }
        return payload

    @app.post("/internal/translate", response_model=TranslationResponse)
    def translate(request: TranslationRequest) -> TranslationResponse:
        if not translator.ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "worker_unavailable",
                    "message": "Translation worker is not ready.",
                },
            )
        if (request.source_language, request.target_language) not in {("en", "vi"), ("vi", "en")}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "unsupported_language_pair",
                    "message": "Translation supports en -> vi and vi -> en.",
                },
            )
        if not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "empty_text", "message": "Translation text must not be empty."},
            )
        if len(request.text.encode("utf-8")) > MAX_TRANSLATION_TEXT_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail={"code": "text_too_large", "message": "Translation text exceeds 100 KiB."},
            )

        started = time.perf_counter()
        try:
            result = translator.translate(
                request.text,
                source_language=request.source_language,
                target_language=request.target_language,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "inference_failed", "message": "Translation inference failed."},
            ) from exc
        return TranslationResponse(
            text=result,
            source_language=request.source_language,
            target_language=request.target_language,
            model=getattr(translator, "model_id", None),
            inference_ms=(time.perf_counter() - started) * 1000,
        )

    return app


def _default_backend() -> TranslationBackend:
    if os.getenv("TRANSLATION_BACKEND", "stub").strip().lower() != "real":
        return StubTranslator()

    from en_vi_speech_api.translation_worker.model import TranslateGemmaTranslator

    translator = TranslateGemmaTranslator(
        model_path=os.getenv(
            "TRANSLATEGEMMA_MODEL_PATH",
            "/kaggle/input/models/keras/translategemma/keras/translategemma_4b_it/1",
        ),
        dtype=os.getenv("TRANSLATEGEMMA_DTYPE", "bfloat16"),
    )
    translator.load()
    return translator


app = create_app(_default_backend())
