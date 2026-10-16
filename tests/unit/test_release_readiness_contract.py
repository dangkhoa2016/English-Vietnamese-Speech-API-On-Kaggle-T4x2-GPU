from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_release_core_artifacts_exist() -> None:
    for relative in (
        "docs/ARCHITECTURE.md",
        "docs/ARCHITECTURE.vi.md",
        "docs/API.md",
        "docs/API.vi.md",
        "docs/SECURITY.md",
        "docs/SECURITY.vi.md",
        "NOTICE.md",
        "THIRD_PARTY_NOTICES.md",
        "constraints-kaggle-tested.txt",
        ".github/workflows/ci.yml",
    ):
        assert (ROOT / relative).is_file(), relative


def test_architecture_docs_record_qualified_gpu_ownership_and_staged_startup() -> None:
    for relative in ("docs/ARCHITECTURE.md", "docs/ARCHITECTURE.vi.md"):
        text = _read(relative)
        for required in (
            "GPU 0",
            "TranslateGemma 4B IT",
            "KerasHub",
            "JAX",
            "GPU 1",
            "Whisper Large V3 Turbo",
            "VoxCPM2",
            "8090",
            "8091",
            "8092",
            "translation ready",
            "speech ready",
            "coordinator ready",
        ):
            assert required in text, (relative, required)


def test_api_docs_cover_public_contract_and_zip_members() -> None:
    for relative in ("docs/API.md", "docs/API.vi.md"):
        text = _read(relative)
        for required in (
            "/health/live",
            "/health/ready",
            "/v1/audio/transcriptions",
            "/v1/audio/speech",
            "/v1/audio/translate-and-speak",
            "transcript.en.txt",
            "translation.vi.txt",
            "speech.vi.wav",
            "metadata.json",
            "X-Request-ID",
        ):
            assert required in text, (relative, required)


def test_security_docs_describe_public_boundary_auth_and_tunnel_fail_closed_rule() -> None:
    for relative in ("docs/SECURITY.md", "docs/SECURITY.vi.md"):
        text = _read(relative)
        for required in (
            "127.0.0.1:8090",
            "127.0.0.1:8091",
            "127.0.0.1:8092",
            "API_AUTH_REQUIRED",
            "ENABLE_CLOUDFLARE_TUNNEL",
            "Bearer",
            "runtime/api_key.txt",
            "PUBLIC_MAX_INFLIGHT",
            "PUBLIC_MAX_PENDING",
        ):
            assert required in text, (relative, required)


def test_third_party_notices_preserve_upstream_model_licenses() -> None:
    text = _read("THIRD_PARTY_NOTICES.md")
    for required in (
        "TranslateGemma 4B IT",
        "Gemma Terms of Use",
        "Whisper Large V3 Turbo",
        "MIT",
        "VoxCPM2",
        "Apache-2.0",
        "19b6bf7590025418821a86dcb817504e0ad7e5df",
    ):
        assert required in text


def test_constraints_pin_the_retained_kaggle_runtime() -> None:
    text = _read("constraints-kaggle-tested.txt")
    for required in (
        "fastapi==0.143.2",
        "httpx==0.28.1",
        "python-multipart==0.0.32",
        "uvicorn==0.54.0",
        "pytest==9.1.1",
        "ruff==0.17.1",
        "jax==0.11.2",
        "jaxlib==0.11.2",
        "keras==3.15.1",
        "keras-hub==0.32.0",
        "torch==2.11.0+cu128",
        "torchaudio==2.11.0+cu128",
        "transformers==5.19.0",
        "soundfile==0.14.0",
        "librosa==1.0.0",
        "voxcpm==2.0.3",
    ):
        assert required in text


def test_ci_runs_cpu_only_release_quality_gate() -> None:
    text = _read(".github/workflows/ci.yml")
    for required in (
        "python-version: '3.12'",
        "constraints-kaggle-tested.txt",
        "sudo apt-get install -y ffmpeg",
        "ruff check .",
        "ruff format --check src tests",
        "pytest -q",
        "bash -n",
        "git diff --check",
    ):
        assert required in text
    assert "actions/checkout@v7" in text
    assert "actions/setup-python@v7" in text
    assert "scripts/start.sh" not in text
    assert "acceptance_pipeline.sh" not in text


def test_project_version_matches_initial_public_release() -> None:
    import tomllib

    project = tomllib.loads(_read("pyproject.toml"))["project"]
    assert project["version"] == "1.0.0"


def test_bilingual_readmes_present_release_entrypoints_and_evidence() -> None:
    common_readme_requirements = (
        "Kaggle T4x2",
        "TranslateGemma 4B IT",
        "Whisper Large V3 Turbo",
        "VoxCPM2",
        "/v1/audio/transcriptions",
        "/v1/audio/speech",
        "/v1/audio/translate-and-speak",
        "kaggle-production-showcase.ipynb",
        "docs/GETTING_STARTED",
        "docs/ARCHITECTURE",
        "docs/API",
        "docs/SECURITY",
        "docs/BENCHMARKS",
    )
    for relative in ("README.md", "README.vi.md"):
        text = _read(relative)
        for required in common_readme_requirements:
            assert required in text, (relative, required)

    assert "THIRD_PARTY_NOTICES.md" in _read("README.md")
    assert "THIRD_PARTY_NOTICES.vi.md" in _read("README.vi.md")

    for relative in ("docs/GETTING_STARTED.md", "docs/GETTING_STARTED.vi.md"):
        text = _read(relative)
        for required in (
            "scripts/bootstrap_kaggle.sh",
            "scripts/start.sh",
            "API_AUTH_REQUIRED=true",
        ):
            assert required in text, (relative, required)


def test_bilingual_kaggle_guides_explain_exact_model_attachment_and_mount_contract() -> None:
    for relative in (
        "docs/GETTING_STARTED.md",
        "docs/GETTING_STARTED.vi.md",
        "docs/KAGGLE.md",
        "docs/KAGGLE.vi.md",
    ):
        text = _read(relative)
        for required in (
            "Add Input",
            "/kaggle/input",
            "read-only",
            "/kaggle/working",
            "keras/translategemma",
            "dangkhoa2016/openai-whisper-large-v3-turbo",
            "dangkhoa2016/openbmb-voxcpm2",
            "translategemma_4b_it",
            "Transformers",
            "PyTorch",
            "Version",
        ):
            assert required in text, (relative, required)


def test_readmes_report_retained_evidence_without_overclaiming_quality() -> None:
    common = (
        "13,865 MiB",
        "6,871 MiB",
        "21,762.6 ms",
        "PUBLIC_MAX_INFLIGHT=2",
    )
    for relative in ("README.md", "README.vi.md"):
        text = _read(relative)
        for required in common:
            assert required in text, (relative, required)

    assert "Translation quality" in _read("README.md")
    assert "Chất lượng dịch" in _read("README.vi.md")


def test_repository_source_has_mit_license_without_relicensing_models() -> None:
    text = _read("LICENSE")
    assert "MIT License" in text
    assert "Copyright (c) 2026" in text
    notice = _read("NOTICE.md")
    assert "does **not** relicense third-party model weights" in notice


def test_bilingual_readmes_show_main_branch_ci_badge() -> None:
    badge = "actions/workflows/ci.yml/badge.svg?branch=main"
    for relative in ("README.md", "README.vi.md"):
        assert badge in _read(relative), relative


def test_mit_license_names_project_author_exactly() -> None:
    text = _read("LICENSE")
    assert "Copyright (c) 2026 Đăng Khoa <i.am@dangkhoa.dev>" in text


def test_github_community_governance_files_exist() -> None:
    required = (
        ".github/CODEOWNERS",
        ".github/CODE_OF_CONDUCT.md",
        ".github/CODE_OF_CONDUCT.vi.md",
        ".github/CONTRIBUTING.md",
        ".github/CONTRIBUTING.vi.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/PULL_REQUEST_TEMPLATE.vi.md",
        ".github/SECURITY.md",
        ".github/SECURITY.vi.md",
        ".github/SUPPORT.md",
        ".github/SUPPORT.vi.md",
        ".github/dependabot.yml",
        ".github/workflows/ci.yml",
        ".github/workflows/repository-audit.yml",
    )
    for relative in required:
        assert (ROOT / relative).is_file(), relative


def test_reviewer_documents_are_bilingual_and_cross_linked() -> None:
    pairs = (
        ("README.md", "README.vi.md"),
        ("NOTICE.md", "NOTICE.vi.md"),
        ("THIRD_PARTY_NOTICES.md", "THIRD_PARTY_NOTICES.vi.md"),
        ("MODEL_LICENSES.md", "MODEL_LICENSES.vi.md"),
        ("LICENSE-NOTES.md", "LICENSE-NOTES.vi.md"),
        ("CHANGELOG.md", "CHANGELOG.vi.md"),
        ("CONTRIBUTING.md", "CONTRIBUTING.vi.md"),
        ("CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.vi.md"),
        ("RELEASE_NOTES_v1.0.0.md", "RELEASE_NOTES_v1.0.0.vi.md"),
        ("docs/API.md", "docs/API.vi.md"),
        ("docs/ARCHITECTURE.md", "docs/ARCHITECTURE.vi.md"),
        ("docs/BENCHMARKS.md", "docs/BENCHMARKS.vi.md"),
        ("docs/SECURITY.md", "docs/SECURITY.vi.md"),
        ("docs/KAGGLE.md", "docs/KAGGLE.vi.md"),
        ("docs/REPRODUCIBILITY.md", "docs/REPRODUCIBILITY.vi.md"),
        ("docs/TROUBLESHOOTING.md", "docs/TROUBLESHOOTING.vi.md"),
        ("docs/RELEASE-EVIDENCE-v1.0.0.md", "docs/RELEASE-EVIDENCE-v1.0.0.vi.md"),
    )
    for english, vietnamese in pairs:
        assert (ROOT / english).is_file(), english
        assert (ROOT / vietnamese).is_file(), vietnamese
        assert f"[Tiếng Việt]({Path(vietnamese).name})" in _read(english), english
        assert f"[English]({Path(english).name})" in _read(vietnamese), vietnamese


def test_readme_header_matches_public_release_badge_contract() -> None:
    text = _read("README.md")
    for required in (
        "repository-audit.yml/badge.svg",
        "License-MIT-green.svg",
        "TranslateGemma",
        "Gemma%20Terms",
        "Whisper",
        "MIT",
        "VoxCPM2",
        "Apache--2.0",
        "Python-3.12",
        "Tesla%20T4%20x2",
        "Release-v1.0.0",
        "🌐 Language / Ngôn ngữ",
    ):
        assert required in text, required


def test_model_license_inventory_separates_source_and_weight_terms() -> None:
    for relative in ("MODEL_LICENSES.md", "MODEL_LICENSES.vi.md"):
        text = _read(relative)
        for required in (
            "TranslateGemma 4B IT",
            "google/translategemma-4b-it",
            "Gemma Terms of Use",
            "Whisper Large V3 Turbo",
            "openai/whisper-large-v3-turbo",
            "MIT",
            "VoxCPM2",
            "openbmb/VoxCPM2",
            "Apache-2.0",
            "19b6bf7590025418821a86dcb817504e0ad7e5df",
            "does not relicense",
        ):
            assert required in text, (relative, required)


def test_public_guides_avoid_editorial_readme_reorganization_language() -> None:
    public_docs = (
        "README.md",
        "README.vi.md",
        "docs/GETTING_STARTED.md",
        "docs/GETTING_STARTED.vi.md",
        "RELEASE_NOTES_v1.0.0.md",
        "RELEASE_NOTES_v1.0.0.vi.md",
    )
    forbidden = (
        "intentionally kept out of",
        "intentionally kept as",
        "README is intentionally",
        "được chủ đích tách khỏi",
        "được chủ đích giữ",
        "tách khỏi README",
    )

    for relative in public_docs:
        text = _read(relative)
        for phrase in forbidden:
            assert phrase not in text, (relative, phrase)
