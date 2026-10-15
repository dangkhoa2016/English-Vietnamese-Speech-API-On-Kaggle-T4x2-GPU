from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Protocol

from fastapi import APIRouter, File, Request, Response, UploadFile

from en_vi_speech_api.config import Settings
from en_vi_speech_api.coordinator.artifacts import build_pipeline_zip
from en_vi_speech_api.coordinator.audio import NormalizedAudio, normalize_for_asr
from en_vi_speech_api.coordinator.limits import request_temp_directory, validate_audio_upload
from en_vi_speech_api.coordinator.worker_client import WorkerAudio


class SpeechPipelineClient(Protocol):
    async def transcribe(self, wav_path: Path, *, language: str) -> dict[str, object]: ...

    async def speak(self, text: str, *, language: str) -> WorkerAudio: ...


class TranslationPipelineClient(Protocol):
    async def translate(
        self, text: str, *, source_language: str, target_language: str
    ) -> dict[str, object]: ...


Normalizer = Callable[[Path], NormalizedAudio]
Packager = Callable[..., bytes]


async def run_pipeline(
    input_path: Path,
    *,
    request_dir: Path,
    request_id: str,
    speech_client: SpeechPipelineClient,
    translation_client: TranslationPipelineClient,
    normalizer: Callable[..., NormalizedAudio] = normalize_for_asr,
    packager: Packager = build_pipeline_zip,
) -> bytes:
    total_started = time.perf_counter()
    normalized = normalizer(input_path, output_dir=request_dir / "normalized")
    transcription = await speech_client.transcribe(normalized.path, language="en")
    transcript = str(transcription.get("text", "")).strip()
    translation = await translation_client.translate(
        transcript,
        source_language="en",
        target_language="vi",
    )
    translated_text = str(translation.get("text", "")).strip()
    speech = await speech_client.speak(translated_text, language="vi")
    total_ms = (time.perf_counter() - total_started) * 1000
    metadata = {
        "request_id": request_id,
        "source_language": "en",
        "target_language": "vi",
        "normalized_audio_duration_s": normalized.duration_s,
        "models": {
            "asr": transcription.get("model"),
            "translation": translation.get("model"),
            "tts": speech.model,
        },
        "timings_ms": {
            "asr": transcription.get("inference_ms"),
            "translation": translation.get("inference_ms"),
            "tts": speech.inference_ms,
            "total": total_ms,
        },
        "output_audio": {
            "sample_rate_hz": speech.sample_rate_hz,
            "duration_s": speech.duration_s,
        },
    }
    return packager(
        transcript=transcript,
        translation=translated_text,
        speech_wav=speech.content,
        metadata=metadata,
    )


def create_translate_and_speak_router(
    speech_client: SpeechPipelineClient,
    translation_client: TranslationPipelineClient,
    settings: Settings,
    *,
    request_temp_base: Path | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.post("/v1/audio/translate-and-speak")
    async def translate_and_speak(
        request: Request,
        file: Annotated[UploadFile, File()],
    ) -> Response:
        with request_temp_directory(base_dir=request_temp_base) as request_dir:
            validated = await validate_audio_upload(
                file,
                request_dir,
                max_bytes=settings.max_audio_upload_bytes,
                max_duration_s=settings.max_audio_duration_s,
            )
            artifact = await run_pipeline(
                validated.path,
                request_dir=request_dir,
                request_id=request.state.request_id,
                speech_client=speech_client,
                translation_client=translation_client,
            )
        return Response(
            content=artifact,
            media_type="application/zip",
            headers={
                "X-Request-ID": request.state.request_id,
                "Content-Disposition": 'attachment; filename="translate-and-speak.zip"',
            },
        )

    return router
