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
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("transcript.en.txt", transcript.encode("utf-8"))
        archive.writestr("translation.vi.txt", translation.encode("utf-8"))
        archive.writestr("speech.vi.wav", speech_wav)
        archive.writestr(
            "metadata.json",
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"),
        )
    return buffer.getvalue()
