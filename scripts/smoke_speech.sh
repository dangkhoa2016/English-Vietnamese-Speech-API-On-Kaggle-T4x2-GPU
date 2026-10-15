#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${SPEECH_PYTHON_BIN:-$ROOT_DIR/.venv-speech/bin/python}"
RUNTIME_DIR="$ROOT_DIR/runtime"
mkdir -p "$RUNTIME_DIR"

[[ -x "$PYTHON_BIN" ]] || { echo "Speech runtime not found: $PYTHON_BIN" >&2; exit 2; }

export CUDA_VISIBLE_DEVICES=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$PYTHON_BIN" - "$RUNTIME_DIR" <<'PY'
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from en_vi_speech_api.speech_worker.asr import ASRService, build_whisper_infer, load_whisper_processor
from en_vi_speech_api.speech_worker.models import (
    WHISPER_MODEL_BASE,
    build_real_speech_models,
    discover_versioned_model,
)
from en_vi_speech_api.speech_worker.tts import TTSService, build_voxcpm_infer

runtime_dir = Path(sys.argv[1])


def snapshot(stage: str) -> None:
    output = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=index,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ],
        text=True,
    )
    print(f"\n=== {stage} pid={os.getpid()} ===", flush=True)
    print(output, end="", flush=True)


def validate_wav(path: Path) -> tuple[int, float]:
    import soundfile as sf

    info = sf.info(path)
    if info.channels != 1:
        raise SystemExit(f"Expected mono WAV: {path}")
    if info.frames <= 0 or info.duration <= 0:
        raise SystemExit(f"Empty WAV output: {path}")
    return info.samplerate, info.duration


async def main() -> None:
    pid = os.getpid()
    models = build_real_speech_models(stage_hook=snapshot)
    models.load()
    tts = TTSService(models=models, infer=build_voxcpm_infer(models))

    texts = {
        "en": "Hello from the English speech synthesis acceptance test.",
        "vi": "Xin chào từ bài kiểm tra tổng hợp giọng nói tiếng Việt.",
    }
    results = {}
    for language, text in texts.items():
        result = await tts.synthesize(text, language=language)
        output = runtime_dir / f"speech-{language}.wav"
        output.write_bytes(result.wav_bytes)
        sample_rate, duration = validate_wav(output)
        if sample_rate != result.sample_rate_hz:
            raise SystemExit("WAV sample-rate metadata mismatch")
        results[language] = (result, output)
        print(
            f"tts_{language}: inference_ms={result.inference_ms:.2f} "
            f"sample_rate={sample_rate} duration_s={duration:.3f} bytes={len(result.wav_bytes)}",
            flush=True,
        )
        snapshot(f"after_tts_{language}")

    en_16k = runtime_dir / "speech-en-16k.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(results["en"][1]),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(en_16k),
        ],
        check=True,
    )

    whisper_path = discover_versioned_model(
        WHISPER_MODEL_BASE,
        required=("config.json", "model.safetensors", "preprocessor_config.json"),
    )
    processor = load_whisper_processor(whisper_path)
    asr = ASRService(models=models, infer=build_whisper_infer(models, processor))
    transcript = await asr.transcribe(en_16k, language="en")
    if not transcript.text.strip():
        raise SystemExit("ASR after TTS returned an empty transcript")
    if not any(word in transcript.text.casefold() for word in ("hello", "english", "speech", "test")):
        raise SystemExit(f"ASR after TTS lacks expected semantic anchors: {transcript.text!r}")
    if not models.ready or os.getpid() != pid:
        raise SystemExit("Speech worker residency changed during TTS/ASR alternation")

    print(
        f"asr_after_tts: text={transcript.text!r} inference_ms={transcript.inference_ms:.2f}",
        flush=True,
    )
    snapshot("after_tts_then_asr")
    print(f"worker_pid={pid}", flush=True)
    print("SMOKE_SPEECH_IN_PROCESS=PASS", flush=True)


asyncio.run(main())
PY

printf '%s\n' '--- WAV validation ---'
for wav in "$RUNTIME_DIR/speech-en.wav" "$RUNTIME_DIR/speech-vi.wav"; do
  ffprobe -v error -show_entries stream=codec_name,sample_rate,channels,duration \
    -of default=noprint_wrappers=1 "$wav"
done

sleep 1
printf '%s\n' '--- GPU after speech process cleanup ---'
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader,nounits
used="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 1 | tr -d ' ')"
if [[ "$used" -gt 10 ]]; then
  echo "GPU1 did not return to baseline after TTS smoke: ${used} MiB" >&2
  exit 1
fi
printf '%s\n' 'SMOKE_SPEECH=PASS'
