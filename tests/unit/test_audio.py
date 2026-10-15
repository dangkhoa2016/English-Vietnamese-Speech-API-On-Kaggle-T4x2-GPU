import io
import wave
from pathlib import Path

import pytest
from starlette.datastructures import Headers, UploadFile

from en_vi_speech_api.errors import ApiError


def wav_bytes(*, sample_rate: int, channels: int, frames: int) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * frames * channels)
    return buffer.getvalue()


def upload_wav(data: bytes) -> UploadFile:
    return UploadFile(
        filename="sample.wav",
        file=io.BytesIO(data),
        headers=Headers({"content-type": "audio/wav"}),
    )


@pytest.mark.asyncio
async def test_validate_audio_upload_accepts_valid_wav_and_records_duration(tmp_path: Path) -> None:
    from en_vi_speech_api.coordinator.limits import validate_audio_upload

    upload = upload_wav(wav_bytes(sample_rate=16000, channels=1, frames=1600))
    validated = await validate_audio_upload(
        upload,
        tmp_path,
        max_bytes=1024 * 1024,
        max_duration_s=30,
    )

    assert validated.path.exists()
    assert validated.size_bytes > 0
    assert validated.duration_s == pytest.approx(0.1, abs=0.02)
    assert validated.original_filename == "sample.wav"


@pytest.mark.asyncio
async def test_validate_audio_upload_rejects_malformed_media(tmp_path: Path) -> None:
    from en_vi_speech_api.coordinator.limits import validate_audio_upload

    upload = upload_wav(b"RIFF-this-is-not-a-valid-wave")
    with pytest.raises(ApiError) as exc_info:
        await validate_audio_upload(
            upload,
            tmp_path,
            max_bytes=1024,
            max_duration_s=30,
        )
    assert exc_info.value.code == "invalid_upload"


@pytest.mark.asyncio
async def test_validate_audio_upload_rejects_excessive_duration(tmp_path: Path) -> None:
    from en_vi_speech_api.coordinator.limits import validate_audio_upload

    upload = upload_wav(wav_bytes(sample_rate=16000, channels=1, frames=3200))
    with pytest.raises(ApiError) as exc_info:
        await validate_audio_upload(
            upload,
            tmp_path,
            max_bytes=1024 * 1024,
            max_duration_s=0.1,
        )
    assert exc_info.value.code == "audio_too_long"


def test_normalize_for_asr_produces_pcm16_mono_16khz(tmp_path: Path) -> None:
    from en_vi_speech_api.coordinator.audio import normalize_for_asr, probe_audio

    source = tmp_path / "stereo-44k.wav"
    source.write_bytes(wav_bytes(sample_rate=44100, channels=2, frames=4410))

    normalized = normalize_for_asr(source, output_dir=tmp_path / "normalized")
    probe = probe_audio(normalized.path)

    assert normalized.path.exists()
    assert normalized.path.name == "normalized.wav"
    assert probe.sample_rate_hz == 16000
    assert probe.channels == 1
    assert probe.codec_name == "pcm_s16le"
    assert probe.duration_s == pytest.approx(0.1, abs=0.03)
