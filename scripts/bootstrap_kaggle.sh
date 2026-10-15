#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_312="${PYTHON_312:-/usr/bin/python3.12}"
[[ -x "$PYTHON_312" ]] || PYTHON_312="$(command -v python3.12)"

ensure_python312_venv() {
  if "$PYTHON_312" -c 'import ensurepip' >/dev/null 2>&1; then
    return 0
  fi
  if [[ "$(id -u)" -ne 0 ]]; then
    echo 'Python 3.12 is missing ensurepip; install python3.12-venv before running bootstrap.' >&2
    return 1
  fi
  echo 'Installing missing Python 3.12 venv support...'
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3.12-venv
  "$PYTHON_312" -c 'import ensurepip' >/dev/null 2>&1
}

ensure_python312_venv

main_ready() {
  [[ -x "$ROOT_DIR/.venv/bin/python" ]] || return 1
  "$ROOT_DIR/.venv/bin/python" - <<'PY' >/dev/null 2>&1
from importlib.metadata import version
assert version('jax') == '0.11.2'
assert version('keras') == '3.15.1'
assert version('keras-hub') == '0.32.0'
import fastapi, uvicorn
PY
}

speech_ready() {
  [[ -x "$ROOT_DIR/.venv-speech/bin/python" ]] || return 1
  "$ROOT_DIR/.venv-speech/bin/python" - <<'PY' >/dev/null 2>&1
from importlib.metadata import version
import torch, transformers, soundfile, voxcpm, fastapi, uvicorn
assert version('torch') == '2.11.0+cu128'
assert version('torchaudio') == '2.11.0+cu128'
assert version('transformers') == '4.57.1'
assert version('soundfile') == '0.14.0'
assert version('librosa') == '0.11.0'
assert version('voxcpm') == '2.0.3'
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
    'jax[cuda12-local]==0.11.2' \
    'keras==3.15.1' \
    'keras-hub==0.32.0'
fi

if speech_ready; then
  echo "Speech runtime already qualified; skipping install."
else
  rm -rf "$ROOT_DIR/.venv-speech"
  "$PYTHON_312" -m venv "$ROOT_DIR/.venv-speech"
  "$ROOT_DIR/.venv-speech/bin/pip" install --upgrade pip wheel
  "$ROOT_DIR/.venv-speech/bin/pip" install \
    --index-url https://download.pytorch.org/whl/cu128 \
    'torch==2.11.0+cu128' \
    'torchaudio==2.11.0+cu128'
  "$ROOT_DIR/.venv-speech/bin/pip" install \
    'fastapi==0.143.2' \
    'uvicorn==0.54.0' \
    'python-multipart==0.0.32' \
    'transformers==4.57.1' \
    'soundfile==0.14.0' \
    'librosa==0.11.0'
  "$ROOT_DIR/.venv-speech/bin/pip" install \
    -c "$ROOT_DIR/constraints-kaggle-tested.txt" \
    'voxcpm==2.0.3'
fi

main_ready || { echo 'Main runtime qualification failed.' >&2; exit 1; }
speech_ready || { echo 'Speech runtime qualification failed.' >&2; exit 1; }

echo "BOOTSTRAP_KAGGLE=PASS"
