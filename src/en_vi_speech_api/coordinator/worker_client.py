from __future__ import annotations

from typing import Any

import httpx

from en_vi_speech_api.errors import ApiError


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

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
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
        return response.json()

    async def health(self) -> dict[str, Any]:
        return await self._request("GET", "/internal/health")

    async def ready(self) -> dict[str, Any]:
        return await self._request("GET", "/internal/ready")

    async def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", path, json=payload)

    async def aclose(self) -> None:
        await self._client.aclose()
