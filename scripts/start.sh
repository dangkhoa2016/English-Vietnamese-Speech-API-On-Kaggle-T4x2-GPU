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

wait_ready() {
  local name="$1" url="$2"
  local pid_file="$RUNTIME_DIR/$name.pid" log_file="$RUNTIME_DIR/$name.log"
  local pid="$(cat "$pid_file")"
  for _ in $(seq 1 "$STARTUP_TIMEOUT_S"); do
    if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
      echo "$name ready (PID $pid)"
      return 0
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "$name exited during startup." >&2
      tail -n 120 "$log_file" >&2 || true
      return 1
    fi
    sleep 1
  done
  echo "$name readiness timeout after ${STARTUP_TIMEOUT_S}s." >&2
  tail -n 120 "$log_file" >&2 || true
  return 1
}

startup_fail() {
  "$ROOT_DIR/scripts/status.sh" >&2 || true
  "$ROOT_DIR/scripts/stop.sh" >/dev/null 2>&1 || true
  exit 1
}

# Stage cold model loads deliberately. Kaggle attached-model storage can become
# severely I/O-bound when TranslateGemma and the speech stack load concurrently.
start_one translation-worker 0 en_vi_speech_api.translation_worker.app:app 8091 "$TRANSLATION_PYTHON_BIN"
wait_ready translation-worker http://127.0.0.1:8091/internal/ready || startup_fail

start_one speech-worker 1 en_vi_speech_api.speech_worker.app:app 8092 "$SPEECH_PYTHON_BIN"
wait_ready speech-worker http://127.0.0.1:8092/internal/ready || startup_fail

start_one coordinator '' en_vi_speech_api.coordinator.app:app 8090 "$PYTHON_BIN"
wait_ready coordinator http://127.0.0.1:8090/health/live || startup_fail

echo "Service processes ready"
