from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from en_vi_speech_api.errors import ApiError


@dataclass(frozen=True, slots=True)
class AudioProbe:
    duration_s: float
    sample_rate_hz: int
    channels: int
    codec_name: str
    format_name: str


@dataclass(frozen=True, slots=True)
class NormalizedAudio:
    path: Path
    duration_s: float
    sample_rate_hz: int = 16000
    channels: int = 1
    codec_name: str = "pcm_s16le"


def probe_audio(path: Path) -> AudioProbe:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,format_name:stream=codec_type,codec_name,sample_rate,channels",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
        payload = json.loads(result.stdout)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise ApiError("invalid_upload", "Uploaded audio could not be decoded.", 400) from exc

    audio_streams = [
        stream for stream in payload.get("streams", []) if stream.get("codec_type") == "audio"
    ]
    if not audio_streams:
        raise ApiError("invalid_upload", "Uploaded file contains no audio stream.", 400)
    stream = audio_streams[0]
    try:
        duration_s = float(payload.get("format", {}).get("duration"))
        sample_rate_hz = int(stream.get("sample_rate"))
        channels = int(stream.get("channels"))
        codec_name = str(stream.get("codec_name"))
        format_name = str(payload.get("format", {}).get("format_name"))
    except (TypeError, ValueError) as exc:
        raise ApiError("invalid_upload", "Audio metadata is incomplete.", 400) from exc
    if duration_s <= 0 or sample_rate_hz <= 0 or channels <= 0:
        raise ApiError("invalid_upload", "Audio metadata is invalid.", 400)
    return AudioProbe(
        duration_s=duration_s,
        sample_rate_hz=sample_rate_hz,
        channels=channels,
        codec_name=codec_name,
        format_name=format_name,
    )


def normalize_for_asr(input_path: Path, *, output_dir: Path) -> NormalizedAudio:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "normalized.wav"
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
        probe = probe_audio(output_path)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ApiError) as exc:
        output_path.unlink(missing_ok=True)
        if isinstance(exc, ApiError):
            raise
        raise ApiError("invalid_upload", "Audio normalization failed.", 400) from exc
    if probe.sample_rate_hz != 16000 or probe.channels != 1 or probe.codec_name != "pcm_s16le":
        output_path.unlink(missing_ok=True)
        raise ApiError("invalid_upload", "Audio normalization contract was not satisfied.", 400)
    return NormalizedAudio(path=output_path, duration_s=probe.duration_s)
