import io
import wave

from fastapi.testclient import TestClient

from en_vi_speech_api.errors import ApiError


def wav_bytes() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        wav.writeframes(b"\x00\x00" * 2 * 4410)
    return buffer.getvalue()


class FakeSpeechClient:
    def __init__(self, error: ApiError | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, int, int, str]] = []

    async def transcribe(self, wav_path, *, language: str):
        if self.error:
            raise self.error
        import wave

        with wave.open(str(wav_path), "rb") as wav:
            self.calls.append((wav_path.name, wav.getframerate(), wav.getnchannels(), language))
        return {
            "text": "Hello from the public transcription endpoint.",
            "language": language,
            "chunk_count": 1,
            "inference_ms": 25.5,
            "model": "openai/whisper-large-v3-turbo",
        }


def test_public_transcription_normalizes_audio_and_returns_timing(tmp_path) -> None:
    from en_vi_speech_api.coordinator.app import create_app

    worker = FakeSpeechClient()
    client = TestClient(create_app(speech_client=worker, request_temp_base=tmp_path))
    response = client.post(
        "/v1/audio/transcriptions",
        files={"file": ("english.wav", wav_bytes(), "audio/wav")},
        data={"language": "en"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["text"].startswith("Hello")
    assert payload["language"] == "en"
    assert payload["model"] == "openai/whisper-large-v3-turbo"
    assert payload["inference_ms"] == 25.5
    assert payload["normalized_audio_duration_s"] > 0
    assert payload["request_id"] == response.headers["x-request-id"]
    assert worker.calls == [("normalized.wav", 16000, 1, "en")]
    assert list(tmp_path.iterdir()) == []


def test_public_transcription_worker_timeout_is_structured(tmp_path) -> None:
    from en_vi_speech_api.coordinator.app import create_app

    worker = FakeSpeechClient(ApiError("worker_timeout", "Worker request timed out.", 504))
    client = TestClient(create_app(speech_client=worker, request_temp_base=tmp_path))
    response = client.post(
        "/v1/audio/transcriptions",
        files={"file": ("english.wav", wav_bytes(), "audio/wav")},
    )

    assert response.status_code == 504
    payload = response.json()
    assert payload["error"]["code"] == "worker_timeout"
    assert payload["error"]["request_id"] == response.headers["x-request-id"]
    assert list(tmp_path.iterdir()) == []
