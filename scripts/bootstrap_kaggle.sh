#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_312="${PYTHON_312:-/usr/bin/python3.12}"
[[ -x "$PYTHON_312" ]] || PYTHON_312="$(command -v python3.12)"
VOXCPM_COMMIT="f772e498a45fbb5fb8e13fbf9b9c48be9fe33e69"
VOXCPM_SOURCE="${VOXCPM_SOURCE:-/kaggle/working/voxcpm-upstream-$VOXCPM_COMMIT}"

main_ready() {
  [[ -x "$ROOT_DIR/.venv/bin/python" ]] || return 1
  "$ROOT_DIR/.venv/bin/python" - <<'PY' >/dev/null 2>&1
from importlib.metadata import version
assert version('jax') == '0.7.2'
assert version('keras') == '3.13.2'
assert version('keras-hub') == '0.26.0'
import fastapi, uvicorn
PY
}

speech_ready() {
  [[ -x "$ROOT_DIR/.venv-speech/bin/python" ]] || return 1
  "$ROOT_DIR/.venv-speech/bin/python" - <<'PY' >/dev/null 2>&1
import torch, transformers, soundfile, voxcpm, fastapi, uvicorn
assert torch.cuda.is_available()
PY
}

if main_ready; then
  echo "Main/translation runtime already qualified; skipping install."
else
  rm -rf "$ROOT_DIR/.venv"
  "$PYTHON_312" -m venv "$ROOT_DIR/.venv"
  "$ROOT_DIR/.venv/bin/pip" install --upgrade pip wheel
  "$ROOT_DIR/.venv/bin/pip" install -e "$ROOT_DIR[dev]"
  "$ROOT_DIR/.venv/bin/pip" install \
    'jax[cuda12-local]==0.7.2' \
    'keras==3.13.2' \
    'keras-hub==0.26.0'
fi

if speech_ready; then
  echo "Speech runtime already qualified; skipping install."
else
  rm -rf "$ROOT_DIR/.venv-speech"
  "$PYTHON_312" -m venv "$ROOT_DIR/.venv-speech"
  "$ROOT_DIR/.venv-speech/bin/pip" install --upgrade pip wheel
  if [[ ! -d "$VOXCPM_SOURCE/.git" ]]; then
    git clone --filter=blob:none https://github.com/OpenBMB/VoxCPM.git "$VOXCPM_SOURCE"
  fi
  git -C "$VOXCPM_SOURCE" fetch --depth=1 origin "$VOXCPM_COMMIT"
  git -C "$VOXCPM_SOURCE" checkout --detach "$VOXCPM_COMMIT"
  "$ROOT_DIR/.venv-speech/bin/pip" install -e "$VOXCPM_SOURCE"
  "$ROOT_DIR/.venv-speech/bin/pip" install \
    'fastapi==0.143.2' \
    'uvicorn==0.54.0' \
    'python-multipart==0.0.32' \
    'transformers==4.57.1' \
    'soundfile==0.14.0' \
    'librosa==0.11.0'
fi

main_ready || { echo 'Main runtime qualification failed.' >&2; exit 1; }
speech_ready || { echo 'Speech runtime qualification failed.' >&2; exit 1; }

echo "BOOTSTRAP_KAGGLE=PASS"
