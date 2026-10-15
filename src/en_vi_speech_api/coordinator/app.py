from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from en_vi_speech_api.config import Settings
from en_vi_speech_api.coordinator.routes.speech import create_speech_router
from en_vi_speech_api.coordinator.routes.transcriptions import create_transcriptions_router
from en_vi_speech_api.coordinator.worker_client import WorkerClient
from en_vi_speech_api.errors import ApiError


def create_app(
    *,
    speech_client=None,
    settings: Settings | None = None,
    request_temp_base: Path | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.load()
    resolved_speech_client = speech_client or WorkerClient(
        f"http://127.0.0.1:{resolved_settings.speech_worker_port}",
        timeout_s=resolved_settings.worker_request_timeout_s,
    )
    app = FastAPI(title="English-Vietnamese Speech API", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", request.state.request_id)
        return response

    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid4()))
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_response(request_id),
            headers={"X-Request-ID": request_id},
        )

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "alive"}

    app.include_router(
        create_transcriptions_router(
            resolved_speech_client,
            resolved_settings,
            request_temp_base=request_temp_base,
        )
    )
    app.include_router(create_speech_router(resolved_speech_client, resolved_settings))
    return app


app = create_app()
