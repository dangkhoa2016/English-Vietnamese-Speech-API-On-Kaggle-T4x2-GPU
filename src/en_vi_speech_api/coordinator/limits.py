from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from starlette.datastructures import UploadFile

from en_vi_speech_api.coordinator.audio import probe_audio
from en_vi_speech_api.errors import ApiError

AUDIO_EXTENSIONS = {
    ".flac",
    ".m4a",
    ".mp3",
    ".ogg",
    ".wav",
    ".webm",
}
AUDIO_CONTENT_TYPES = {
    "audio/flac",
    "audio/m4a",
    "audio/mpeg",
    "audio/ogg",
    "audio/wav",
    "audio/wave",
    "audio/webm",
    "audio/x-m4a",
    "audio/x-wav",
    "video/webm",
}


@dataclass(frozen=True, slots=True)
class ValidatedUpload:
    path: Path
    size_bytes: int
    duration_s: float
    original_filename: str
    content_type: str | None


async def read_text_upload(
    upload: UploadFile,
    *,
    max_bytes: int,
    chunk_size: int = 64 * 1024,
) -> str:
    if max_bytes <= 0 or chunk_size <= 0:
        raise ValueError("max_bytes and chunk_size must be positive")
    filename = (upload.filename or "").strip()
    if Path(filename).suffix.casefold() != ".txt":
        raise ApiError("unsupported_media_type", "Text upload must be a UTF-8 .txt file.", 415)

    data = bytearray()
    while True:
        chunk = await upload.read(min(chunk_size, max_bytes + 1))
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > max_bytes:
            raise ApiError("text_too_large", "Text upload exceeds the configured byte limit.", 413)

    try:
        text = bytes(data).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ApiError("invalid_utf8", "Text upload must be valid UTF-8.", 400) from exc
    if not text.strip():
        raise ApiError("empty_text", "Text upload must not be empty.", 400)
    return text


async def validate_audio_upload(
    upload: UploadFile,
    output_dir: Path,
    *,
    max_bytes: int,
    max_duration_s: float,
    chunk_size: int = 1024 * 1024,
) -> ValidatedUpload:
    if max_bytes <= 0 or max_duration_s <= 0 or chunk_size <= 0:
        raise ValueError("audio limits and chunk_size must be positive")

    filename = (upload.filename or "").strip()
    extension = Path(filename).suffix.casefold()
    content_type = upload.content_type.casefold() if upload.content_type else None
    if extension not in AUDIO_EXTENSIONS:
        raise ApiError("unsupported_media_type", "Unsupported audio file extension.", 415)
    if content_type and content_type not in AUDIO_CONTENT_TYPES:
        raise ApiError("unsupported_media_type", "Unsupported audio media type.", 415)

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"upload{extension}"
    size_bytes = 0
    try:
        with destination.open("wb") as handle:
            while True:
                chunk = await upload.read(min(chunk_size, max_bytes + 1))
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > max_bytes:
                    raise ApiError(
                        "audio_too_large", "Audio upload exceeds the configured byte limit.", 413
                    )
                handle.write(chunk)

        if size_bytes == 0:
            raise ApiError("invalid_upload", "Audio upload must not be empty.", 400)
        probe = probe_audio(destination)
        if probe.duration_s > max_duration_s:
            raise ApiError("audio_too_long", "Audio duration exceeds the configured limit.", 413)
        return ValidatedUpload(
            path=destination,
            size_bytes=size_bytes,
            duration_s=probe.duration_s,
            original_filename=filename,
            content_type=content_type,
        )
    except Exception:
        destination.unlink(missing_ok=True)
        raise


@contextmanager
def request_temp_directory(*, base_dir: Path | None = None) -> Iterator[Path]:
    if base_dir is not None:
        base_dir.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix="en-vi-speech-", dir=str(base_dir) if base_dir else None))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
