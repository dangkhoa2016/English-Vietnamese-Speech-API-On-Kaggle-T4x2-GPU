#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/runtime"

show_process() {
  local name="$1" port="$2" health_url="$3"
  local pid_file="$RUNTIME_DIR/$name.pid"
  local pid='<none>' state='stopped' ready='no'
  if [[ -f "$pid_file" ]]; then
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      state='running'
    fi
  fi
  if curl -fsS --max-time 2 "$health_url" >/dev/null 2>&1; then
    ready='yes'
  fi
  printf '%-20s pid=%-8s port=%-5s state=%-8s ready=%s\n' "$name" "$pid" "$port" "$state" "$ready"
}

show_process coordinator 8090 http://127.0.0.1:8090/health/live
show_process translation-worker 8091 http://127.0.0.1:8091/internal/ready
show_process speech-worker 8092 http://127.0.0.1:8092/internal/ready
