#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/runtime"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
TRANSLATION_PYTHON_BIN="${TRANSLATION_PYTHON_BIN:-$PYTHON_BIN}"
SPEECH_PYTHON_BIN="${SPEECH_PYTHON_BIN:-$ROOT_DIR/.venv-speech/bin/python}"
STARTUP_TIMEOUT_S="${STARTUP_TIMEOUT_S:-180}"
mkdir -p "$RUNTIME_DIR"

"$ROOT_DIR/scripts/preflight.sh" >/dev/null

start_one() {
  local name="$1" gpu="$2" app="$3" port="$4" python_bin="$5"
  local pid_file="$RUNTIME_DIR/$name.pid" log_file="$RUNTIME_DIR/$name.log"
  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "$name already running (PID $(cat "$pid_file"))" >&2
    return 1
  fi
  env CUDA_VISIBLE_DEVICES="$gpu" PYTHONPATH="$ROOT_DIR/src" \
    "$python_bin" -m uvicorn "$app" --host 127.0.0.1 --port "$port" \
    >"$log_file" 2>&1 &
  echo $! >"$pid_file"
}

start_one translation-worker 0 en_vi_speech_api.translation_worker.app:app 8091 "$TRANSLATION_PYTHON_BIN"
start_one speech-worker 1 en_vi_speech_api.speech_worker.app:app 8092 "$SPEECH_PYTHON_BIN"
start_one coordinator '' en_vi_speech_api.coordinator.app:app 8090 "$PYTHON_BIN"

for attempt in $(seq 1 "$STARTUP_TIMEOUT_S"); do
  if curl -fsS http://127.0.0.1:8091/internal/ready >/dev/null \
    && curl -fsS http://127.0.0.1:8092/internal/ready >/dev/null \
    && curl -fsS http://127.0.0.1:8090/health/live >/dev/null; then
    echo "Service processes ready"
    exit 0
  fi
  sleep 1
done

echo "Startup readiness timeout" >&2
"$ROOT_DIR/scripts/status.sh" >&2 || true
"$ROOT_DIR/scripts/stop.sh" >/dev/null 2>&1 || true
exit 1
