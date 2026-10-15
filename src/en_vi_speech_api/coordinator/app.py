from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from en_vi_speech_api.config import Settings
from en_vi_speech_api.coordinator.admission import AdmissionController
from en_vi_speech_api.coordinator.auth import authorization_required, load_or_create_api_key
from en_vi_speech_api.coordinator.routes.health import create_health_router
from en_vi_speech_api.coordinator.routes.speech import create_speech_router
from en_vi_speech_api.coordinator.routes.transcriptions import create_transcriptions_router
from en_vi_speech_api.coordinator.routes.translate_and_speak import (
    create_translate_and_speak_router,
)
from en_vi_speech_api.coordinator.worker_client import WorkerClient
from en_vi_speech_api.errors import ApiError


def _error_response(exc: ApiError, request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response(request_id),
        headers={"X-Request-ID": request_id},
    )


def create_app(
    *,
    speech_client=None,
    translation_client=None,
    settings: Settings | None = None,
    request_temp_base: Path | None = None,
    runtime_dir: Path | None = None,
    admission: AdmissionController | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.load()
    resolved_speech_client = speech_client or WorkerClient(
        f"http://127.0.0.1:{resolved_settings.speech_worker_port}",
        timeout_s=resolved_settings.worker_request_timeout_s,
    )
    resolved_translation_client = translation_client or WorkerClient(
        f"http://127.0.0.1:{resolved_settings.translation_worker_port}",
        timeout_s=resolved_settings.worker_request_timeout_s,
    )
    resolved_runtime_dir = runtime_dir or Path("runtime")
    api_key = (
        load_or_create_api_key(resolved_runtime_dir / "api_key.txt")
        if resolved_settings.api_auth_required
        else None
    )
    resolved_admission = admission or AdmissionController(
        max_inflight=resolved_settings.public_max_inflight,
        max_pending=resolved_settings.public_max_pending,
        wait_timeout_s=resolved_settings.public_request_timeout_s,
    )
    app = FastAPI(title="English-Vietnamese Speech API", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def public_guards(request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        lease = None
        try:
            if api_key is not None and request.url.path != "/health/live":
                authorization_required(request, api_key)
            if request.url.path.startswith("/v1/"):
                lease = await resolved_admission.acquire()
            response = await call_next(request)
        except ApiError as exc:
            response = _error_response(exc, request_id)
        finally:
            if lease is not None:
                await lease.release()
        response.headers.setdefault("X-Request-ID", request_id)
        return response

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid4()))
        return _error_response(exc, request_id)

    app.include_router(create_health_router(resolved_translation_client, resolved_speech_client))
    app.include_router(
        create_transcriptions_router(
            resolved_speech_client,
            resolved_settings,
            request_temp_base=request_temp_base,
        )
    )
    app.include_router(create_speech_router(resolved_speech_client, resolved_settings))
    app.include_router(
        create_translate_and_speak_router(
            resolved_speech_client,
            resolved_translation_client,
            resolved_settings,
            request_temp_base=request_temp_base,
        )
    )
    return app


app = create_app()
