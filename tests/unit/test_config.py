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
        "API_AUTH_REQUIRED",
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
    assert settings.api_auth_required is False


def test_settings_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COORDINATOR_PORT", "18090")
    monkeypatch.setenv("MAX_AUDIO_UPLOAD_BYTES", "1048576")
    monkeypatch.setenv("PUBLIC_REQUEST_TIMEOUT_S", "321")
    monkeypatch.setenv("ENABLE_CLOUDFLARE_TUNNEL", "true")
    monkeypatch.setenv("API_AUTH_REQUIRED", "true")

    settings = Settings.load()

    assert settings.coordinator_port == 18090
    assert settings.max_audio_upload_bytes == 1048576
    assert settings.public_request_timeout_s == 321
    assert settings.enable_cloudflare_tunnel is True
    assert settings.api_auth_required is True


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


def test_parse_nvidia_smi_output_zero_gpus() -> None:
    from en_vi_speech_api.coordinator.lifecycle import parse_nvidia_smi_csv

    assert parse_nvidia_smi_csv("") == ()


def test_parse_nvidia_smi_output_one_t4() -> None:
    from en_vi_speech_api.coordinator.lifecycle import parse_nvidia_smi_csv

    gpus = parse_nvidia_smi_csv("0, Tesla T4, 15360\n")
    assert len(gpus) == 1
    assert gpus[0].index == 0
    assert gpus[0].name == "Tesla T4"
    assert gpus[0].memory_total_mib == 15360


def test_parse_nvidia_smi_output_two_t4s() -> None:
    from en_vi_speech_api.coordinator.lifecycle import parse_nvidia_smi_csv

    gpus = parse_nvidia_smi_csv("0, Tesla T4, 15360\n1, Tesla T4, 15360\n")
    assert [gpu.index for gpu in gpus] == [0, 1]
    assert [gpu.name for gpu in gpus] == ["Tesla T4", "Tesla T4"]


def test_validate_gpu_topology_rejects_less_than_two_t4s() -> None:
    from en_vi_speech_api.coordinator.lifecycle import validate_gpu_topology

    with pytest.raises(RuntimeError, match="exactly two Tesla T4 GPUs"):
        validate_gpu_topology("0, Tesla T4, 15360\n")


def test_validate_gpu_topology_accepts_two_t4s(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from en_vi_speech_api.coordinator import lifecycle

    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0,1")
    monkeypatch.setattr(lifecycle, "KAGGLE_WORKING_DIR", tmp_path)
    monkeypatch.setattr(lifecycle.shutil, "which", lambda name: f"/usr/bin/{name}")

    report = lifecycle.validate_gpu_topology("0, Tesla T4, 15360\n1, Tesla T4, 15360\n")

    assert report.gpu_count == 2
    assert report.gpu_names == ("Tesla T4", "Tesla T4")
    assert report.gpu_vram_mib == (15360, 15360)
    assert report.cuda_visible_devices == "0,1"
    assert report.ffmpeg_available is True
    assert report.working_directory == tmp_path
    assert report.working_directory_writable is True


def test_ports_are_free_treats_time_wait_as_rebindable() -> None:
    import socket

    from en_vi_speech_api.coordinator.lifecycle import ports_are_free

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    listener.listen(1)
    client = socket.create_connection(("127.0.0.1", port))
    connection, _ = listener.accept()
    connection.close()
    client.close()
    listener.close()

    assert ports_are_free((port,)) is True
