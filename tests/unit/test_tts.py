import asyncio

import pytest


class FakeModels:
    def __init__(self) -> None:
        self.ready = True
        self.gpu_semaphore = asyncio.Semaphore(1)


@pytest.mark.asyncio
@pytest.mark.parametrize("language", ["en", "vi"])
async def test_tts_supports_en_vi_and_uses_shared_semaphore(language: str) -> None:
    from en_vi_speech_api.speech_worker.tts import TTSService

    models = FakeModels()
    observed_locked: list[bool] = []

    def infer(text: str, actual_language: str):
        observed_locked.append(models.gpu_semaphore.locked())
        assert text == "Hello world" or text == "Xin chào thế giới"
        assert actual_language == language
        return [0.0, 0.25, -0.25, 0.0], 48000

    def encode(samples, sample_rate: int) -> bytes:
        assert len(samples) == 4
        assert sample_rate == 48000
        return b"RIFFsynthetic-wav"

    text = "Hello world" if language == "en" else "Xin chào thế giới"
    service = TTSService(models=models, infer=infer, encode_wav=encode)
    result = await service.synthesize(text, language=language)

    assert result.wav_bytes == b"RIFFsynthetic-wav"
    assert result.language == language
    assert result.sample_rate_hz == 48000
    assert result.duration_s == pytest.approx(4 / 48000)
    assert observed_locked == [True]
    assert models.gpu_semaphore._value == 1


@pytest.mark.asyncio
async def test_tts_rejects_empty_text() -> None:
    from en_vi_speech_api.speech_worker.tts import TTSService

    models = FakeModels()
    service = TTSService(models=models, infer=lambda *_: ([], 48000))

    with pytest.raises(ValueError, match="empty"):
        await service.synthesize("   \n", language="en")


@pytest.mark.asyncio
async def test_tts_releases_shared_semaphore_on_inference_failure() -> None:
    from en_vi_speech_api.speech_worker.tts import TTSService

    models = FakeModels()
    observed_locked: list[bool] = []

    def fail(_text: str, _language: str):
        observed_locked.append(models.gpu_semaphore.locked())
        raise RuntimeError("synthetic TTS failure")

    service = TTSService(models=models, infer=fail)
    with pytest.raises(RuntimeError, match="synthetic TTS failure"):
        await service.synthesize("Hello", language="en")

    assert observed_locked == [True]
    assert models.gpu_semaphore._value == 1


def test_internal_speak_route_returns_wav_headers() -> None:
    from fastapi.testclient import TestClient

    from en_vi_speech_api.speech_worker.app import create_app
    from en_vi_speech_api.speech_worker.models import StubSpeechModels
    from en_vi_speech_api.speech_worker.tts import SpeechResult

    class FakeTTS:
        async def synthesize(self, text: str, language: str):
            assert text == "Xin chào"
            assert language == "vi"
            return SpeechResult(
                wav_bytes=b"RIFFfake-wave",
                language="vi",
                sample_rate_hz=48000,
                duration_s=1.25,
                inference_ms=25.5,
            )

    client = TestClient(create_app(StubSpeechModels(), tts_service=FakeTTS()))
    response = client.post("/internal/speak", json={"text": "Xin chào", "language": "vi"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["x-speech-language"] == "vi"
    assert response.headers["x-audio-sample-rate"] == "48000"
    assert response.content == b"RIFFfake-wave"
