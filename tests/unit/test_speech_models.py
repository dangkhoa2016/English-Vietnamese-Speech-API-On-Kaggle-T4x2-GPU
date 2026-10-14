import asyncio

import pytest
from fastapi.testclient import TestClient


def test_speech_models_require_both_models_before_ready() -> None:
    from en_vi_speech_api.speech_worker.models import SpeechModels

    loaded: list[str] = []
    models = SpeechModels(
        voxcpm_loader=lambda: loaded.append("voxcpm") or object(),
        whisper_loader=lambda: loaded.append("whisper") or object(),
    )

    assert models.ready is False
    metadata = models.load()

    assert loaded == ["voxcpm", "whisper"]
    assert models.voxcpm is not None
    assert models.whisper is not None
    assert models.ready is True
    assert metadata["ready"] is True


def test_speech_models_stay_not_ready_if_second_model_fails() -> None:
    from en_vi_speech_api.speech_worker.models import SpeechModels

    def fail_whisper():
        raise RuntimeError("synthetic whisper load failure")

    models = SpeechModels(voxcpm_loader=object, whisper_loader=fail_whisper)

    with pytest.raises(RuntimeError, match="synthetic whisper load failure"):
        models.load()

    assert models.voxcpm is not None
    assert models.whisper is None
    assert models.ready is False


def test_speech_models_own_one_shared_gpu_semaphore() -> None:
    from en_vi_speech_api.speech_worker.models import SpeechModels

    models = SpeechModels(voxcpm_loader=object, whisper_loader=object)

    assert isinstance(models.gpu_semaphore, asyncio.Semaphore)
    assert models.gpu_semaphore._value == 1


def test_speech_worker_ready_fails_closed_until_both_models_loaded() -> None:
    from en_vi_speech_api.speech_worker.app import create_app
    from en_vi_speech_api.speech_worker.models import SpeechModels

    models = SpeechModels(voxcpm_loader=object, whisper_loader=object)
    client = TestClient(create_app(models))

    before = client.get("/internal/ready")
    assert before.status_code == 503

    models.load()
    after = client.get("/internal/ready")
    assert after.status_code == 200
    assert after.json()["ready"] is True


def test_discover_speech_model_path_uses_latest_complete_version(tmp_path) -> None:
    from en_vi_speech_api.speech_worker.models import discover_versioned_model

    base = tmp_path / "model"
    incomplete = base / "3"
    complete = base / "2"
    incomplete.mkdir(parents=True)
    complete.mkdir(parents=True)
    (incomplete / "config.json").write_text("{}", encoding="utf-8")
    (complete / "config.json").write_text("{}", encoding="utf-8")
    (complete / "model.safetensors").write_bytes(b"x")

    assert discover_versioned_model(base, required=("config.json", "model.safetensors")) == complete


def test_real_speech_loader_rejects_more_than_one_logical_gpu(monkeypatch) -> None:
    from en_vi_speech_api.speech_worker import models as module

    class FakeCuda:
        @staticmethod
        def is_available():
            return True

        @staticmethod
        def device_count():
            return 2

    fake_torch = type("FakeTorch", (), {"cuda": FakeCuda})
    monkeypatch.setattr(module, "_import_torch", lambda: fake_torch)

    with pytest.raises(RuntimeError, match="exactly one logical CUDA device"):
        module.assert_single_logical_cuda_device()
