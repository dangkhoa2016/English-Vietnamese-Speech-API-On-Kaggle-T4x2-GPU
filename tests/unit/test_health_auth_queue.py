from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from en_vi_speech_api.errors import ApiError


class FakeWorker:
    def __init__(self, *, ready_payload=None, error: ApiError | None = None) -> None:
        self.ready_payload = ready_payload or {"ready": True}
        self.error = error

    async def ready(self):
        if self.error:
            raise self.error
        return self.ready_payload


@pytest.mark.parametrize(
    ("translation_error", "speech_error", "expected_status"),
    [
        (None, None, 200),
        (ApiError("worker_unavailable", "translation down", 503), None, 503),
        (None, ApiError("worker_unavailable", "speech down", 503), 503),
        (
            ApiError("worker_unavailable", "translation down", 503),
            ApiError("worker_unavailable", "speech down", 503),
            503,
        ),
    ],
)
def test_health_ready_reflects_both_workers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    translation_error: ApiError | None,
    speech_error: ApiError | None,
    expected_status: int,
) -> None:
    monkeypatch.setenv("API_AUTH_REQUIRED", "false")
    from en_vi_speech_api.coordinator.app import create_app

    client = TestClient(
        create_app(
            translation_client=FakeWorker(error=translation_error),
            speech_client=FakeWorker(error=speech_error),
            runtime_dir=tmp_path,
        )
    )
    assert client.get("/health/live").status_code == 200
    response = client.get("/health/ready")
    assert response.status_code == expected_status
    payload = response.json()
    if expected_status == 200:
        assert payload["ready"] is True
        assert payload["workers"]["translation"]["ready"] is True
        assert payload["workers"]["speech"]["ready"] is True
    else:
        assert payload["ready"] is False
        assert "workers" in payload


def test_generated_api_key_is_persistent_and_private(tmp_path: Path) -> None:
    from en_vi_speech_api.coordinator.auth import load_or_create_api_key

    key_path = tmp_path / "api_key.txt"
    first = load_or_create_api_key(key_path)
    second = load_or_create_api_key(key_path)

    assert first == second
    assert len(first) >= 32
    assert key_path.read_text(encoding="utf-8").strip() == first
    assert key_path.stat().st_mode & 0o777 == 0o600


def test_auth_required_rejects_missing_and_accepts_bearer(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("API_AUTH_REQUIRED", "true")
    from en_vi_speech_api.coordinator.app import create_app

    client = TestClient(
        create_app(
            translation_client=FakeWorker(),
            speech_client=FakeWorker(),
            runtime_dir=tmp_path,
        )
    )
    key = (tmp_path / "api_key.txt").read_text(encoding="utf-8").strip()

    missing = client.get("/health/ready")
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "unauthorized"

    accepted = client.get("/health/ready", headers={"Authorization": f"Bearer {key}"})
    assert accepted.status_code == 200


@pytest.mark.asyncio
async def test_admission_active_pending_queue_full_and_release() -> None:
    from en_vi_speech_api.coordinator.admission import AdmissionController

    admission = AdmissionController(max_inflight=1, max_pending=1, wait_timeout_s=1.0)
    first = await admission.acquire()
    assert admission.active == 1
    assert admission.pending == 0

    waiter = asyncio.create_task(admission.acquire())
    await asyncio.sleep(0.02)
    assert admission.active == 1
    assert admission.pending == 1

    with pytest.raises(ApiError) as exc_info:
        await admission.acquire()
    assert exc_info.value.code == "queue_full"
    assert exc_info.value.status_code == 429

    await first.release()
    second = await waiter
    assert admission.active == 1
    assert admission.pending == 0
    await second.release()
    assert admission.active == 0


@pytest.mark.asyncio
async def test_admission_timeout_releases_pending_slot() -> None:
    from en_vi_speech_api.coordinator.admission import AdmissionController

    admission = AdmissionController(max_inflight=1, max_pending=1, wait_timeout_s=0.02)
    first = await admission.acquire()
    with pytest.raises(ApiError) as exc_info:
        await admission.acquire()
    assert exc_info.value.code == "request_timeout"
    assert admission.active == 1
    assert admission.pending == 0
    await first.release()
    assert admission.active == 0
