from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from en_vi_speech_api.errors import ApiError


@dataclass(frozen=True, slots=True)
class WorkerAudio:
    content: bytes
    media_type: str
    model: str
    inference_ms: float
    sample_rate_hz: int
    duration_s: float
    language: str


class WorkerClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_s: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_s),
            transport=transport,
        )

    async def _send(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise ApiError("worker_timeout", "Worker request timed out.", 504) from exc
        except httpx.RequestError as exc:
            raise ApiError("worker_unavailable", "Worker is unavailable.", 503) from exc

        if response.status_code >= 500:
            raise ApiError("worker_unavailable", "Worker is unavailable.", 503)
        if response.status_code >= 400:
            raise ApiError("inference_failed", "Worker rejected the request.", response.status_code)
        return response

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = await self._send(method, path, **kwargs)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ApiError("inference_failed", "Worker returned invalid JSON.", 502) from exc
        if not isinstance(payload, dict):
            raise ApiError("inference_failed", "Worker returned invalid JSON.", 502)
        return payload

    async def health(self) -> dict[str, Any]:
        return await self._request("GET", "/internal/health")

    async def ready(self) -> dict[str, Any]:
        return await self._request("GET", "/internal/ready")

    async def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", path, json=payload)

    async def transcribe(self, wav_path: Path, *, language: str) -> dict[str, Any]:
        with wav_path.open("rb") as handle:
            return await self._request(
                "POST",
                "/internal/transcribe",
                files={"file": (wav_path.name, handle, "audio/wav")},
                data={"language": language},
            )

    async def speak(self, text: str, *, language: str) -> WorkerAudio:
        response = await self._send(
            "POST",
            "/internal/speak",
            json={"text": text, "language": language},
        )
        try:
            return WorkerAudio(
                content=response.content,
                media_type=response.headers.get("content-type", "audio/wav").split(";", 1)[0],
                model=response.headers["x-model"],
                inference_ms=float(response.headers["x-inference-ms"]),
                sample_rate_hz=int(response.headers["x-audio-sample-rate"]),
                duration_s=float(response.headers["x-audio-duration-s"]),
                language=response.headers["x-speech-language"],
            )
        except (KeyError, ValueError) as exc:
            raise ApiError(
                "inference_failed", "Worker returned invalid audio metadata.", 502
            ) from exc

    async def aclose(self) -> None:
        await self._client.aclose()
