#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/runtime"
ENV_ROOT="${ENV_ROOT:-/tmp/envi-speech-envs}"
TRANSLATION_ENV="${TRANSLATION_ENV:-$ENV_ROOT/translation}"
SPEECH_ENV="${SPEECH_ENV:-$ENV_ROOT/speech}"
PYTHON_BIN="${PYTHON_BIN:-$TRANSLATION_ENV/bin/python}"
TRANSLATION_PYTHON_BIN="${TRANSLATION_PYTHON_BIN:-$PYTHON_BIN}"
SPEECH_PYTHON_BIN="${SPEECH_PYTHON_BIN:-$SPEECH_ENV/bin/python}"
STARTUP_TIMEOUT_S="${STARTUP_TIMEOUT_S:-900}"
STARTUP_PROGRESS_INTERVAL_S="${STARTUP_PROGRESS_INTERVAL_S:-15}"
STARTUP_MODE="${ENVI_STARTUP_MODE:-sequential}"
[[ "$STARTUP_MODE" == "sequential" || "$STARTUP_MODE" == "parallel" ]] || { echo "Invalid ENVI_STARTUP_MODE" >&2; exit 2; }
[[ "$STARTUP_TIMEOUT_S" =~ ^[0-9]+$ ]] && (( STARTUP_TIMEOUT_S > 0 )) || { echo "Invalid STARTUP_TIMEOUT_S" >&2; exit 2; }
[[ "$STARTUP_PROGRESS_INTERVAL_S" =~ ^[0-9]+$ ]] && (( STARTUP_PROGRESS_INTERVAL_S > 0 )) || { echo "Invalid STARTUP_PROGRESS_INTERVAL_S" >&2; exit 2; }
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
  echo "STARTING $name pid=$! log=$log_file" >&2
}

wait_ready() {
  local name="$1" url="$2"
  local pid_file="$RUNTIME_DIR/$name.pid" log_file="$RUNTIME_DIR/$name.log"
  local pid started now deadline next_report
  pid="$(cat "$pid_file")"
  started="$SECONDS"
  deadline=$((started + STARTUP_TIMEOUT_S))
  next_report=$((started + STARTUP_PROGRESS_INTERVAL_S))
  while :; do
    if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
      now=$SECONDS
      echo "$name ready (PID $pid) STARTUP_SECONDS=$((now - started))"
      return 0
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "$name exited during startup." >&2
      tail -n 120 "$log_file" >&2 || true
      return 1
    fi
    now=$SECONDS
    if ((now >= deadline)); then
      echo "$name readiness timeout after $((now - started))s (budget ${STARTUP_TIMEOUT_S}s)." >&2
      tail -n 120 "$log_file" >&2 || true
      return 1
    fi
    if ((now >= next_report)); then
      echo "STARTUP_PROGRESS worker=$name elapsed_s=$((now - started)) remaining_s=$((deadline - now))" >&2
      if [[ "$name" == "speech-worker" ]]; then
        grep 'SPEECH_LOAD_STAGE=' "$log_file" | tail -n 3 >&2 || true
      else
        grep -E 'ready|load|ERROR|Error|Traceback' "$log_file" | tail -n 2 >&2 || true
      fi
      next_report=$((now + STARTUP_PROGRESS_INTERVAL_S))
    fi
    sleep 1
  done
}

startup_fail() {
  "$ROOT_DIR/scripts/status.sh" >&2 || true
  "$ROOT_DIR/scripts/stop.sh" >/dev/null 2>&1 || true
  exit 1
}

# Default sequential: Kaggle-mounted models may compete for cold storage I/O.
# Opt-in parallel: independent GPU visibility with shared storage; measure before promotion.
echo "STARTUP_MODE=$STARTUP_MODE"
if [[ "$STARTUP_MODE" == "parallel" ]]; then
  start_one translation-worker 0 en_vi_speech_api.translation_worker.app:app 8091 "$TRANSLATION_PYTHON_BIN"
  start_one speech-worker 1 en_vi_speech_api.speech_worker.app:app 8092 "$SPEECH_PYTHON_BIN"
  wait_ready translation-worker http://127.0.0.1:8091/internal/ready || startup_fail
  wait_ready speech-worker http://127.0.0.1:8092/internal/ready || startup_fail
else
  start_one translation-worker 0 en_vi_speech_api.translation_worker.app:app 8091 "$TRANSLATION_PYTHON_BIN"
  wait_ready translation-worker http://127.0.0.1:8091/internal/ready || startup_fail
  start_one speech-worker 1 en_vi_speech_api.speech_worker.app:app 8092 "$SPEECH_PYTHON_BIN"
  wait_ready speech-worker http://127.0.0.1:8092/internal/ready || startup_fail
fi

start_one coordinator '' en_vi_speech_api.coordinator.app:app 8090 "$PYTHON_BIN"
wait_ready coordinator http://127.0.0.1:8090/health/live || startup_fail

echo "Service processes ready"
