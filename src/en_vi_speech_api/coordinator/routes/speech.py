from __future__ import annotations

from typing import Annotated, Protocol

from fastapi import APIRouter, File, Form, Request, Response, UploadFile

from en_vi_speech_api.config import Settings
from en_vi_speech_api.coordinator.limits import read_text_upload
from en_vi_speech_api.coordinator.worker_client import WorkerAudio
from en_vi_speech_api.errors import ApiError


class SpeechSynthesisClient(Protocol):
    async def speak(self, text: str, *, language: str) -> WorkerAudio: ...


def create_speech_router(speech_client: SpeechSynthesisClient, settings: Settings) -> APIRouter:
    router = APIRouter()

    @router.post("/v1/audio/speech")
    async def speak(
        request: Request,
        file: Annotated[UploadFile, File()],
        language: Annotated[str, Form()],
    ) -> Response:
        if language not in {"en", "vi"}:
            raise ApiError("unsupported_language", "Speech language must be en or vi.", 400)
        text = await read_text_upload(file, max_bytes=settings.max_text_upload_bytes)
        audio = await speech_client.speak(text, language=language)
        return Response(
            content=audio.content,
            media_type=audio.media_type,
            headers={
                "X-Request-ID": request.state.request_id,
                "X-Model": audio.model,
                "X-Inference-Ms": f"{audio.inference_ms:.3f}",
                "X-Audio-Sample-Rate": str(audio.sample_rate_hz),
                "X-Audio-Duration-S": f"{audio.duration_s:.6f}",
                "X-Speech-Language": audio.language,
            },
        )

    return router
