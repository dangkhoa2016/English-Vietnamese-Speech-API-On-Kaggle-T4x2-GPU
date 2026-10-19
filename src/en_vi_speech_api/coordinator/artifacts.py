from __future__ import annotations

import io
import json
import zipfile


def build_pipeline_zip(
    *,
    transcript: str,
    translation: str,
    speech_wav: bytes,
    metadata: dict,
    source_language: str = "en",
    target_language: str = "vi",
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"transcript.{source_language}.txt", transcript.encode("utf-8"))
        archive.writestr(f"translation.{target_language}.txt", translation.encode("utf-8"))
        archive.writestr(f"speech.{target_language}.wav", speech_wav)
        archive.writestr(
            "metadata.json",
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"),
        )
    return buffer.getvalue()
