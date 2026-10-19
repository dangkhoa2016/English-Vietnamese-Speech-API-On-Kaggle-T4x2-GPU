from __future__ import annotations

import os
from dataclasses import dataclass


class Routes:
    TRANSCRIPTIONS = "/v1/audio/transcriptions"
    SPEECH = "/v1/audio/speech"
    TRANSLATE_AND_SPEAK = "/v1/audio/translate-and-speak"

    TRANSLATION_HEALTH = "/internal/health"
    TRANSLATION_READY = "/internal/ready"
    TRANSLATION_TRANSLATE = "/internal/translate"

    SPEECH_HEALTH = "/internal/health"
    SPEECH_READY = "/internal/ready"
    SPEECH_TRANSCRIBE = "/internal/transcribe"
    SPEECH_SPEAK = "/internal/speak"


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    value = default if raw is None else int(raw)
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


@dataclass(frozen=True, slots=True)
class Settings:
    coordinator_port: int
    translation_worker_port: int
    speech_worker_port: int
    max_audio_upload_bytes: int
    max_text_upload_bytes: int
    max_audio_duration_s: int
    public_request_timeout_s: int
    worker_request_timeout_s: int
    speech_gpu_concurrency: int
    translation_concurrency: int
    public_max_inflight: int
    public_max_pending: int
    enable_cloudflare_tunnel: bool
    api_auth_required: bool

    @classmethod
    def load(cls) -> Settings:
        settings = cls(
            coordinator_port=_int_env("COORDINATOR_PORT", 8090),
            translation_worker_port=_int_env("TRANSLATION_WORKER_PORT", 8091),
            speech_worker_port=_int_env("SPEECH_WORKER_PORT", 8092),
            max_audio_upload_bytes=_int_env("MAX_AUDIO_UPLOAD_BYTES", 25 * 1024 * 1024),
            max_text_upload_bytes=_int_env("MAX_TEXT_UPLOAD_BYTES", 100 * 1024),
            max_audio_duration_s=_int_env("MAX_AUDIO_DURATION_S", 1800),
            public_request_timeout_s=_int_env("PUBLIC_REQUEST_TIMEOUT_S", 600),
            worker_request_timeout_s=_int_env("WORKER_REQUEST_TIMEOUT_S", 540),
            speech_gpu_concurrency=_int_env("SPEECH_GPU_CONCURRENCY", 1),
            translation_concurrency=_int_env("TRANSLATION_CONCURRENCY", 1),
            public_max_inflight=_int_env("PUBLIC_MAX_INFLIGHT", 2),
            public_max_pending=_int_env("PUBLIC_MAX_PENDING", 2),
            enable_cloudflare_tunnel=_bool_env("ENABLE_CLOUDFLARE_TUNNEL", False),
            api_auth_required=_bool_env("API_AUTH_REQUIRED", False),
        )
        ports = {
            settings.coordinator_port,
            settings.translation_worker_port,
            settings.speech_worker_port,
        }
        if len(ports) != 3:
            raise ValueError("coordinator and worker ports must be unique")
        return settings
