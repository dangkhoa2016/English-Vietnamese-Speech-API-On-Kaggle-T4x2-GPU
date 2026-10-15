#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${BENCHMARK_OUT_DIR:-$ROOT_DIR/runtime/benchmark-pipeline}"
RESULTS="$OUT_DIR/results.json"
FIXTURE="$ROOT_DIR/data/fixtures/english-short.wav"
SEQUENTIAL_RUNS="${SEQUENTIAL_RUNS:-3}"
RUN_CONCURRENT_QUALIFICATION="${RUN_CONCURRENT_QUALIFICATION:-true}"
mkdir -p "$OUT_DIR"

curl -fsS http://127.0.0.1:8090/health/live >/dev/null

"$ROOT_DIR/.venv/bin/python" - "$ROOT_DIR" "$OUT_DIR" "$RESULTS" "$FIXTURE" "$SEQUENTIAL_RUNS" "$RUN_CONCURRENT_QUALIFICATION" <<'PY'
from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

root = Path(sys.argv[1])
out_dir = Path(sys.argv[2])
results_path = Path(sys.argv[3])
fixture = Path(sys.argv[4])
sequential_runs = int(sys.argv[5])
run_concurrent = sys.argv[6].lower() in {"1", "true", "yes", "on"}
expected_members = {"transcript.en.txt", "translation.vi.txt", "speech.vi.wav", "metadata.json"}


def curl(args: list[str]) -> tuple[bytes, float]:
    started = time.perf_counter()
    proc = subprocess.run(["curl", "-fsS", *args], check=True, capture_output=True)
    return proc.stdout, (time.perf_counter() - started) * 1000


def flagship(name: str, audio_path: Path) -> dict:
    archive_path = out_dir / f"{name}.zip"
    _, client_ms = curl([
        "-F", f"file=@{audio_path};type=audio/wav",
        "http://127.0.0.1:8090/v1/audio/translate-and-speak",
        "-o", str(archive_path),
    ])
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        if names != expected_members:
            raise RuntimeError(f"{name}: unexpected ZIP members: {sorted(names)}")
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        transcript = archive.read("transcript.en.txt").decode("utf-8").strip()
        translation = archive.read("translation.vi.txt").decode("utf-8").strip()
    if not transcript or not translation:
        raise RuntimeError(f"{name}: empty transcript/translation")
    return {
        "name": name,
        "client_total_ms": round(client_ms, 3),
        "request_id": metadata["request_id"],
        "timings_ms": metadata["timings_ms"],
        "normalized_audio_duration_s": metadata["normalized_audio_duration_s"],
        "output_audio": metadata["output_audio"],
        "models": metadata["models"],
        "transcript": transcript,
        "translation": translation,
    }


def json_request(args: list[str]) -> tuple[dict, float]:
    payload, client_ms = curl(args)
    return json.loads(payload.decode("utf-8")), round(client_ms, 3)


def speech(language: str, text: str) -> dict:
    text_path = out_dir / f"speech-{language}.txt"
    wav_path = out_dir / f"speech-{language}.wav"
    headers_path = out_dir / f"speech-{language}.headers"
    text_path.write_text(text, encoding="utf-8")
    started = time.perf_counter()
    subprocess.run([
        "curl", "-fsS", "-D", str(headers_path),
        "-F", f"file=@{text_path};type=text/plain",
        "-F", f"language={language}",
        "http://127.0.0.1:8090/v1/audio/speech",
        "-o", str(wav_path),
    ], check=True, capture_output=True)
    client_ms = round((time.perf_counter() - started) * 1000, 3)
    if wav_path.stat().st_size <= 44:
        raise RuntimeError(f"{language} speech output is empty")
    return {"language": language, "client_total_ms": client_ms, "bytes": wav_path.stat().st_size}


warmup = flagship("warmup", fixture)
sequential = [flagship(f"sequential-{i}", fixture) for i in range(1, sequential_runs + 1)]

transcription, transcription_ms = json_request([
    "-F", f"file=@{fixture};type=audio/wav",
    "http://127.0.0.1:8090/v1/audio/transcriptions",
])
translation, translation_ms = json_request([
    "-H", "Content-Type: application/json",
    "-d", json.dumps({
        "text": "Artificial intelligence can help people communicate across languages.",
        "source_language": "en",
        "target_language": "vi",
    }),
    "http://127.0.0.1:8091/internal/translate",
])
standalone = {
    "transcription": {"client_total_ms": transcription_ms, "response": transcription},
    "translation": {"client_total_ms": translation_ms, "response": translation},
    "speech_en": speech("en", "Hello from the English benchmark request."),
    "speech_vi": speech("vi", "Xin chào từ yêu cầu kiểm thử tiếng Việt."),
}
secondary_concurrent_fixture = out_dir / "speech-en.wav"

concurrent = {"attempted": run_concurrent, "qualified": False, "runs": [], "error": None}
if run_concurrent:
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(flagship, "concurrent-1", fixture),
                pool.submit(flagship, "concurrent-2", secondary_concurrent_fixture),
            ]
            runs = [future.result() for future in as_completed(futures)]
        ids = {run["request_id"] for run in runs}
        transcripts = {run["transcript"] for run in runs}
        translations = {run["translation"] for run in runs}
        by_name = {run["name"]: run for run in runs}
        concurrent["runs"] = sorted(runs, key=lambda item: item["name"])
        concurrent["qualified"] = (
            len(runs) == 2
            and len(ids) == 2
            and len(transcripts) == 2
            and len(translations) == 2
            and by_name["concurrent-1"]["transcript"] == warmup["transcript"]
            and by_name["concurrent-2"]["transcript"] != warmup["transcript"]
        )
        if not concurrent["qualified"]:
            concurrent["error"] = "distinct-input request IDs/artifact pairing did not qualify"
    except Exception as exc:  # qualification failure is evidence, not a harness crash
        concurrent["error"] = f"{type(exc).__name__}: {exc}"

stage_keys = ("asr", "translation", "tts", "total")
summary = {
    key: {
        "mean_ms": round(statistics.mean(float(run["timings_ms"][key]) for run in sequential), 3),
        "min_ms": round(min(float(run["timings_ms"][key]) for run in sequential), 3),
        "max_ms": round(max(float(run["timings_ms"][key]) for run in sequential), 3),
    }
    for key in stage_keys
}
result = {
    "warmup": warmup,
    "sequential": sequential,
    "sequential_summary": summary,
    "standalone": standalone,
    "concurrent": concurrent,
}
results_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"sequential_summary": summary, "concurrent": concurrent}, ensure_ascii=False, indent=2))
print(f"results_json={results_path}")
print("BENCHMARK_PIPELINE=PASS")
PY
