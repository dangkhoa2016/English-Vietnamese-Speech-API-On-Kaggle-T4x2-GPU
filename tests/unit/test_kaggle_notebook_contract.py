from __future__ import annotations

import json
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


def test_notebook_has_single_six_case_gallery() -> None:
    cells = load_notebook()["cells"]
    all_sources = "\n".join("".join(c.get("source", [])) for c in cells)
    gallery_cells = [
        "".join(c["source"])
        for c in cells
        if c["cell_type"] == "code" and "SCENARIO_GALLERY_COUNT=6" in "".join(c["source"])
    ]
    assert len(gallery_cells) == 1
    gallery = gallery_cells[0]
    for slug in (
        "en-customer",
        "en-business",
        "en-travel",
        "vi-healthcare",
        "vi-banking",
        "vi-education",
    ):
        assert f'"{slug}"' in gallery
    assert "for slug in case_slugs:" in gallery
    assert "len(scenario_summary) == 6" in gallery
    assert 'len({row["request_id"] for row in scenario_summary}) == 6' in gallery
    assert "Step 10B" not in all_sources
    assert "SCENARIO_COUNT=6" in gallery
    assert "data/showcase/acceptance-manifest.json" in gallery
    assert "display(Audio(filename=str(original)))" in gallery
    assert "display(Audio(filename=str(output_path)))" in gallery
    assert "base64" not in all_sources.lower()


def test_notebook_documents_runtime_wheelhouse_and_audio_quality_evidence() -> None:
    notebook = load_notebook()
    first = "".join(notebook["cells"][0]["source"])
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    for required in (
        "english-vietnamese-speech-api-qualified-runtime",
        "qualified runtime",
        "RUNTIME_SOURCE",
        "official package indexes",
        "vendor",
    ):
        assert required in first or required in source


def test_showcase_source_files_match_exactly_six_active_scenarios() -> None:
    root = ROOT / "data/showcase"
    manifest = json.loads((root / "acceptance-manifest.json").read_text(encoding="utf-8"))
    samples = manifest["validated_samples"]
    assert set(samples) == set(manifest["active_scenario_slugs"])
    assert len(samples) == 6
    assert {p.name for p in root.glob("*.wav")} == {x["file"] for x in samples.values()}
    assert {p.name for p in root.glob("*.txt")} == {f"{slug}.txt" for slug in samples}


def test_redundant_legacy_flagship_audio_is_not_generated() -> None:
    cells = load_notebook()["cells"]
    source = "\n".join("".join(c.get("source", [])) for c in cells)
    assert "SOURCE_GALLERY_PRECHECK=PASS" in source
    assert "VERIFIED_SOURCE_AUDIO_COUNT=6" in source
    assert "display(Audio(filename=str(original)))" in source
    assert "display(Audio(filename=str(output_path)))" in source


def test_bootstrap_prefers_single_attached_runtime_archive() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for required in (
        "english-vietnamese-speech-api-qualified-runtime",
        "envi-speech-runtime-v1.bundle",
        "RUNTIME_ARCHIVE",
        "RUNTIME_EXTRACT_ROOT",
        "RUNTIME_SOURCE=KAGGLE_SINGLE_ARCHIVE",
        "RUNTIME_SOURCE=INTERNET_FALLBACK",
        'tar -xf "$RUNTIME_ARCHIVE"',
        "translation-requirements.txt",
        "speech-public-requirements.txt",
        "speech-vendor-requirements.txt",
        "build-requirements.txt",
        "editables==0.5",
    ):
        assert required in text


def test_bootstrap_puts_runtime_envs_and_caches_under_tmp() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for required in (
        'RUNTIME_EXTRACT_ROOT="${RUNTIME_EXTRACT_ROOT:-/tmp/envi-speech-runtime-v1}"',
        'ENV_ROOT="${ENV_ROOT:-/tmp/envi-speech-envs}"',
        'TRANSLATION_ENV="${TRANSLATION_ENV:-$ENV_ROOT/translation}"',
        'SPEECH_ENV="${SPEECH_ENV:-$ENV_ROOT/speech}"',
        'XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/envi-speech-cache}"',
        'HF_HOME="${HF_HOME:-$XDG_CACHE_HOME/huggingface}"',
        'TORCH_HOME="${TORCH_HOME:-$XDG_CACHE_HOME/torch}"',
        'KERAS_HOME="${KERAS_HOME:-$XDG_CACHE_HOME/keras}"',
        "--no-cache-dir",
        "TMP_RUNTIME_LAYOUT=PASS",
    ):
        assert required in text
    for forbidden in (
        "$ROOT_DIR/.venv/bin/python",
        "$ROOT_DIR/.venv-speech/bin/python",
        "/kaggle/working/envi-speech-api-pytorch-cu128-wheels",
    ):
        assert forbidden not in text


def test_bootstrap_uses_extracted_public_and_pytorch_wheelhouses() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for required in (
        'RUNTIME_WHEELHOUSE="${RUNTIME_WHEELHOUSE:-$RUNTIME_ROOT/wheelhouse}"',
        'RUNTIME_PYTORCH_DIR="${RUNTIME_PYTORCH_DIR:-$RUNTIME_ROOT/pytorch-cu128-wheels}"',
        '--find-links "$RUNTIME_WHEELHOUSE"',
        '--find-links "$RUNTIME_PYTORCH_DIR"',
        'pip_install_speech_local "$SPEECH_ENV/bin/python" -r "$SPEECH_PUBLIC_MANIFEST"',
    ):
        assert required in text


def test_notebook_documents_single_archive_and_tmp_runtime_layout() -> None:
    source = "\n".join("".join(cell.get("source", [])) for cell in load_notebook()["cells"])
    for required in (
        "envi-speech-runtime-v1.bundle",
        "/tmp/envi-speech-runtime-v1",
        "/tmp/envi-speech-envs/translation",
        "/tmp/envi-speech-envs/speech",
        "/tmp/envi-speech-cache",
        "TMP_RUNTIME_LAYOUT=PASS",
    ):
        assert required in source
    assert "pytorch-cu128-wheels.zip" not in source
    assert "staging local dưới `/kaggle/working`" not in source


def test_notebook_pins_runtime_dataset_version_1() -> None:
    source = "\n".join("".join(cell.get("source", [])) for cell in load_notebook()["cells"])
    assert "english-vietnamese-speech-api-qualified-runtime" in source
    assert "qualified-runtime` **Version 1**" in source
    assert "qualified-runtime` **Version 3**" not in source


def test_release_docs_pin_runtime_dataset_version_1() -> None:
    for relative in (
        "docs/GETTING_STARTED.md",
        "docs/GETTING_STARTED.vi.md",
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


def test_production_showcase_uses_fresh_release_checkout_and_rejects_stale_working_venvs() -> None:
    notebook = load_notebook()
    code_cells = [
        "".join(cell.get("source", [])) for cell in notebook["cells"] if cell["cell_type"] == "code"
    ]
    bootstrap_cell = next(code for code in code_cells if "bootstrap_kaggle.sh" in code)
    setup_cell = code_cells[0]
    attachment_cell = code_cells[1]

    for required in (
        'RELEASE_REF = os.getenv("ENVI_SOURCE_REF", "main").strip()',
        'EXPECTED_SOURCE_COMMIT = os.getenv("ENVI_EXPECTED_SOURCE_COMMIT", "").strip().lower()',
        "SOURCE_COMMIT_PIN=PASS",
        "EXISTING_CHECKOUT_PRESERVED=",
        "SOURCE_COMMIT_PIN=UNPINNED_REPRODUCIBILITY_NOT_GUARANTEED",
        '"--branch"',
        "RELEASE_REF",
        '"--single-branch"',
        'print("SOURCE_COMMIT="',
    ):
        assert required in setup_cell

    for required in (
        "envi-speech-runtime-v1.bundle",
        'print("RUNTIME_ARCHIVE=PASS")',
        'print("WORKING_VENV_COUNT=0")',
    ):
        assert required in attachment_cell

    assert 'bootstrap_env["REQUIRE_RUNTIME_DATASET"] = "true"' in bootstrap_cell
    assert 'print("KAGGLE_WORKING_RUNTIME_BYTES="' in bootstrap_cell


def test_bootstrap_can_fail_closed_when_qualified_runtime_archive_is_required() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for required in (
        'REQUIRE_RUNTIME_DATASET="${REQUIRE_RUNTIME_DATASET:-false}"',
        'if [[ "${REQUIRE_RUNTIME_DATASET,,}" == "true" && ! -f "$RUNTIME_ARCHIVE" ]]; then',
        "RUNTIME_DATASET_REQUIRED=FAIL",
    ):
        assert required in text


def test_bootstrap_checks_required_runtime_archive_before_environment_backend_selection() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    archive_guard = text.index("RUNTIME_DATASET_REQUIRED=FAIL")
    backend_selection = text.index("BOOTSTRAP_VENV_BACKEND=uv")
    assert archive_guard < backend_selection


def test_production_showcase_prints_runtime_mount_diagnostics_before_failing() -> None:
    notebook = load_notebook()
    code_cells = [
        "".join(cell.get("source", [])) for cell in notebook["cells"] if cell["cell_type"] == "code"
    ]
    attachment_cell = code_cells[1]
    for required in (
        'print("RUNTIME_ARCHIVE_EXPECTED="',
        'print("RUNTIME_ARCHIVE_EXISTS="',
        'print("KAGGLE_INPUT_TOP_LEVEL="',
        'print("QUALIFIED_RUNTIME_CANDIDATES="',
        'print("RUNTIME_DATASET_REQUIRED=FAIL")',
    ):
        assert required in attachment_cell


def test_production_showcase_docs_do_not_advertise_internet_fallback() -> None:
    notebook = load_notebook()
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    assert "Internet-only installation remains a fallback" not in source
    assert "Nếu Dataset chưa attach thì mới dùng Internet-only fallback" not in source


def test_bootstrap_resolves_namespaced_kaggle_dataset_mounts() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for required in (
        'KAGGLE_INPUT_ROOT="${KAGGLE_INPUT_ROOT:-/kaggle/input}"',
        'RUNTIME_DATASET_OWNER="${RUNTIME_DATASET_OWNER:-dangkhoa2016}"',
        '"$KAGGLE_INPUT_ROOT/datasets/$RUNTIME_DATASET_OWNER/$RUNTIME_DATASET_SLUG/$RUNTIME_ARCHIVE_NAME"',
        'find "$KAGGLE_INPUT_ROOT/datasets"',
        'echo "RUNTIME_DATASET_LAYOUT=$RUNTIME_DATASET_LAYOUT"',
    ):
        assert required in text


def test_production_showcase_resolves_and_propagates_namespaced_runtime_archive() -> None:
    notebook = load_notebook()
    code_cells = [
        "".join(cell.get("source", [])) for cell in notebook["cells"] if cell["cell_type"] == "code"
    ]
    attachment_cell = code_cells[1]
    bootstrap_cell = next(code for code in code_cells if "bootstrap_kaggle.sh" in code)

    for required in (
        'Path("/kaggle/input/datasets")',
        '"dangkhoa2016"',
        "rglob(runtime_archive_name)",
        'print("RUNTIME_DATASET_LAYOUT="',
    ):
        assert required in attachment_cell

    assert 'bootstrap_env["RUNTIME_ARCHIVE"] = str(runtime_archive)' in bootstrap_cell


def test_public_project_materials_use_audience_neutral_showcase_framing() -> None:
    public_paths = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix in {".md", ".ipynb"}
        and ".git" not in path.parts
        and "tests" not in path.parts
    ]
    audience_term = "review" + "er"
    retired_evidence_phrases = (
        "fresh " + "executed production evidence",
        "fresh " + "executed demo evidence",
        "executed production evidence:",
        "generated and published separately from a real Kaggle T4 x2 run",
        "generated separately from a real Kaggle T4 x2 run",
        "được tạo riêng từ một lần chạy Kaggle T4 x2 thật",
        "được tạo/publish riêng từ một lần chạy Kaggle T4 x2 thật",
    )

    for path in public_paths:
        content = path.read_text(encoding="utf-8").lower()
        assert audience_term not in content, path
        for phrase in retired_evidence_phrases:
            assert phrase.lower() not in content, (path, phrase)


def test_bootstrap_prefers_uv_without_apt_venv_bootstrap_and_reports_phase_timers() -> None:
    source = (ROOT / "scripts" / "bootstrap_kaggle.sh").read_text(encoding="utf-8")

    assert 'UV_BIN="${UV_BIN:-$(command -v uv || true)}"' in source
    assert "BOOTSTRAP_VENV_BACKEND=uv" in source
    assert "uv venv" in source or '"$UV_BIN" venv' in source
    assert '"$UV_BIN" pip install' in source
    assert "apt-get" not in source
    assert "python3.12-venv" not in source

    for marker in (
        "RUNTIME_ARCHIVE_EXTRACT_SECONDS=",
        "TRANSLATION_ENV_CREATE_SECONDS=",
        "TRANSLATION_INSTALL_SECONDS=",
        "SPEECH_ENV_CREATE_SECONDS=",
        "SPEECH_VENDOR_INSTALL_SECONDS=",
        "SPEECH_PUBLIC_INSTALL_SECONDS=",
        "BOOTSTRAP_TOTAL_SECONDS=",
    ):
        assert marker in source


def test_readmes_are_project_landing_pages_not_operational_runbooks() -> None:
    readmes = {
        "README.md": "docs/GETTING_STARTED.md",
        "README.vi.md": "docs/GETTING_STARTED.vi.md",
    }
    forbidden = (
        "bash scripts/bootstrap_kaggle.sh",
        "bash scripts/preflight.sh",
        "bash scripts/start.sh",
        "bash scripts/acceptance_pipeline.sh",
        "bash scripts/benchmark_pipeline.sh",
        "API_AUTH_REQUIRED=true",
        "ENABLE_CLOUDFLARE_TUNNEL=true",
        "ruff check .",
        "pytest -q",
        "force-with-lease",
        "repoint",
    )

    for relative, getting_started in readmes.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert getting_started in text, relative
        assert len(text.splitlines()) <= 180, relative
        for phrase in forbidden:
            assert phrase not in text, (relative, phrase)

    assert (ROOT / "docs/GETTING_STARTED.md").is_file()
    assert (ROOT / "docs/GETTING_STARTED.vi.md").is_file()


def test_production_gallery_uses_all_six_git_sources() -> None:
    source = "\n".join("".join(c.get("source", [])) for c in load_notebook()["cells"])
    assert "Step 10A" not in source
    assert "SCENARIO_GALLERY=PASS" in source
    assert "len(scenario_summary) == 6" in source
    assert "REVERSE_PIPELINE=PASS" in source
    assert 'os.getenv("ENVI_SHOWCASE_MODE", "quick")' in source
    assert 'if SHOWCASE_MODE == "full":' in source
    assert "display(Audio(filename=str(original)))" in source
    assert "display(Audio(filename=str(output_path)))" in source
    assert "data/showcase/acceptance-manifest.json" in source
    assert "base64" not in source.lower()


def test_standalone_voice_examples_are_persisted_separately() -> None:
    cells = load_notebook()["cells"]
    code = "\n".join("".join(c.get("source", [])) for c in cells if c["cell_type"] == "code")
    assert "voice-smoke-{language}.wav" in code
    assert "STANDALONE_VOICE_TESTS=PASS" in code
    assert "voice-smoke-tests.zip" in code
    assert "STANDALONE_VOICE_TESTS=2" in code
    assert "display(Audio(filename=str(wav_path)))" in code
    assert "voice-smoke-manifest.json" in code
    assert "sha256" in code


def test_notebook_exposes_checked_out_source_to_kernel() -> None:
    cells = load_notebook()["cells"]
    setup = "".join(cells[1]["source"])
    assert 'source_python = str(REPO / "src")' in setup
    assert "sys.path.insert(0, source_python)" in setup
    assert 'assert (REPO / "src/en_vi_speech_api/translation_worker/model.py").is_file()' in setup


def test_gallery_does_not_condition_on_scenario_to_score_translation() -> None:
    cells = load_notebook()["cells"]
    gallery = "\n".join(
        "".join(c["source"])
        for c in cells
        if c["cell_type"] == "code" and "SCENARIO_GALLERY_COUNT=6" in "".join(c["source"])
    )
    assert "def required_facts" not in gallery
    assert "if slug ==" not in gallery
    assert "SHOWCASE_SEMANTIC_FIDELITY=NOT_AUTOMATICALLY_VERIFIED" in gallery
    assert "fact_checks" not in gallery


def test_notebook_preserves_existing_user_checkout_and_opt_in_stitching() -> None:
    notebook = load_notebook()
    setup = "".join(notebook["cells"][1]["source"])
    startup = "".join(notebook["cells"][11]["source"])
    assert "shutil.rmtree(REPO)" not in setup
    assert "REPO_BASE.with_name" in setup
    assert "EXISTING_CHECKOUT_PRESERVED=" in setup
    assert 'os.getenv("ENVI_STITCH_VI_SENTENCES", "false")' in startup
    assert '"VOXCPM_VI_SENTENCE_STITCHING": STITCH_VI_SENTENCES' in startup
    assert 'VOXCPM_VI_SENTENCE_STITCHING=true" in worker_env' not in startup
