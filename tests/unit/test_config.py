import pytest

from en_vi_speech_api.config import Settings
from en_vi_speech_api.errors import ApiError


def test_settings_defaults_match_approved_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "COORDINATOR_PORT",
        "TRANSLATION_WORKER_PORT",
        "SPEECH_WORKER_PORT",
        "MAX_AUDIO_UPLOAD_BYTES",
        "MAX_TEXT_UPLOAD_BYTES",
        "MAX_AUDIO_DURATION_S",
        "PUBLIC_REQUEST_TIMEOUT_S",
        "WORKER_REQUEST_TIMEOUT_S",
        "SPEECH_GPU_CONCURRENCY",
        "TRANSLATION_CONCURRENCY",
        "PUBLIC_MAX_INFLIGHT",
        "PUBLIC_MAX_PENDING",
        "ENABLE_CLOUDFLARE_TUNNEL",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.load()

    assert settings.coordinator_port == 8090
    assert settings.translation_worker_port == 8091
    assert settings.speech_worker_port == 8092
    assert settings.max_audio_upload_bytes == 25 * 1024 * 1024
    assert settings.max_text_upload_bytes == 100 * 1024
    assert settings.max_audio_duration_s == 1800
    assert settings.public_request_timeout_s == 600
    assert settings.worker_request_timeout_s == 540
    assert settings.speech_gpu_concurrency == 1
    assert settings.translation_concurrency == 1
    assert settings.public_max_inflight == 2
    assert settings.public_max_pending == 2
    assert settings.enable_cloudflare_tunnel is False


def test_settings_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COORDINATOR_PORT", "18090")
    monkeypatch.setenv("MAX_AUDIO_UPLOAD_BYTES", "1048576")
    monkeypatch.setenv("PUBLIC_REQUEST_TIMEOUT_S", "321")
    monkeypatch.setenv("ENABLE_CLOUDFLARE_TUNNEL", "true")

    settings = Settings.load()

    assert settings.coordinator_port == 18090
    assert settings.max_audio_upload_bytes == 1048576
    assert settings.public_request_timeout_s == 321
    assert settings.enable_cloudflare_tunnel is True


def test_settings_reject_port_collisions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COORDINATOR_PORT", "8090")
    monkeypatch.setenv("TRANSLATION_WORKER_PORT", "8090")

    with pytest.raises(ValueError, match="ports must be unique"):
        Settings.load()


def test_api_error_contract_contains_required_fields() -> None:
    error = ApiError(code="invalid_upload", message="Upload is invalid.", status_code=400)

    assert error.to_response("req-123") == {
        "error": {
            "code": "invalid_upload",
            "message": "Upload is invalid.",
            "request_id": "req-123",
        }
    }
    assert error.status_code == 400


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("MAX_AUDIO_UPLOAD_BYTES", "0"),
        ("MAX_TEXT_UPLOAD_BYTES", "-1"),
        ("MAX_AUDIO_DURATION_S", "0"),
        ("PUBLIC_REQUEST_TIMEOUT_S", "0"),
        ("WORKER_REQUEST_TIMEOUT_S", "-5"),
    ],
)
def test_settings_reject_non_positive_limits_and_timeouts(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=name):
        Settings.load()


def test_route_contracts_are_stable() -> None:
    from en_vi_speech_api.config import Routes

    assert Routes.TRANSCRIPTIONS == "/v1/audio/transcriptions"
    assert Routes.SPEECH == "/v1/audio/speech"
    assert Routes.TRANSLATE_AND_SPEAK == "/v1/audio/translate-and-speak"
    assert Routes.TRANSLATION_HEALTH == "/internal/health"
    assert Routes.TRANSLATION_READY == "/internal/ready"
    assert Routes.TRANSLATION_TRANSLATE == "/internal/translate"
    assert Routes.SPEECH_HEALTH == "/internal/health"
    assert Routes.SPEECH_READY == "/internal/ready"
    assert Routes.SPEECH_TRANSCRIBE == "/internal/transcribe"
    assert Routes.SPEECH_SPEAK == "/internal/speak"
