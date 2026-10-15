import io
from pathlib import Path

import pytest
from starlette.datastructures import Headers, UploadFile

from en_vi_speech_api.errors import ApiError


def make_upload(name: str, data: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        filename=name,
        file=io.BytesIO(data),
        headers=Headers({"content-type": content_type}),
    )


@pytest.mark.asyncio
async def test_read_text_upload_accepts_utf8_bom_newlines_and_vietnamese() -> None:
    from en_vi_speech_api.coordinator.limits import read_text_upload

    upload = make_upload(
        "input.txt", b"\xef\xbb\xbfXin ch\xc3\xa0o\nVi\xe1\xbb\x87t Nam\n", "text/plain"
    )
    text = await read_text_upload(upload, max_bytes=1024)
    assert text == "Xin chào\nViệt Nam\n"


@pytest.mark.asyncio
async def test_read_text_upload_rejects_non_utf8_binary() -> None:
    from en_vi_speech_api.coordinator.limits import read_text_upload

    upload = make_upload("input.txt", b"\xff\xfe\x00\x81", "text/plain")
    with pytest.raises(ApiError) as exc_info:
        await read_text_upload(upload, max_bytes=1024)
    assert exc_info.value.code == "invalid_utf8"


@pytest.mark.asyncio
async def test_read_text_upload_rejects_empty_text() -> None:
    from en_vi_speech_api.coordinator.limits import read_text_upload

    upload = make_upload("input.txt", b" \n\t", "text/plain")
    with pytest.raises(ApiError) as exc_info:
        await read_text_upload(upload, max_bytes=1024)
    assert exc_info.value.code == "empty_text"


@pytest.mark.asyncio
async def test_read_text_upload_rejects_oversize_without_unbounded_read() -> None:
    from en_vi_speech_api.coordinator.limits import read_text_upload

    upload = make_upload("input.txt", b"x" * 33, "text/plain")
    with pytest.raises(ApiError) as exc_info:
        await read_text_upload(upload, max_bytes=32, chunk_size=8)
    assert exc_info.value.code == "text_too_large"


@pytest.mark.asyncio
async def test_audio_upload_rejects_unsupported_extension_before_probe(tmp_path: Path) -> None:
    from en_vi_speech_api.coordinator.limits import validate_audio_upload

    upload = make_upload("payload.exe", b"not audio", "application/octet-stream")
    with pytest.raises(ApiError) as exc_info:
        await validate_audio_upload(upload, tmp_path, max_bytes=1024, max_duration_s=30)
    assert exc_info.value.code == "unsupported_media_type"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_audio_upload_rejects_oversize_and_removes_partial_file(tmp_path: Path) -> None:
    from en_vi_speech_api.coordinator.limits import validate_audio_upload

    upload = make_upload("sample.wav", b"x" * 65, "audio/wav")
    with pytest.raises(ApiError) as exc_info:
        await validate_audio_upload(
            upload,
            tmp_path,
            max_bytes=64,
            max_duration_s=30,
            chunk_size=16,
        )
    assert exc_info.value.code == "audio_too_large"
    assert list(tmp_path.iterdir()) == []


def test_request_temp_directory_is_removed_on_success_and_exception(tmp_path: Path) -> None:
    from en_vi_speech_api.coordinator.limits import request_temp_directory

    with request_temp_directory(base_dir=tmp_path) as request_dir:
        marker = request_dir / "marker.txt"
        marker.write_text("x", encoding="utf-8")
        success_path = request_dir
    assert not success_path.exists()

    with pytest.raises(RuntimeError), request_temp_directory(base_dir=tmp_path) as request_dir:
        (request_dir / "marker.txt").write_text("x", encoding="utf-8")
        failure_path = request_dir
        raise RuntimeError("synthetic failure")
    assert not failure_path.exists()


@pytest.mark.asyncio
async def test_read_text_upload_rejects_non_txt_extension() -> None:
    from en_vi_speech_api.coordinator.limits import read_text_upload

    upload = make_upload("input.bin", b"Xin chao", "application/octet-stream")
    with pytest.raises(ApiError) as exc_info:
        await read_text_upload(upload, max_bytes=1024)
    assert exc_info.value.code == "unsupported_media_type"
