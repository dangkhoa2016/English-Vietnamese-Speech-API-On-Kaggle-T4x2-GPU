#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${SPEECH_PYTHON_BIN:-$ROOT_DIR/.venv-speech/bin/python}"
FIXTURE="$ROOT_DIR/data/fixtures/english-short.wav"
EXPECTED="$ROOT_DIR/data/fixtures/english-short.expected.txt"

[[ -x "$PYTHON_BIN" ]] || { echo "Speech runtime not found: $PYTHON_BIN" >&2; exit 2; }
[[ -f "$FIXTURE" ]] || { echo "ASR fixture not found: $FIXTURE" >&2; exit 2; }
[[ -f "$EXPECTED" ]] || { echo "ASR expected transcript not found: $EXPECTED" >&2; exit 2; }

export CUDA_VISIBLE_DEVICES=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

ffprobe -v error -show_entries stream=codec_name,sample_rate,channels,duration \
  -of default=noprint_wrappers=1 "$FIXTURE"

"$PYTHON_BIN" - "$FIXTURE" "$EXPECTED" <<'PY'
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

fixture = Path(sys.argv[1])
expected = Path(sys.argv[2]).read_text(encoding="utf-8").strip()


def gpu_used_mib() -> int:
    text = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits", "-i", "1"],
        text=True,
    )
    return int(text.strip())


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


async def main() -> None:
    models = build_real_speech_models(stage_hook=snapshot)
    models.load()
    whisper_path = discover_versioned_model(
        WHISPER_MODEL_BASE,
        required=("config.json", "model.safetensors", "preprocessor_config.json"),
    )
    processor = load_whisper_processor(whisper_path)
    service = ASRService(models=models, infer=build_whisper_infer(models, processor))

    used: list[int] = []
    results = []
    for run in range(1, 4):
        result = await service.transcribe(fixture, language="en")
        results.append(result)
        used.append(gpu_used_mib())
        print(
            f"run={run} text={result.text!r} chunks={result.chunk_count} "
            f"inference_ms={result.inference_ms:.2f} gpu_used_mib={used[-1]}",
            flush=True,
        )

    if any(not result.text.strip() for result in results):
        raise SystemExit("Whisper produced an empty transcript")
    if any(result.chunk_count != 1 for result in results):
        raise SystemExit("Short ASR fixture unexpectedly required multiple chunks")
    if results[-1].text.casefold().rstrip(". ") != expected.casefold().rstrip(". "):
        raise SystemExit(
            f"Final transcript did not match the retained fixture text: {results[-1].text!r}"
        )
    if used[2] > used[1] + 128:
        raise SystemExit(f"GPU memory grew unexpectedly across warm ASR requests: {used}")
    if os.getpid() <= 1:
        raise SystemExit("Invalid worker PID")

    snapshot("after_three_asr_requests")
    print(f"gpu_memory_series_mib={used}", flush=True)
    print("SMOKE_TRANSCRIPTION_IN_PROCESS=PASS", flush=True)


asyncio.run(main())
PY

sleep 1
printf '%s\n' '--- GPU after ASR process cleanup ---'
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader,nounits
used="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 1 | tr -d ' ')"
if [[ "$used" -gt 10 ]]; then
  echo "GPU1 did not return to baseline after ASR smoke: ${used} MiB" >&2
  exit 1
fi
printf '%s\n' 'SMOKE_TRANSCRIPTION=PASS'
