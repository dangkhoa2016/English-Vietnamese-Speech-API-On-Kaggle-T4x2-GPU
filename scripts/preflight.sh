#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3.12}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

printf '%s\n' '=== English-Vietnamese Speech API: Kaggle T4x2 Preflight ==='
printf 'Python: '; "$PYTHON_BIN" --version
printf 'FFmpeg: '; ffmpeg -version | head -n 1
printf 'FFprobe: '; ffprobe -version | head -n 1
printf '%s\n' '--- Framework package metadata (no framework imports) ---'
"$PYTHON_BIN" - <<'PY'
from importlib.metadata import PackageNotFoundError, version
for name in ("torch", "jax", "keras", "keras-hub", "transformers"):
    try:
        print(f"{name}: {version(name)}")
    except PackageNotFoundError:
        print(f"{name}: not installed in selected Python")
PY
printf '%s\n' '--- GPU topology ---'
nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader
printf '%s\n' '--- RAM ---'
free -h
printf '%s\n' '--- Disk ---'
df -h /kaggle/working
printf 'CUDA_VISIBLE_DEVICES=%s\n' "${CUDA_VISIBLE_DEVICES:-<unset>}"

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
"$PYTHON_BIN" - <<'PY'
from en_vi_speech_api.coordinator.lifecycle import ports_are_free, validate_gpu_topology
report = validate_gpu_topology()
print(f"Validated GPUs: {report.gpu_count} x {report.gpu_names}")
print(f"VRAM MiB: {report.gpu_vram_mib}")
print(f"FFmpeg available: {report.ffmpeg_available}")
print(f"Working directory: {report.working_directory}")
print(f"Working directory writable: {report.working_directory_writable}")
if not report.ffmpeg_available:
    raise SystemExit("FFmpeg/FFprobe unavailable")
if not report.working_directory_writable:
    raise SystemExit("/kaggle/working is not writable")
if not ports_are_free():
    raise SystemExit("One or more required ports 8090-8092 are already in use")
print("Required ports 8090-8092: free")
PY
printf '%s\n' 'PRECHECK: PASS'
