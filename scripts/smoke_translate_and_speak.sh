#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/tmp/envi-speech-envs/translation/bin/python}"
RUNTIME_DIR="$ROOT_DIR/runtime/flagship-smoke"
ARTIFACT="$RUNTIME_DIR/translate-and-speak.zip"
mkdir -p "$RUNTIME_DIR"

cleanup() {
  "$ROOT_DIR/scripts/stop.sh" >/dev/null 2>&1 || true
}
trap cleanup EXIT

cleanup
sleep 1
printf '%s\n' '=== flagship baseline GPU ==='
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader,nounits

BASELINE_GPU_MAX_USED_MIB="${BASELINE_GPU_MAX_USED_MIB:-64}"
while IFS= read -r used; do
  used="${used// /}"
  if [[ "$used" -gt "$BASELINE_GPU_MAX_USED_MIB" ]]; then
    echo "GPU baseline is not clean (${used} MiB > ${BASELINE_GPU_MAX_USED_MIB} MiB); refusing flagship acceptance." >&2
    exit 3
  fi
done < <(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)

SPEECH_BACKEND=real TRANSLATION_BACKEND=real STARTUP_TIMEOUT_S=240 \
  "$ROOT_DIR/scripts/start.sh"

printf '%s\n' '=== service readiness ==='
"$ROOT_DIR/scripts/status.sh"
printf '%s\n' '=== resident GPU snapshot ==='
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader,nounits

curl -fsS \
  -D "$RUNTIME_DIR/response.headers" \
  -F "file=@$ROOT_DIR/data/fixtures/english-short.wav;type=audio/wav" \
  http://127.0.0.1:8090/v1/audio/translate-and-speak \
  -o "$ARTIFACT"

cat "$RUNTIME_DIR/response.headers"

"$PYTHON_BIN" - "$ARTIFACT" "$RUNTIME_DIR" <<'PY'
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

artifact = Path(sys.argv[1])
out_dir = Path(sys.argv[2]) / "extracted"
out_dir.mkdir(parents=True, exist_ok=True)
expected = {
    "transcript.en.txt",
    "translation.vi.txt",
    "speech.vi.wav",
    "metadata.json",
}
with zipfile.ZipFile(artifact) as archive:
    names = set(archive.namelist())
    if names != expected:
        raise SystemExit(f"unexpected ZIP members: {sorted(names)}")
    archive.extractall(out_dir)

transcript = (out_dir / "transcript.en.txt").read_text(encoding="utf-8").strip()
translation = (out_dir / "translation.vi.txt").read_text(encoding="utf-8").strip()
metadata = json.loads((out_dir / "metadata.json").read_text(encoding="utf-8"))
serialized = json.dumps(metadata, ensure_ascii=False)
if not transcript:
    raise SystemExit("empty English transcript")
if not translation:
    raise SystemExit("empty Vietnamese translation")
if "/kaggle/" in serialized or "/tmp/" in serialized:
    raise SystemExit("metadata leaked a private filesystem path")
for key in ("asr", "translation", "tts", "total"):
    if key not in metadata.get("timings_ms", {}):
        raise SystemExit(f"missing timing: {key}")
print(f"transcript_en={transcript!r}")
print(f"translation_vi={translation!r}")
print("metadata=" + json.dumps(metadata, ensure_ascii=False, sort_keys=True))
print("zip_contract=PASS")
PY

printf '%s\n' '=== speech.vi.wav ==='
ffprobe -v error \
  -show_entries stream=codec_name,sample_rate,channels \
  -show_entries format=duration,size \
  -of default=noprint_wrappers=1 \
  "$RUNTIME_DIR/extracted/speech.vi.wav"

printf '%s\n' '=== GPU after flagship request ==='
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader,nounits
printf '%s\n' 'FLAGSHIP_IN_PROCESS=PASS'

cleanup
trap - EXIT
sleep 2
printf '%s\n' '=== GPU after cleanup ==='
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader,nounits
"$PYTHON_BIN" - <<'PY'
from en_vi_speech_api.coordinator.lifecycle import ports_are_free
if not ports_are_free((8090, 8091, 8092)):
    raise SystemExit("ports 8090-8092 were not released")
print("cleanup_ports=PASS")
PY
printf '%s\n' 'SMOKE_TRANSLATE_AND_SPEAK=PASS'
