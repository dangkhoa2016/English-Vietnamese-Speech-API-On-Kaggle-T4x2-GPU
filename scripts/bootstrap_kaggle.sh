#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_312="${PYTHON_312:-/usr/bin/python3.12}"
[[ -x "$PYTHON_312" ]] || PYTHON_312="$(command -v python3.12)"
UV_BIN="${UV_BIN:-$(command -v uv || true)}"
BOOTSTRAP_STARTED_AT="$(date +%s)"

KAGGLE_INPUT_ROOT="${KAGGLE_INPUT_ROOT:-/kaggle/input}"
RUNTIME_DATASET_OWNER="${RUNTIME_DATASET_OWNER:-dangkhoa2016}"
RUNTIME_DATASET_SLUG="english-vietnamese-speech-api-qualified-runtime"
RUNTIME_ARCHIVE_NAME="envi-speech-runtime-v1.bundle"
RUNTIME_ARCHIVE_OVERRIDE="${RUNTIME_ARCHIVE:-}"
REQUIRE_RUNTIME_DATASET="${REQUIRE_RUNTIME_DATASET:-false}"

resolve_runtime_archive() {
  if [[ -n "$RUNTIME_ARCHIVE_OVERRIDE" ]]; then
    printf '%s\n' "$RUNTIME_ARCHIVE_OVERRIDE"
    return 0
  fi

  local legacy_archive="$KAGGLE_INPUT_ROOT/$RUNTIME_DATASET_SLUG/$RUNTIME_ARCHIVE_NAME"
  local namespaced_archive="$KAGGLE_INPUT_ROOT/datasets/$RUNTIME_DATASET_OWNER/$RUNTIME_DATASET_SLUG/$RUNTIME_ARCHIVE_NAME"
  local discovered_archive=""

  if [[ -f "$legacy_archive" ]]; then
    printf '%s\n' "$legacy_archive"
    return 0
  fi
  if [[ -f "$namespaced_archive" ]]; then
    printf '%s\n' "$namespaced_archive"
    return 0
  fi
  if [[ -d "$KAGGLE_INPUT_ROOT/datasets" ]]; then
    discovered_archive="$(find "$KAGGLE_INPUT_ROOT/datasets" -type f -name "$RUNTIME_ARCHIVE_NAME" -path "*/$RUNTIME_DATASET_SLUG/*" -print -quit 2>/dev/null || true)"
    if [[ -n "$discovered_archive" ]]; then
      printf '%s\n' "$discovered_archive"
      return 0
    fi
    printf '%s\n' "$namespaced_archive"
    return 0
  fi

  printf '%s\n' "$legacy_archive"
}

RUNTIME_ARCHIVE="$(resolve_runtime_archive)"
RUNTIME_DATASET_ROOT="$(dirname "$RUNTIME_ARCHIVE")"
if [[ -n "$RUNTIME_ARCHIVE_OVERRIDE" ]]; then
  RUNTIME_DATASET_LAYOUT="EXPLICIT_OVERRIDE"
elif [[ "$RUNTIME_ARCHIVE" == "$KAGGLE_INPUT_ROOT/datasets/"* ]]; then
  RUNTIME_DATASET_LAYOUT="KAGGLE_NAMESPACED"
else
  RUNTIME_DATASET_LAYOUT="KAGGLE_LEGACY"
fi

echo "RUNTIME_DATASET_LAYOUT=$RUNTIME_DATASET_LAYOUT"
echo "RUNTIME_ARCHIVE_RESOLVED=$RUNTIME_ARCHIVE"

if [[ "${REQUIRE_RUNTIME_DATASET,,}" == "true" && ! -f "$RUNTIME_ARCHIVE" ]]; then
  echo "RUNTIME_DATASET_REQUIRED=FAIL" >&2
  echo "Required qualified runtime archive is missing: $RUNTIME_ARCHIVE" >&2
  exit 1
fi

if [[ -n "$UV_BIN" ]]; then
  echo "BOOTSTRAP_VENV_BACKEND=uv"
elif "$PYTHON_312" -c 'import ensurepip' >/dev/null 2>&1; then
  echo "BOOTSTRAP_VENV_BACKEND=stdlib"
else
  echo 'BOOTSTRAP_VENV_BACKEND=FAIL' >&2
  echo 'Python 3.12 lacks ensurepip and uv is unavailable; cannot create isolated runtimes.' >&2
  exit 1
fi

create_venv() {
  local target="$1"
  rm -rf "$target"
  if [[ -n "$UV_BIN" ]]; then
    "$UV_BIN" venv --python "$PYTHON_312" "$target" >/dev/null
  else
    "$PYTHON_312" -m venv "$target"
  fi
}

package_install() {
  local python_bin="$1"
  shift
  if [[ -n "$UV_BIN" ]]; then
    "$UV_BIN" pip install --python "$python_bin" "$@"
  else
    "$python_bin" -m pip install --no-cache-dir "$@"
  fi
}

package_check() {
  local python_bin="$1"
  if [[ -n "$UV_BIN" ]]; then
    "$UV_BIN" pip check --python "$python_bin"
  else
    "$python_bin" -m pip check
  fi
}

RUNTIME_EXTRACT_ROOT="${RUNTIME_EXTRACT_ROOT:-/tmp/envi-speech-runtime-v1}"
RUNTIME_ROOT="${RUNTIME_ROOT:-$RUNTIME_EXTRACT_ROOT/runtime}"
RUNTIME_WHEELHOUSE="${RUNTIME_WHEELHOUSE:-$RUNTIME_ROOT/wheelhouse}"
RUNTIME_MANIFEST_DIR="${RUNTIME_MANIFEST_DIR:-$RUNTIME_ROOT}"
RUNTIME_PYTORCH_DIR="${RUNTIME_PYTORCH_DIR:-$RUNTIME_ROOT/pytorch-cu128-wheels}"

ENV_ROOT="${ENV_ROOT:-/tmp/envi-speech-envs}"
TRANSLATION_ENV="${TRANSLATION_ENV:-$ENV_ROOT/translation}"
SPEECH_ENV="${SPEECH_ENV:-$ENV_ROOT/speech}"
XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/envi-speech-cache}"
HF_HOME="${HF_HOME:-$XDG_CACHE_HOME/huggingface}"
TORCH_HOME="${TORCH_HOME:-$XDG_CACHE_HOME/torch}"
KERAS_HOME="${KERAS_HOME:-$XDG_CACHE_HOME/keras}"
UV_CACHE_DIR="${UV_CACHE_DIR:-$XDG_CACHE_HOME/uv}"
export ENV_ROOT TRANSLATION_ENV SPEECH_ENV XDG_CACHE_HOME HF_HOME TORCH_HOME KERAS_HOME UV_CACHE_DIR
mkdir -p "$ENV_ROOT" "$XDG_CACHE_HOME" "$HF_HOME" "$TORCH_HOME" "$KERAS_HOME" "$UV_CACHE_DIR"

TRANSLATION_MANIFEST="$RUNTIME_MANIFEST_DIR/translation-requirements.txt"
SPEECH_PUBLIC_MANIFEST="$RUNTIME_MANIFEST_DIR/speech-public-requirements.txt"
SPEECH_VENDOR_MANIFEST="$RUNTIME_MANIFEST_DIR/speech-vendor-requirements.txt"
BUILD_MANIFEST="$RUNTIME_MANIFEST_DIR/build-requirements.txt"
EDITABLES_REQUIREMENT="editables==0.5"

runtime_contract_ready() {
  compgen -G "$RUNTIME_WHEELHOUSE/*.whl" >/dev/null 2>&1 \
    && compgen -G "$RUNTIME_PYTORCH_DIR/*.whl" >/dev/null 2>&1 \
    && [[ -f "$TRANSLATION_MANIFEST" ]] \
    && [[ -f "$SPEECH_PUBLIC_MANIFEST" ]] \
    && [[ -f "$SPEECH_VENDOR_MANIFEST" ]] \
    && [[ -f "$BUILD_MANIFEST" ]]
}

USE_RUNTIME_DATASET=0
if [[ -f "$RUNTIME_ARCHIVE" ]]; then
  if ! runtime_contract_ready; then
    rm -rf "$RUNTIME_EXTRACT_ROOT"
    mkdir -p "$RUNTIME_EXTRACT_ROOT"
    started_at="$(date +%s)"
    tar -xf "$RUNTIME_ARCHIVE" -C "$RUNTIME_EXTRACT_ROOT"
    finished_at="$(date +%s)"
    echo "RUNTIME_ARCHIVE_EXTRACT_SECONDS=$((finished_at - started_at))"
  fi
  runtime_contract_ready || {
    echo "Qualified runtime archive extracted but required wheelhouses/manifests are missing." >&2
    exit 1
  }
  USE_RUNTIME_DATASET=1
  echo "RUNTIME_SOURCE=KAGGLE_SINGLE_ARCHIVE"
  echo "RUNTIME_ARCHIVE=$RUNTIME_ARCHIVE"
  echo "RUNTIME_ROOT=$RUNTIME_ROOT"
  echo "RUNTIME_WHEELHOUSE=$RUNTIME_WHEELHOUSE"
  echo "RUNTIME_PYTORCH_DIR=$RUNTIME_PYTORCH_DIR"
else
  echo "RUNTIME_SOURCE=INTERNET_FALLBACK"
fi

echo "TRANSLATION_ENV=$TRANSLATION_ENV"
echo "SPEECH_ENV=$SPEECH_ENV"
echo "XDG_CACHE_HOME=$XDG_CACHE_HOME"
echo "TMP_RUNTIME_LAYOUT=PASS"

pip_install_local() {
  local python_bin="$1"
  shift
  package_install "$python_bin" --no-index --find-links "$RUNTIME_WHEELHOUSE" "$@"
}

pip_install_speech_local() {
  local python_bin="$1"
  shift
  package_install "$python_bin" --no-index \
    --find-links "$RUNTIME_WHEELHOUSE" \
    --find-links "$RUNTIME_PYTORCH_DIR" \
    "$@"
}

main_ready() {
  [[ -x "$TRANSLATION_ENV/bin/python" ]] || return 1
  "$TRANSLATION_ENV/bin/python" - <<'PY' >/dev/null 2>&1
from importlib.metadata import version
assert version('jax') == '0.11.2'
assert version('keras') == '3.15.1'
assert version('keras-hub') == '0.32.0'
import fastapi, uvicorn
PY
}

speech_ready() {
  [[ -x "$SPEECH_ENV/bin/python" ]] || return 1
  "$SPEECH_ENV/bin/python" - <<'PY' >/dev/null 2>&1
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
  echo "TRANSLATION_ENV_CREATE_SECONDS=0"
  echo "TRANSLATION_INSTALL_SECONDS=0"
else
  phase_started_at="$(date +%s)"
  create_venv "$TRANSLATION_ENV"
  echo "TRANSLATION_ENV_CREATE_SECONDS=$(($(date +%s) - phase_started_at))"
  phase_started_at="$(date +%s)"
  if (( USE_RUNTIME_DATASET )); then
    pip_install_local "$TRANSLATION_ENV/bin/python" -r "$TRANSLATION_MANIFEST"
    pip_install_local "$TRANSLATION_ENV/bin/python" -r "$BUILD_MANIFEST"
    pip_install_local "$TRANSLATION_ENV/bin/python" "$EDITABLES_REQUIREMENT"
    package_install "$TRANSLATION_ENV/bin/python" \
      --no-index --find-links "$RUNTIME_WHEELHOUSE" \
      --no-build-isolation --no-deps -e "$ROOT_DIR[dev]"
  else
    package_install "$TRANSLATION_ENV/bin/python" -e "$ROOT_DIR[dev]"
    package_install "$TRANSLATION_ENV/bin/python" \
      'jax[cuda12-local]==0.11.2' \
      'keras==3.15.1' \
      'keras-hub==0.32.0'
  fi
  echo "TRANSLATION_INSTALL_SECONDS=$(($(date +%s) - phase_started_at))"
fi

if speech_ready; then
  echo "Speech runtime already qualified; skipping install."
  echo "SPEECH_ENV_CREATE_SECONDS=0"
  echo "SPEECH_VENDOR_INSTALL_SECONDS=0"
  echo "SPEECH_PUBLIC_INSTALL_SECONDS=0"
else
  phase_started_at="$(date +%s)"
  create_venv "$SPEECH_ENV"
  echo "SPEECH_ENV_CREATE_SECONDS=$(($(date +%s) - phase_started_at))"
  if (( USE_RUNTIME_DATASET )); then
    phase_started_at="$(date +%s)"
    package_install "$SPEECH_ENV/bin/python" \
      --index-url https://pypi.org/simple --only-binary=:all: --no-deps \
      -r "$SPEECH_VENDOR_MANIFEST"
    echo "SPEECH_VENDOR_INSTALL_SECONDS=$(($(date +%s) - phase_started_at))"
    phase_started_at="$(date +%s)"
    pip_install_speech_local "$SPEECH_ENV/bin/python" -r "$SPEECH_PUBLIC_MANIFEST"
    package_check "$SPEECH_ENV/bin/python"
    echo "SPEECH_PUBLIC_INSTALL_SECONDS=$(($(date +%s) - phase_started_at))"
  else
    echo "SPEECH_VENDOR_INSTALL_SECONDS=0"
    phase_started_at="$(date +%s)"
    package_install "$SPEECH_ENV/bin/python" \
      --index-url https://download.pytorch.org/whl/cu128 \
      'torch==2.11.0+cu128' \
      'torchaudio==2.11.0+cu128'
    package_install "$SPEECH_ENV/bin/python" \
      'fastapi==0.143.2' \
      'uvicorn==0.54.0' \
      'python-multipart==0.0.32' \
      'transformers==5.19.0' \
      'soundfile==0.14.0' \
      'librosa==1.0.0'
    package_install "$SPEECH_ENV/bin/python" \
      -c "$ROOT_DIR/constraints-kaggle-tested.txt" \
      'voxcpm==2.0.3'
    echo "SPEECH_PUBLIC_INSTALL_SECONDS=$(($(date +%s) - phase_started_at))"
  fi
fi

main_ready || { echo 'Main runtime qualification failed.' >&2; exit 1; }
speech_ready || { echo 'Speech runtime qualification failed.' >&2; exit 1; }

echo "BOOTSTRAP_TOTAL_SECONDS=$(($(date +%s) - BOOTSTRAP_STARTED_AT))"
echo "BOOTSTRAP_KAGGLE=PASS"
