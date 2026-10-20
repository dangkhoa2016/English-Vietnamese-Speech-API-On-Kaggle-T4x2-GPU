#!/usr/bin/env bash
set -Eeuo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/tmp/envi-speech-envs/translation/bin/python}"
LOG_FILE="$ROOT_DIR/runtime/translation-real-smoke.log"
PID_FILE="$ROOT_DIR/runtime/translation-real-smoke.pid"
mkdir -p "$ROOT_DIR/runtime" /tmp/envi-speech-cache/translategemma-jax

cleanup() {
  if [[ -f "$PID_FILE" ]]; then
    pid="$(cat "$PID_FILE")"
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 30); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.2
    done
    kill -9 "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
  fi
}
trap cleanup EXIT

printf '%s\n' '--- GPU baseline ---'
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader,nounits

export CUDA_VISIBLE_DEVICES=0
export KERAS_BACKEND=jax
export XLA_PYTHON_CLIENT_PREALLOCATE=true
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.97
export JAX_COMPILATION_CACHE_DIR=/tmp/envi-speech-cache/translategemma-jax
export JAX_PERSISTENT_CACHE_MIN_COMPILE_TIME_SECS=1
export JAX_PERSISTENT_CACHE_MIN_ENTRY_SIZE_BYTES=-1
export TRANSLATION_BACKEND=real
export TRANSLATEGEMMA_MODEL_PATH="${TRANSLATEGEMMA_MODEL_PATH:-/kaggle/input/models/keras/translategemma/keras/translategemma_4b_it/1}"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$PYTHON_BIN" -m uvicorn en_vi_speech_api.translation_worker.app:app \
  --host 127.0.0.1 --port 8091 >"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"
started_at="$(date +%s)"

for attempt in $(seq 1 900); do
  if curl -fsS --max-time 2 http://127.0.0.1:8091/internal/ready >/tmp/translation-ready.json 2>/dev/null; then
    break
  fi
  if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo 'Translation worker exited during startup.' >&2
    tail -n 120 "$LOG_FILE" >&2 || true
    exit 1
  fi
  if [[ "$attempt" -eq 900 ]]; then
    echo 'Translation worker readiness timeout.' >&2
    tail -n 120 "$LOG_FILE" >&2 || true
    exit 1
  fi
  sleep 1
done

ready_at="$(date +%s)"
printf 'startup_seconds=%s\n' "$((ready_at - started_at))"
printf 'ready='; cat /tmp/translation-ready.json; echo
printf '%s\n' '--- GPU at readiness ---'
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader,nounits

response="$(curl -fsS --max-time 540 \
  -H 'Content-Type: application/json' \
  -d '{"text":"Artificial intelligence can help people communicate across languages.","source_language":"en","target_language":"vi"}' \
  http://127.0.0.1:8091/internal/translate)"
printf 'translation_response=%s\n' "$response"

"$PYTHON_BIN" - "$response" <<'PY'
import json
import sys
payload = json.loads(sys.argv[1])
text = payload.get("text", "").strip()
if not text:
    raise SystemExit("empty Vietnamese translation")
if not any(ch in text for ch in "ăâđêôơưĂÂĐÊÔƠƯáàảãạấầẩẫậéèẻẽẹíìỉĩịóòỏõọúùủũụýỳỷỹỵ"):
    raise SystemExit(f"translation lacks expected Vietnamese Unicode evidence: {text!r}")
print("translation_unicode_check=PASS")
PY

printf '%s\n' '--- GPU after translation ---'
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader,nounits

cleanup
trap - EXIT
sleep 1
printf '%s\n' '--- GPU after worker cleanup ---'
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader,nounits
"$PYTHON_BIN" - <<'PY'
from en_vi_speech_api.coordinator.lifecycle import ports_are_free
if not ports_are_free((8091,)):
    raise SystemExit("translation worker port 8091 was not released")
print("worker_cleanup_check=PASS")
PY
printf '%s\n' 'SMOKE_TRANSLATION: PASS'
