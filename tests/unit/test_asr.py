import asyncio
from pathlib import Path

import pytest


class FakeModels:
    def __init__(self) -> None:
        self.ready = True
        self.gpu_semaphore = asyncio.Semaphore(1)


@pytest.mark.asyncio
async def test_asr_acquires_and_releases_shared_gpu_semaphore_on_success(tmp_path: Path) -> None:
    from en_vi_speech_api.speech_worker.asr import ASRService

    models = FakeModels()
    observed_locked: list[bool] = []

    def infer(wav_path: Path, language: str):
        observed_locked.append(models.gpu_semaphore.locked())
        assert wav_path.name == "sample.wav"
        assert language == "en"
        return "Hello from a synthetic voice.", 1

    service = ASRService(models=models, infer=infer)
    result = await service.transcribe(tmp_path / "sample.wav", language="en")

    assert result.text == "Hello from a synthetic voice."
    assert result.language == "en"
    assert result.chunk_count == 1
    assert observed_locked == [True]
    assert models.gpu_semaphore._value == 1


@pytest.mark.asyncio
async def test_asr_releases_shared_gpu_semaphore_on_failure(tmp_path: Path) -> None:
    from en_vi_speech_api.speech_worker.asr import ASRService

    models = FakeModels()
    observed_locked: list[bool] = []

    def fail(_wav_path: Path, _language: str):
        observed_locked.append(models.gpu_semaphore.locked())
        raise RuntimeError("synthetic ASR failure")

    service = ASRService(models=models, infer=fail)
    with pytest.raises(RuntimeError, match="synthetic ASR failure"):
        await service.transcribe(tmp_path / "sample.wav", language="en")

    assert observed_locked == [True]
    assert models.gpu_semaphore._value == 1


@pytest.mark.asyncio
async def test_asr_rejects_unready_models(tmp_path: Path) -> None:
    from en_vi_speech_api.speech_worker.asr import ASRService

    models = FakeModels()
    models.ready = False
    service = ASRService(models=models, infer=lambda *_: ("should not run", 1))

    with pytest.raises(RuntimeError, match="not ready"):
        await service.transcribe(tmp_path / "sample.wav")


def test_internal_transcribe_route_cleans_temporary_file(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from en_vi_speech_api.speech_worker.app import create_app
    from en_vi_speech_api.speech_worker.asr import TranscriptionResult
    from en_vi_speech_api.speech_worker.models import StubSpeechModels

    observed_paths: list[Path] = []

    class FakeASR:
        async def transcribe(self, wav_path: Path, language: str = "en"):
            observed_paths.append(wav_path)
            assert wav_path.exists()
            assert language == "en"
            return TranscriptionResult(
                text="Hello synthetic world.",
                language="en",
                chunk_count=1,
                inference_ms=12.5,
            )

    client = TestClient(create_app(StubSpeechModels(), asr_service=FakeASR()))
    response = client.post(
        "/internal/transcribe",
        files={"file": ("sample.wav", b"RIFFsynthetic", "audio/wav")},
        data={"language": "en"},
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Hello synthetic world."
    assert response.json()["chunk_count"] == 1
    assert len(observed_paths) == 1
    assert not observed_paths[0].exists()
