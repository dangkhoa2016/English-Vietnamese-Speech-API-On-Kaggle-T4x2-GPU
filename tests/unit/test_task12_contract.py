from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_task12_scripts_exist_and_are_valid_bash() -> None:
    for relative in ("scripts/acceptance_pipeline.sh", "scripts/benchmark_pipeline.sh"):
        path = ROOT / relative
        assert path.is_file(), relative
        subprocess.run(["bash", "-n", str(path)], check=True)


def test_acceptance_pipeline_owns_lifecycle_and_cleanup_contract() -> None:
    text = (ROOT / "scripts/acceptance_pipeline.sh").read_text(encoding="utf-8")
    for required in (
        "BASELINE_GPU_MAX_USED_MIB",
        'STARTUP_TIMEOUT_S="${STARTUP_TIMEOUT_S:-900}"',
        "scripts/start.sh",
        "scripts/stop.sh",
        "benchmark_pipeline.sh",
        "worker_pid_survival=PASS",
        "gpu_ownership=PASS",
        "cleanup_ports=PASS",
        "ACCEPTANCE_PIPELINE=PASS",
    ):
        assert required in text


def test_benchmark_pipeline_records_sequential_and_concurrent_evidence() -> None:
    text = (ROOT / "scripts/benchmark_pipeline.sh").read_text(encoding="utf-8")
    for required in (
        "SEQUENTIAL_RUNS",
        "RUN_CONCURRENT_QUALIFICATION",
        "results.json",
        "translate-and-speak",
        "transcriptions",
        "speech",
        "/internal/translate",
        "concurrent",
    ):
        assert required in text


def test_kaggle_startup_timeout_tolerates_cold_attached_storage() -> None:
    start_text = (ROOT / "scripts/start.sh").read_text(encoding="utf-8")
    acceptance_text = (ROOT / "scripts/acceptance_pipeline.sh").read_text(encoding="utf-8")
    notebook = json.loads(
        (ROOT / "notebooks/kaggle-production-showcase.ipynb").read_text(encoding="utf-8")
    )
    notebook_source = "\n".join(
        "".join(cell.get("source", [])) for cell in notebook.get("cells", [])
    )

    assert 'STARTUP_TIMEOUT_S="${STARTUP_TIMEOUT_S:-900}"' in start_text
    assert 'STARTUP_TIMEOUT_S="${STARTUP_TIMEOUT_S:-900}"' in acceptance_text
    assert '"STARTUP_TIMEOUT_S": os.getenv("STARTUP_TIMEOUT_S", "900")' in notebook_source
    assert (
        '"STARTUP_PROGRESS_INTERVAL_S": os.getenv("ENVI_STARTUP_PROGRESS_INTERVAL_S", "15")'
        in notebook_source
    )


def test_start_script_stages_model_workers_to_avoid_cold_io_contention() -> None:
    text = (ROOT / "scripts/start.sh").read_text(encoding="utf-8")
    assert 'STARTUP_MODE="${ENVI_STARTUP_MODE:-sequential}"' in text
    parallel = text.split('if [[ "$STARTUP_MODE" == "parallel" ]]; then', 1)[1].split(
        "\nelse\n", 1
    )[0]
    sequential = text.split("\nelse\n", 1)[1].split("\nfi\n", 1)[0]
    assert parallel.index("start_one speech-worker") < parallel.index(
        "wait_ready translation-worker"
    )
    assert (
        sequential.index("start_one translation-worker")
        < sequential.index("wait_ready translation-worker")
        < sequential.index("start_one speech-worker")
        < sequential.index("wait_ready speech-worker")
    )
    coordinator_start = text.index("start_one coordinator")
    coordinator_ready = text.index("wait_ready coordinator")
    assert coordinator_start < coordinator_ready


def test_concurrency_qualification_uses_distinct_audio_inputs() -> None:
    text = (ROOT / "scripts/benchmark_pipeline.sh").read_text(encoding="utf-8")
    assert 'secondary_concurrent_fixture = out_dir / "speech-en.wav"' in text
    assert 'pool.submit(flagship, "concurrent-1", fixture)' in text
    assert 'pool.submit(flagship, "concurrent-2", secondary_concurrent_fixture)' in text
    assert "len(transcripts) == 2" in text
    assert "len(translations) == 2" in text
