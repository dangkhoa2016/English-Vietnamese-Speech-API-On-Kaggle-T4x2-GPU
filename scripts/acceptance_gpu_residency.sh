#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${SPEECH_PYTHON_BIN:-/tmp/envi-speech-envs/speech/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Speech Python runtime not found: $PYTHON_BIN" >&2
  exit 2
fi

export CUDA_VISIBLE_DEVICES=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

printf '%s\n' '=== Speech GPU co-residency acceptance ==='
printf 'python='; "$PYTHON_BIN" --version
printf '%s\n' '--- physical GPU baseline ---'
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader,nounits

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import os
import subprocess

from en_vi_speech_api.speech_worker.models import build_real_speech_models


def snapshot(stage: str) -> None:
    output = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ],
        text=True,
    )
    print(f"\n=== STAGE {stage} pid={os.getpid()} ===", flush=True)
    print(output, end="", flush=True)


pid = os.getpid()
snapshot("before_load")
models = build_real_speech_models(stage_hook=snapshot)
metadata = models.load()

ready_checks = [models.ready for _ in range(5)]
if ready_checks != [True] * 5:
    raise SystemExit(f"speech readiness was unstable: {ready_checks}")
if os.getpid() != pid:
    raise SystemExit("speech worker PID changed during residency acceptance")

voxcpm_devices = {parameter.device.type for parameter in models.voxcpm.tts_model.parameters()}
whisper_devices = {parameter.device.type for parameter in models.whisper.parameters()}
if voxcpm_devices != {"cuda"}:
    raise SystemExit(f"VoxCPM2 parameters are not CUDA-only: {sorted(voxcpm_devices)}")
if whisper_devices != {"cuda"}:
    raise SystemExit(f"Whisper parameters are not CUDA-only: {sorted(whisper_devices)}")

import torch

torch.cuda.synchronize()
snapshot("both_resident_warm")
print(f"metadata={metadata}", flush=True)
print(f"ready_checks={ready_checks}", flush=True)
print(f"worker_pid={pid}", flush=True)
print(f"voxcpm_parameter_devices={sorted(voxcpm_devices)}", flush=True)
print(f"whisper_parameter_devices={sorted(whisper_devices)}", flush=True)
print(f"torch_allocated_mib={torch.cuda.memory_allocated() / 1024**2:.1f}", flush=True)
print(f"torch_reserved_mib={torch.cuda.memory_reserved() / 1024**2:.1f}", flush=True)
print("SPEECH_CO_RESIDENCY_IN_PROCESS=PASS", flush=True)
PY

for _ in $(seq 1 20); do
  used="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 1 | tr -d ' ')"
  if [[ "$used" -le 10 ]]; then
    break
  fi
  sleep 0.25
done

printf '%s\n' '--- physical GPU after process cleanup ---'
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader,nounits
used="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 1 | tr -d ' ')"
if [[ "$used" -gt 10 ]]; then
  echo "GPU1 memory did not return to baseline after acceptance process exit: ${used} MiB" >&2
  exit 1
fi

printf '%s\n' 'ACCEPTANCE_GPU_RESIDENCY=PASS'
