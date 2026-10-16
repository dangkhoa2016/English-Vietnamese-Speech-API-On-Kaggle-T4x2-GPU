from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "notebooks/kaggle-production-showcase.ipynb"
BOOTSTRAP = ROOT / "scripts/bootstrap_kaggle.sh"


def load_notebook() -> dict:
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def test_notebook_first_cell_is_attached_model_guide() -> None:
    notebook = load_notebook()
    first = notebook["cells"][0]
    source = "".join(first["source"])
    assert first["cell_type"] == "markdown"
    for required in (
        "ATTACH MODELS BEFORE RUN ALL",
        "TranslateGemma 4B IT",
        "Whisper Large V3 Turbo",
        "VoxCPM2",
        "GPU T4 x2",
    ):
        assert required in source


def test_notebook_covers_production_showcase_flow() -> None:
    source = "\n".join("".join(cell.get("source", [])) for cell in load_notebook()["cells"])
    for required in (
        "git rev-parse HEAD",
        "scripts/preflight.sh",
        "pytest",
        "scripts/start.sh",
        "/v1/audio/transcriptions",
        "/v1/audio/speech",
        "/v1/audio/translate-and-speak",
        "scripts/benchmark_pipeline.sh",
        "ENABLE_CLOUDFLARE_TUNNEL",
        "scripts/run_tunnel.sh",
        "scripts/stop.sh",
        "nvidia-smi",
    ):
        assert required in source


def test_notebook_python_cells_parse() -> None:
    for index, cell in enumerate(load_notebook()["cells"]):
        if cell["cell_type"] != "code":
            continue
        ast.parse("".join(cell["source"]), filename=f"cell-{index}")


def test_bootstrap_pins_qualified_model_runtimes() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for required in (
        "jax[cuda12-local]==0.7.2",
        "keras==3.13.2",
        "keras-hub==0.26.0",
        "f772e498a45fbb5fb8e13fbf9b9c48be9fe33e69",
        ".venv-speech",
        "python-multipart==0.0.32",
    ):
        assert required in text
    subprocess.run(["bash", "-n", str(BOOTSTRAP)], check=True)


def test_showcase_notebooks_have_stable_ids_and_matching_sources() -> None:
    executed_path = ROOT / "notebooks/kaggle-production-showcase-executed.ipynb"
    source_nb = load_notebook()
    executed_nb = json.loads(executed_path.read_text(encoding="utf-8"))

    assert len(source_nb["cells"]) == len(executed_nb["cells"])
    assert all(cell.get("id") for cell in source_nb["cells"])
    assert [cell["id"] for cell in source_nb["cells"]] == [
        cell["id"] for cell in executed_nb["cells"]
    ]
    assert [cell.get("source", []) for cell in source_nb["cells"]] == [
        cell.get("source", []) for cell in executed_nb["cells"]
    ]
