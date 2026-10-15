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

RUNTIME_DATASET_SLUG="english-vietnamese-speech-api-qualified-runtime"
RUNTIME_ROOT="${RUNTIME_ROOT:-/kaggle/input/${RUNTIME_DATASET_SLUG}}"
RUNTIME_WHEELHOUSE="${RUNTIME_WHEELHOUSE:-$RUNTIME_ROOT}"
RUNTIME_MANIFEST_DIR="${RUNTIME_MANIFEST_DIR:-$RUNTIME_ROOT}"
TRANSLATION_MANIFEST="$RUNTIME_MANIFEST_DIR/translation-requirements.txt"
SPEECH_PUBLIC_MANIFEST="$RUNTIME_MANIFEST_DIR/speech-public-requirements.txt"
SPEECH_VENDOR_MANIFEST="$RUNTIME_MANIFEST_DIR/speech-vendor-requirements.txt"
BUILD_MANIFEST="$RUNTIME_MANIFEST_DIR/build-requirements.txt"
EDITABLES_REQUIREMENT="editables==0.5"
USE_RUNTIME_DATASET=0
if compgen -G "$RUNTIME_WHEELHOUSE/*.whl" >/dev/null 2>&1 \
  && [[ -f "$TRANSLATION_MANIFEST" ]] \
  && [[ -f "$SPEECH_PUBLIC_MANIFEST" ]] \
  && [[ -f "$SPEECH_VENDOR_MANIFEST" ]] \
  && [[ -f "$BUILD_MANIFEST" ]]; then
  USE_RUNTIME_DATASET=1
  echo "RUNTIME_SOURCE=KAGGLE_WHEELHOUSE_HYBRID"
  echo "RUNTIME_WHEELHOUSE=$RUNTIME_WHEELHOUSE"
else
  echo "RUNTIME_SOURCE=INTERNET_FALLBACK"
fi

pip_install_local() {
  local python_bin="$1"
  shift
  "$python_bin" -m pip install --no-index --find-links "$RUNTIME_WHEELHOUSE" "$@"
}


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
assert version('transformers') == '5.19.0'
assert version('soundfile') == '0.14.0'
assert version('librosa') == '1.0.0'
assert version('voxcpm') == '2.0.3'
assert torch.cuda.is_available()
PY
}

if main_ready; then
  echo "Main/translation runtime already qualified; skipping install."
else
  rm -rf "$ROOT_DIR/.venv"
  "$PYTHON_312" -m venv "$ROOT_DIR/.venv"
  if (( USE_RUNTIME_DATASET )); then
    pip_install_local "$ROOT_DIR/.venv/bin/python" -r "$TRANSLATION_MANIFEST"
    pip_install_local "$ROOT_DIR/.venv/bin/python" -r "$BUILD_MANIFEST"
    pip_install_local "$ROOT_DIR/.venv/bin/python" "$EDITABLES_REQUIREMENT"
    "$ROOT_DIR/.venv/bin/python" -m pip install \
      --no-index --find-links "$RUNTIME_WHEELHOUSE" \
      --no-build-isolation --no-deps -e "$ROOT_DIR[dev]"
  else
    "$ROOT_DIR/.venv/bin/pip" install --upgrade pip wheel
    "$ROOT_DIR/.venv/bin/pip" install -e "$ROOT_DIR[dev]"
    "$ROOT_DIR/.venv/bin/pip" install \
      'jax[cuda12-local]==0.11.2' \
      'keras==3.15.1' \
      'keras-hub==0.32.0'
  fi
fi

if speech_ready; then
  echo "Speech runtime already qualified; skipping install."
else
  rm -rf "$ROOT_DIR/.venv-speech"
  "$PYTHON_312" -m venv "$ROOT_DIR/.venv-speech"
  if (( USE_RUNTIME_DATASET )); then
    "$ROOT_DIR/.venv-speech/bin/python" -m pip install \
      --index-url https://pypi.org/simple --only-binary=:all: --no-deps \
      -r "$SPEECH_VENDOR_MANIFEST"
    pip_install_local "$ROOT_DIR/.venv-speech/bin/python" -r "$SPEECH_PUBLIC_MANIFEST"
    "$ROOT_DIR/.venv-speech/bin/python" -m pip check
  else
    "$ROOT_DIR/.venv-speech/bin/pip" install --upgrade pip wheel
    "$ROOT_DIR/.venv-speech/bin/pip" install \
      --index-url https://download.pytorch.org/whl/cu128 \
      'torch==2.11.0+cu128' \
      'torchaudio==2.11.0+cu128'
    "$ROOT_DIR/.venv-speech/bin/pip" install \
      'fastapi==0.143.2' \
      'uvicorn==0.54.0' \
      'python-multipart==0.0.32' \
      'transformers==5.19.0' \
      'soundfile==0.14.0' \
      'librosa==1.0.0'
    "$ROOT_DIR/.venv-speech/bin/pip" install \
      -c "$ROOT_DIR/constraints-kaggle-tested.txt" \
      'voxcpm==2.0.3'
  fi
fi

main_ready || { echo 'Main runtime qualification failed.' >&2; exit 1; }
speech_ready || { echo 'Speech runtime qualification failed.' >&2; exit 1; }

echo "BOOTSTRAP_KAGGLE=PASS"
