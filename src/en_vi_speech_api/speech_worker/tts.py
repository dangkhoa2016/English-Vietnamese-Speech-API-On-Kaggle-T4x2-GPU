from __future__ import annotations

import asyncio
import io
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol


class SpeechModelState(Protocol):
    ready: bool
    voxcpm: Any
    gpu_semaphore: asyncio.Semaphore


@dataclass(frozen=True, slots=True)
class SpeechResult:
    wav_bytes: bytes
    language: str
    sample_rate_hz: int
    duration_s: float
    inference_ms: float
    model: str = "openbmb/VoxCPM2"


def encode_wav_bytes(samples: Any, sample_rate_hz: int) -> bytes:
    import soundfile as sf

    buffer = io.BytesIO()
    sf.write(buffer, samples, sample_rate_hz, format="WAV", subtype="PCM_16")
    return buffer.getvalue()


class TTSService:
    def __init__(
        self,
        *,
        models: SpeechModelState,
        infer: Callable[[str, str], tuple[Any, int]],
        encode_wav: Callable[[Any, int], bytes] = encode_wav_bytes,
    ) -> None:
        self.models = models
        self._infer = infer
        self._encode_wav = encode_wav

    async def synthesize(self, text: str, language: str) -> SpeechResult:
        if not self.models.ready:
            raise RuntimeError("Speech models are not ready")
        if language not in {"en", "vi"}:
            raise ValueError("TTS language must be 'en' or 'vi'")
        normalized_text = text.strip()
        if not normalized_text:
            raise ValueError("TTS text must not be empty")

        started = time.perf_counter()
        async with self.models.gpu_semaphore:
            samples, sample_rate_hz = await asyncio.to_thread(
                self._infer,
                normalized_text,
                language,
            )
        sample_count = len(samples)
        if sample_rate_hz <= 0 or sample_count <= 0:
            raise RuntimeError("VoxCPM2 returned an invalid waveform")
        wav_bytes = self._encode_wav(samples, sample_rate_hz)
        return SpeechResult(
            wav_bytes=wav_bytes,
            language=language,
            sample_rate_hz=sample_rate_hz,
            duration_s=sample_count / sample_rate_hz,
            inference_ms=(time.perf_counter() - started) * 1000,
        )


def build_voxcpm_infer(models: SpeechModelState) -> Callable[[str, str], tuple[Any, int]]:
    def infer(text: str, language: str) -> tuple[Any, int]:
        if language not in {"en", "vi"}:
            raise ValueError("Unsupported VoxCPM2 language")
        waveform = models.voxcpm.generate(text=text)
        sample_rate_hz = int(models.voxcpm.tts_model.sample_rate)
        return waveform, sample_rate_hz

    return infer
