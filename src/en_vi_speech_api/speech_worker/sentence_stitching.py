from __future__ import annotations

import io
import re
from collections.abc import Sequence

import numpy as np
import soundfile as sf

# Split only at clear sentence boundaries; never rewrite API or translated text.
# Known abbreviations are kept together.
_ABBREVIATIONS = frozenset({"TS.", "ThS.", "PGS.", "GS.", "Dr.", "Mr.", "Mrs.", "Ms.", "TP.", "v.v.", "e.g.", "i.e."})


def split_vietnamese_sentences(text: str, *, max_segments: int = 12) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    segments: list[str] = []
    begin = 0
    for boundary in re.finditer(r"(?<=[.!?])\s+", cleaned):
        before = cleaned[begin:boundary.start()].strip()
        after = cleaned[boundary.end():]
        if not before or not after or not after[0].isupper():
            continue
        if before.split()[-1] in _ABBREVIATIONS:
            continue
        segments.append(before)
        begin = boundary.end()
        if len(segments) >= max_segments:
            return [cleaned]
    segments.append(cleaned[begin:].strip())
    return segments


def join_pcm_wav_segments(wavs: Sequence[bytes], *, pause_ms: int = 300) -> tuple[np.ndarray, int]:
    if not 0 <= pause_ms <= 2000:
        raise ValueError("pause_ms must be between 0 and 2000")
    if not wavs:
        raise ValueError("At least one WAV segment is required")
    decoded: list[np.ndarray] = []
    sample_rate: int | None = None
    for encoded in wavs:
        with sf.SoundFile(io.BytesIO(encoded)) as wav:
            if wav.channels != 1 or wav.subtype != "PCM_16":
                raise ValueError("Expected mono PCM_16 WAV segments")
            if sample_rate is not None and wav.samplerate != sample_rate:
                raise ValueError("Sentence WAV sample rates differ")
            sample_rate = wav.samplerate
            audio = wav.read(dtype="float32")
        if not len(audio) or not np.isfinite(audio).all():
            raise ValueError("Invalid or empty WAV segment")
        decoded.append(audio)
    assert sample_rate is not None
    pause = np.zeros(round(pause_ms * sample_rate / 1000), dtype=np.float32)
    chunks: list[np.ndarray] = []
    for index, item in enumerate(decoded):
        if index:
            chunks.append(pause)
        chunks.append(item)
    return np.concatenate(chunks), sample_rate