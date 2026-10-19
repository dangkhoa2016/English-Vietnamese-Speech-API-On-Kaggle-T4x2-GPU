from __future__ import annotations

from pathlib import Path
from typing import Annotated, Protocol

from fastapi import APIRouter, File, Form, Request, UploadFile

from en_vi_speech_api.config import Settings
from en_vi_speech_api.coordinator.audio import normalize_for_asr
from en_vi_speech_api.coordinator.limits import request_temp_directory, validate_audio_upload
from en_vi_speech_api.errors import ApiError


class SpeechTranscriptionClient(Protocol):
    async def transcribe(self, wav_path: Path, *, language: str) -> dict[str, object]: ...


def create_transcriptions_router(
    speech_client: SpeechTranscriptionClient,
    settings: Settings,
    *,
    request_temp_base: Path | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.post("/v1/audio/transcriptions")
    async def transcribe(
        request: Request,
        file: Annotated[UploadFile, File()],
        language: Annotated[str, Form()] = "en",
    ) -> dict[str, object]:
        if language not in {"en", "vi"}:
            raise ApiError("unsupported_language", "Transcription language must be en or vi.", 400)
        with request_temp_directory(base_dir=request_temp_base) as request_dir:
            validated = await validate_audio_upload(
                file,
                request_dir,
                max_bytes=settings.max_audio_upload_bytes,
                max_duration_s=settings.max_audio_duration_s,
            )
            normalized = normalize_for_asr(validated.path, output_dir=request_dir / "normalized")
            result = await speech_client.transcribe(normalized.path, language=language)
            return {
                **result,
                "normalized_audio_duration_s": normalized.duration_s,
                "request_id": request.state.request_id,
            }

    return router
