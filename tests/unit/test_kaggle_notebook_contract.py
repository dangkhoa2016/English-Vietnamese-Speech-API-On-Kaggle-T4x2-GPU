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


def test_notebook_first_cell_is_bilingual_attached_model_guide() -> None:
    notebook = load_notebook()
    first = notebook["cells"][0]
    source = "".join(first["source"])
    assert first["cell_type"] == "markdown"
    for required in (
        "Before you run / Trước khi chạy",
        "### English",
        "### Tiếng Việt",
        "Add Input",
        "GPU T4 x2",
        "TranslateGemma 4B IT",
        "Whisper Large V3 Turbo",
        "VoxCPM2",
        "/kaggle/input/models/keras/translategemma/keras/translategemma_4b_it/1",
        "/kaggle/input/models/dangkhoa2016/openai-whisper-large-v3-turbo/transformers/default/1",
        "/kaggle/input/models/dangkhoa2016/openbmb-voxcpm2/pytorch/default/1",
        "read-only",
        "/kaggle/working",
    ):
        assert required in source


def test_every_code_cell_has_bilingual_explanatory_markdown_immediately_before_it() -> None:
    cells = load_notebook()["cells"]
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        assert index > 0, f"code cell {index} cannot be first"
        previous = cells[index - 1]
        assert previous["cell_type"] == "markdown", f"code cell {index} lacks markdown guide"
        guide = "".join(previous.get("source", []))
        assert "### English" in guide, f"code cell {index} lacks English section"
        assert "### Tiếng Việt" in guide, f"code cell {index} lacks Vietnamese section"
        assert "**English:**" not in guide, f"code cell {index} uses mixed inline English label"
        assert "**Tiếng Việt:**" not in guide, (
            f"code cell {index} uses mixed inline Vietnamese label"
        )


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


def test_notebook_has_four_case_public_production_scenario_gallery() -> None:
    cells = load_notebook()["cells"]
    gallery_index = next(
        index
        for index, cell in enumerate(cells)
        if cell["cell_type"] == "markdown"
        and "Production Scenario Gallery" in "".join(cell.get("source", []))
    )
    gallery_guide = "".join(cells[gallery_index]["source"])
    gallery_code = "".join(cells[gallery_index + 1]["source"])

    assert cells[gallery_index + 1]["cell_type"] == "code"
    assert "### English" in gallery_guide
    assert "### Tiếng Việt" in gallery_guide
    for slug in (
        "customer-support",
        "technical-incident",
        "travel-hospitality",
        "business-update",
    ):
        assert slug in gallery_code

    for required in (
        "http://127.0.0.1:8090/v1/audio/speech",
        "http://127.0.0.1:8090/v1/audio/translate-and-speak",
        "transcript.en.txt",
        "translation.vi.txt",
        "speech.vi.wav",
        "metadata.json",
        "request_id",
        "timings_ms",
        "source_tts_ms",
        "scenario_summary",
        "display(Audio",
        "SCENARIO_GALLERY=PASS",
    ):
        assert required in gallery_code
    assert "8091/internal/translate" not in gallery_code


def test_notebook_python_cells_parse() -> None:
    for index, cell in enumerate(load_notebook()["cells"]):
        if cell["cell_type"] != "code":
            continue
        ast.parse("".join(cell["source"]), filename=f"cell-{index}")


def test_bootstrap_installs_python312_venv_when_ensurepip_is_missing() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "import ensurepip" in text
    assert "python3.12-venv" in text
    assert "apt-get -o Acquire::Retries=3 install" in text


def test_bootstrap_continues_after_partial_apt_update_failure(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    ensurepip_ready = tmp_path / "ensurepip-ready"
    apt_log = tmp_path / "apt.log"

    fake_python = fake_bin / "python3.12"
    fake_python.write_text(
        '#!/usr/bin/env bash\nif [[ -f "$ENSUREPIP_READY" ]]; then exit 0; fi\nexit 1\n',
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    fake_id = fake_bin / "id"
    fake_id.write_text("#!/usr/bin/env bash\nprintf '0\\n'\n", encoding="utf-8")
    fake_id.chmod(0o755)

    fake_apt = fake_bin / "apt-get"
    fake_apt.write_text(
        "#!/usr/bin/env bash\n"
        'printf \'%s\\n\' "$*" >> "$APT_LOG"\n'
        'if [[ " $* " == *" update "* || " $* " == *" update" ]]; then exit 100; fi\n'
        'if [[ " $* " == *" install "* ]]; then touch "$ENSUREPIP_READY"; exit 0; fi\n'
        "exit 2\n",
        encoding="utf-8",
    )
    fake_apt.chmod(0o755)

    extract_function = r"awk '/^ensure_python312_venv\(\)/,/^}/ {print}' " + str(BOOTSTRAP)
    harness = f'set -euo pipefail\neval "$({extract_function})"\nensure_python312_venv\n'
    env = {
        "PATH": f"{fake_bin}:/usr/bin:/bin",
        "PYTHON_312": str(fake_python),
        "ENSUREPIP_READY": str(ensurepip_ready),
        "APT_LOG": str(apt_log),
    }
    completed = subprocess.run(
        ["bash", "-c", harness],
        check=False,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    assert "APT_UPDATE_WARNING=continuing_after_partial_repository_failure" in completed.stdout
    assert "PYTHON312_VENV_READY=PASS" in completed.stdout
    calls = apt_log.read_text(encoding="utf-8")
    assert "Acquire::Retries=3 update -qq" in calls
    assert "Acquire::Retries=3 install -y -qq python3.12-venv" in calls


def test_bootstrap_pins_qualified_model_runtimes() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for required in (
        "jax[cuda12-local]==0.11.2",
        "keras==3.15.1",
        "keras-hub==0.32.0",
        "torch==2.11.0+cu128",
        "torchaudio==2.11.0+cu128",
        "https://download.pytorch.org/whl/cu128",
        "constraints-kaggle-tested.txt",
        "voxcpm==2.0.3",
        ".venv-speech",
        "python-multipart==0.0.32",
    ):
        assert required in text
    subprocess.run(["bash", "-n", str(BOOTSTRAP)], check=True)
    for obsolete in (
        "0.7.2",
        "3.13.2",
        "0.26.0",
        "2.10.0+cu128",
        "0.0.post1+gf772e498a",
        "f772e498a45fbb5fb8e13fbf9b9c48be9fe33e69",
    ):
        assert obsolete not in text


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


def test_notebook_documents_runtime_wheelhouse_and_audio_quality_evidence() -> None:
    notebook = load_notebook()
    first = "".join(notebook["cells"][0]["source"])
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    for required in (
        "english-vietnamese-speech-api-qualified-runtime",
        "qualified runtime",
        "RUNTIME_SOURCE",
        "RMS dBFS",
        "Peak dBFS",
        "official package indexes",
        "vendor",
    ):
        assert required in first or required in source


def test_flagship_pipeline_displays_english_source_audio_before_vietnamese_output() -> None:
    cells = load_notebook()["cells"]
    step_index = next(
        index
        for index, cell in enumerate(cells)
        if cell["cell_type"] == "markdown" and "Step 9" in "".join(cell.get("source", []))
    )
    code = "".join(cells[step_index + 1]["source"])
    assert "English source audio" in code
    assert "display(Audio(filename=str(fixture)))" in code
    assert "Vietnamese output audio" in code


def test_bootstrap_prefers_attached_qualified_runtime_wheelhouse() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for required in (
        "english-vietnamese-speech-api-qualified-runtime",
        "--no-index",
        "--find-links",
        "RUNTIME_SOURCE=KAGGLE_WHEELHOUSE_HYBRID",
        "RUNTIME_SOURCE=INTERNET_FALLBACK",
        "translation-requirements.txt",
        "speech-public-requirements.txt",
        "speech-vendor-requirements.txt",
        "build-requirements.txt",
        "editables==0.5",
    ):
        assert required in text


def test_notebook_pins_runtime_dataset_version_1() -> None:
    source = "\n".join("".join(cell.get("source", [])) for cell in load_notebook()["cells"])
    assert "english-vietnamese-speech-api-qualified-runtime" in source
    assert "qualified-runtime` **Version 1**" in source
    assert "qualified-runtime` **Version 3**" not in source


def test_release_docs_pin_runtime_dataset_version_1() -> None:
    for relative in (
        "README.md",
        "README.vi.md",
        "docs/KAGGLE.md",
        "docs/KAGGLE.vi.md",
        "RELEASE_NOTES_v1.0.0.md",
        "RELEASE_NOTES_v1.0.0.vi.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "english-vietnamese-speech-api-qualified-runtime" in text
        assert "qualified-runtime" in text, relative
        assert "Version 1" in text, relative
        assert "qualified-runtime`, Version 3" not in text, relative
        assert "qualified-runtime` Version 3" not in text, relative


def test_bootstrap_prefers_kaggle_expanded_pytorch_wheel_directory() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for required in (
        "pytorch-cu128-wheels",
        "RUNTIME_PYTORCH_DIR",
        "KAGGLE_EXPANDED_PYTORCH_DIR",
        '--find-links "$RUNTIME_PYTORCH_DIR"',
    ):
        assert required in text


def test_bootstrap_keeps_archive_extraction_as_local_staging_fallback() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for required in (
        "pytorch-cu128-wheels.zip",
        "RUNTIME_PYTORCH_ARCHIVE",
        "RUNTIME_PYTORCH_STAGING",
        "unzip -q",
        "/kaggle/working",
        "LOCAL_PYTORCH_ARCHIVE_FALLBACK",
    ):
        assert required in text


def test_bootstrap_uses_both_public_and_pytorch_wheelhouses_for_speech() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert "pip_install_speech_local" in text
    assert '--find-links "$RUNTIME_WHEELHOUSE"' in text
    assert '--find-links "$RUNTIME_PYTORCH_DIR"' in text
    assert (
        'pip_install_speech_local "$ROOT_DIR/.venv-speech/bin/python" -r "$SPEECH_PUBLIC_MANIFEST"'
        in text
    )


def test_bootstrap_prefers_expanded_pytorch_directory_before_archive_fallback() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    expanded = text.index('compgen -G "$RUNTIME_PYTORCH_DIR/*.whl"')
    archive = text.index('[[ -f "$RUNTIME_PYTORCH_ARCHIVE" ]]')
    assert expanded < archive
