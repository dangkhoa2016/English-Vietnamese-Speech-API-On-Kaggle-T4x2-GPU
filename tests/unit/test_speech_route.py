import io

from fastapi.testclient import TestClient

from en_vi_speech_api.errors import ApiError


class FakeSpeechClient:
    def __init__(self, error: ApiError | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, str]] = []

    async def speak(self, text: str, *, language: str):
        if self.error:
            raise self.error
        from en_vi_speech_api.coordinator.worker_client import WorkerAudio

        self.calls.append((text, language))
        return WorkerAudio(
            content=b"RIFFpublic-wav",
            media_type="audio/wav",
            model="openbmb/VoxCPM2",
            inference_ms=88.25,
            sample_rate_hz=48000,
            duration_s=1.5,
            language=language,
        )


def test_public_speech_accepts_utf8_txt_and_returns_wav(tmp_path) -> None:
    from en_vi_speech_api.coordinator.app import create_app

    worker = FakeSpeechClient()
    client = TestClient(create_app(speech_client=worker, request_temp_base=tmp_path))
    response = client.post(
        "/v1/audio/speech",
        files={"file": ("speech.txt", io.BytesIO("Xin chào Việt Nam\n".encode()), "text/plain")},
        data={"language": "vi"},
    )

    assert response.status_code == 200
    assert response.content == b"RIFFpublic-wav"
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["x-request-id"]
    assert response.headers["x-model"] == "openbmb/VoxCPM2"
    assert response.headers["x-inference-ms"] == "88.250"
    assert worker.calls == [("Xin chào Việt Nam\n", "vi")]
    assert list(tmp_path.iterdir()) == []


def test_public_speech_worker_unavailable_is_structured(tmp_path) -> None:
    from en_vi_speech_api.coordinator.app import create_app

    worker = FakeSpeechClient(ApiError("worker_unavailable", "Worker is unavailable.", 503))
    client = TestClient(create_app(speech_client=worker, request_temp_base=tmp_path))
    response = client.post(
        "/v1/audio/speech",
        files={"file": ("speech.txt", b"Hello", "text/plain")},
        data={"language": "en"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "worker_unavailable"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
