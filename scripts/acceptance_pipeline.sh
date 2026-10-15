#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/runtime"
RESULTS="$RUNTIME_DIR/benchmark-pipeline/results.json"
BASELINE_GPU_MAX_USED_MIB="${BASELINE_GPU_MAX_USED_MIB:-64}"
STARTUP_TIMEOUT_S="${STARTUP_TIMEOUT_S:-360}"

cleanup() { "$ROOT_DIR/scripts/stop.sh" >/dev/null 2>&1 || true; }
trap cleanup EXIT
cleanup
sleep 1

printf '%s\n' '=== Task 12 baseline GPU ==='
nvidia-smi --query-gpu=index,name,memory.used,memory.free --format=csv,noheader,nounits
while IFS= read -r used; do
  used="${used// /}"
  if [[ "$used" -gt "$BASELINE_GPU_MAX_USED_MIB" ]]; then
    echo "GPU baseline is not clean (${used} MiB > ${BASELINE_GPU_MAX_USED_MIB} MiB); refusing Task 12 acceptance." >&2
    exit 3
  fi
done < <(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)

SPEECH_BACKEND=real TRANSLATION_BACKEND=real API_AUTH_REQUIRED=false STARTUP_TIMEOUT_S="$STARTUP_TIMEOUT_S" \
  "$ROOT_DIR/scripts/start.sh"

translation_pid="$(cat "$RUNTIME_DIR/translation-worker.pid")"
speech_pid="$(cat "$RUNTIME_DIR/speech-worker.pid")"
coordinator_pid="$(cat "$RUNTIME_DIR/coordinator.pid")"
printf 'worker_pids translation=%s speech=%s coordinator=%s\n' "$translation_pid" "$speech_pid" "$coordinator_pid"

"$ROOT_DIR/.venv/bin/python" - "$translation_pid" "$speech_pid" "$coordinator_pid" <<'PY'
from __future__ import annotations
import subprocess, sys
translation_pid, speech_pid, coordinator_pid = map(int, sys.argv[1:])
gpus = {}
for line in subprocess.check_output([
    "nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader,nounits"
], text=True).splitlines():
    index, uuid = [part.strip() for part in line.split(",", 1)]
    gpus[uuid] = int(index)
apps = {}
raw = subprocess.check_output([
    "nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader,nounits"
], text=True).strip()
for line in raw.splitlines() if raw else []:
    uuid, pid = [part.strip() for part in line.split(",", 1)]
    apps[int(pid)] = gpus[uuid]
if apps.get(translation_pid) != 0:
    raise SystemExit(f"translation worker is not owned by physical GPU0: {apps}")
if apps.get(speech_pid) != 1:
    raise SystemExit(f"speech worker is not owned by physical GPU1: {apps}")
if coordinator_pid in apps:
    raise SystemExit(f"CPU coordinator unexpectedly owns a GPU: {apps}")
print(f"gpu_process_map={apps}")
print("gpu_ownership=PASS")
PY

printf '%s\n' '=== Task 12 residency snapshot ==='
nvidia-smi --query-gpu=index,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits

SEQUENTIAL_RUNS="${SEQUENTIAL_RUNS:-3}" \
RUN_CONCURRENT_QUALIFICATION="${RUN_CONCURRENT_QUALIFICATION:-true}" \
  "$ROOT_DIR/scripts/benchmark_pipeline.sh"

for spec in "translation-worker:$translation_pid" "speech-worker:$speech_pid" "coordinator:$coordinator_pid"; do
  name="${spec%%:*}"; pid="${spec##*:}"
  current="$(cat "$RUNTIME_DIR/$name.pid")"
  [[ "$current" == "$pid" ]] || { echo "$name PID changed: $pid -> $current" >&2; exit 1; }
  kill -0 "$pid" 2>/dev/null || { echo "$name exited during benchmark" >&2; exit 1; }
done
printf '%s\n' 'worker_pid_survival=PASS'

"$ROOT_DIR/.venv/bin/python" - "$RESULTS" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"concurrency_2_qualified={str(bool(payload['concurrent']['qualified'])).lower()}")
if payload["concurrent"].get("error"):
    print(f"concurrency_2_error={payload['concurrent']['error']}")
PY

printf '%s\n' '=== Task 12 GPU after benchmark ==='
nvidia-smi --query-gpu=index,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits

cleanup
trap - EXIT
sleep 2
printf '%s\n' '=== Task 12 GPU after cleanup ==='
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader,nounits
while IFS= read -r used; do
  used="${used// /}"
  [[ "$used" -le "$BASELINE_GPU_MAX_USED_MIB" ]] || { echo "GPU cleanup failed: ${used} MiB" >&2; exit 1; }
done < <(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
"$ROOT_DIR/.venv/bin/python" - <<'PY'
from en_vi_speech_api.coordinator.lifecycle import ports_are_free
if not ports_are_free((8090, 8091, 8092)):
    raise SystemExit("ports 8090-8092 were not released")
print("cleanup_ports=PASS")
PY
printf '%s\n' 'ACCEPTANCE_PIPELINE=PASS'
