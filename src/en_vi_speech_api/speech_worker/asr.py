from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class SpeechModelState(Protocol):
    ready: bool
    whisper: Any
    gpu_semaphore: asyncio.Semaphore


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    text: str
    language: str
    chunk_count: int
    inference_ms: float
    model: str = "openai/whisper-large-v3-turbo"


class ASRService:
    def __init__(
        self,
        *,
        models: SpeechModelState,
        infer: Callable[[Path, str], tuple[str, int]],
    ) -> None:
        self.models = models
        self._infer = infer

    async def transcribe(self, wav_path: Path, language: str = "en") -> TranscriptionResult:
        if not self.models.ready:
            raise RuntimeError("Speech models are not ready")
        if language != "en":
            raise ValueError("v1 ASR supports explicit English transcription only")

        started = time.perf_counter()
        async with self.models.gpu_semaphore:
            text, chunk_count = await asyncio.to_thread(self._infer, Path(wav_path), language)
        return TranscriptionResult(
            text=text.strip(),
            language=language,
            chunk_count=chunk_count,
            inference_ms=(time.perf_counter() - started) * 1000,
        )


def load_whisper_processor(model_path: Path | str) -> Any:
    from transformers import AutoProcessor

    return AutoProcessor.from_pretrained(str(model_path), local_files_only=True)


def build_whisper_infer(
    models: SpeechModelState,
    processor: Any,
    *,
    chunk_seconds: int = 30,
) -> Callable[[Path, str], tuple[str, int]]:
    if chunk_seconds <= 0:
        raise ValueError("chunk_seconds must be positive")

    def infer(wav_path: Path, language: str) -> tuple[str, int]:
        import soundfile as sf
        import torch

        audio, sample_rate = sf.read(str(wav_path), dtype="float32", always_2d=False)
        if sample_rate != 16000:
            raise ValueError(f"Expected 16 kHz normalized WAV, got {sample_rate} Hz")
        if getattr(audio, "ndim", 1) != 1:
            raise ValueError("Expected mono normalized WAV")
        if len(audio) == 0:
            raise ValueError("Audio is empty")

        chunk_samples = chunk_seconds * sample_rate
        transcripts: list[str] = []
        chunk_count = 0
        for start in range(0, len(audio), chunk_samples):
            chunk = audio[start : start + chunk_samples]
            inputs = processor(
                chunk,
                sampling_rate=sample_rate,
                return_tensors="pt",
                return_attention_mask=True,
            )
            input_features = inputs.input_features.to(device="cuda:0", dtype=torch.float16)
            attention_mask = inputs.attention_mask.to(device="cuda:0")
            with torch.inference_mode():
                generated_ids = models.whisper.generate(
                    input_features,
                    attention_mask=attention_mask,
                    language=language,
                    task="transcribe",
                )
            decoded = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
            if decoded:
                transcripts.append(decoded)
            chunk_count += 1

        return " ".join(transcripts).strip(), chunk_count

    return infer
