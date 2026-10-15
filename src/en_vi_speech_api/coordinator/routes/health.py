from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from en_vi_speech_api.errors import ApiError


class ReadinessClient(Protocol):
    async def ready(self) -> dict[str, object]: ...


async def _worker_state(client: ReadinessClient) -> dict[str, object]:
    try:
        payload = await client.ready()
        return {"ready": bool(payload.get("ready", False)), "details": payload}
    except ApiError as exc:
        return {"ready": False, "error": {"code": exc.code, "message": exc.message}}


def create_health_router(
    translation_client: ReadinessClient,
    speech_client: ReadinessClient,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "alive"}

    @router.get("/health/ready")
    async def ready():
        translation = await _worker_state(translation_client)
        speech = await _worker_state(speech_client)
        workers = {"translation": translation, "speech": speech}
        is_ready = bool(translation["ready"] and speech["ready"])
        payload = {"ready": is_ready, "workers": workers}
        if is_ready:
            return payload
        return JSONResponse(status_code=503, content=payload)

    return router
