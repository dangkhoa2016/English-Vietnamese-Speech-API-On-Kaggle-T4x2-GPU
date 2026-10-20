import httpx
import pytest

from en_vi_speech_api.errors import ApiError


@pytest.mark.asyncio
async def test_worker_client_routes_health_ready_and_post_json() -> None:
    from en_vi_speech_api.coordinator.worker_client import WorkerClient

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/internal/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/internal/ready":
            return httpx.Response(200, json={"ready": True})
        if request.url.path == "/internal/translate":
            assert request.method == "POST"
            return httpx.Response(200, json={"text": "Xin chào"})
        return httpx.Response(404)

    client = WorkerClient(
        "http://127.0.0.1:8091",
        timeout_s=2,
        transport=httpx.MockTransport(handler),
    )
    assert await client.health() == {"status": "ok"}
    assert await client.ready() == {"ready": True}
    assert await client.post_json("/internal/translate", {"text": "Hello"}) == {"text": "Xin chào"}
    await client.aclose()


@pytest.mark.asyncio
async def test_worker_client_converts_timeout_to_api_error() -> None:
    from en_vi_speech_api.coordinator.worker_client import WorkerClient

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("worker too slow", request=request)

    client = WorkerClient(
        "http://127.0.0.1:8092",
        timeout_s=1,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(ApiError) as exc_info:
        await client.health()
    assert exc_info.value.code == "worker_timeout"
    assert exc_info.value.status_code == 504
    await client.aclose()


@pytest.mark.asyncio
async def test_worker_client_converts_connect_error_to_api_error() -> None:
    from en_vi_speech_api.coordinator.worker_client import WorkerClient

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("worker offline", request=request)

    client = WorkerClient(
        "http://127.0.0.1:8092",
        timeout_s=1,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(ApiError) as exc_info:
        await client.ready()
    assert exc_info.value.code == "worker_unavailable"
    assert exc_info.value.status_code == 503
    await client.aclose()


def test_worker_process_environments_isolate_physical_gpus() -> None:
    from en_vi_speech_api.coordinator.lifecycle import build_worker_environment

    translation_env = build_worker_environment("translation")
    speech_env = build_worker_environment("speech")

    assert translation_env["CUDA_VISIBLE_DEVICES"] == "0"
    assert speech_env["CUDA_VISIBLE_DEVICES"] == "1"
