# English–Vietnamese Speech API on Kaggle T4x2

<p align="center">
  <a href="https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/repository-audit.yml"><img alt="Repository Audit" src="https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/repository-audit.yml/badge.svg?branch=main"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
  <a href="MODEL_LICENSES.md"><img alt="TranslateGemma terms" src="https://img.shields.io/badge/TranslateGemma-Gemma%20Terms-orange.svg"></a>
  <a href="MODEL_LICENSES.md"><img alt="Whisper upstream license" src="https://img.shields.io/badge/Whisper-MIT-green.svg"></a>
  <a href="MODEL_LICENSES.md"><img alt="VoxCPM2 upstream license" src="https://img.shields.io/badge/VoxCPM2-Apache--2.0-orange.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
  <img alt="GPU" src="https://img.shields.io/badge/GPU-Tesla%20T4%20x2-76B900?logo=nvidia&logoColor=white">
  <img alt="Release" src="https://img.shields.io/badge/Release-v1.0.0-blue">
</p>

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](README.vi.md)

A reproducible research project and production-style demonstration for running **English ↔ Vietnamese speech translation**, with speech recognition, translation, and synthesized audio on a single Kaggle **Tesla T4 x2** session.

The system combines **Whisper Large V3 Turbo**, **TranslateGemma 4B IT**, and **VoxCPM2** behind one FastAPI coordinator while keeping model ownership explicit across two GPUs. The repository focuses on coexistence, runtime isolation, reproducibility, bounded concurrency, observable request flow, and transparent reporting of both strengths and limitations.

## Research focus

This project explores how three complementary speech and translation models can coexist on two widely available 16 GB Tesla T4 GPUs without per-request model swapping.

- **GPU 0** — TranslateGemma 4B IT via Keras 3 / KerasHub / JAX.
- **GPU 1** — Whisper Large V3 Turbo and VoxCPM2 in one persistent PyTorch worker.
- **CPU** — FastAPI coordinator, request validation, bounded admission control, health aggregation, and ZIP packaging.

The architecture intentionally separates the JAX and PyTorch runtimes and stages cold model loading to reduce storage and GPU contention.

## What the system provides

| Capability | Public endpoint |
| --- | --- |
| English or Vietnamese speech recognition | `POST /v1/audio/transcriptions` |
| English or Vietnamese text-to-speech | `POST /v1/audio/speech` |
| English ↔ Vietnamese audio translation and speech synthesis | `POST /v1/audio/translate-and-speak` |
| Liveness and readiness | `GET /health/live`, `GET /health/ready` |

The pipeline returns a ZIP containing `transcript.<source>.txt`, `translation.<target>.txt`, `speech.<target>.wav`, and `metadata.json`. Multipart `source_language` and `target_language` select `en → vi` (default) or `vi → en`. Coordinator responses include `X-Request-ID` for traceability.

## Architecture

```text
Client
  |
  v
Coordinator :8090 (CPU)
  |------------------------------|
  v                              v
Translation worker :8091         Speech worker :8092
GPU 0                            GPU 1
TranslateGemma 4B IT             Whisper Large V3 Turbo
KerasHub / JAX                   VoxCPM2
                                 PyTorch
```

Cold startup is staged as:

```text
translation ready → speech ready → coordinator ready
```

See [Architecture](docs/ARCHITECTURE.md) for the full process, GPU, and service contract.

## Qualified results

Retained Kaggle T4x2 acceptance evidence records:

- **13,865 MiB** model residency on GPU 0.
- **6,871 MiB** model residency on GPU 1.
- **21,762.6 ms** mean server-pipeline time across the retained three-request warm flagship benchmark.
- Two distinct concurrent flagship requests passed with `PUBLIC_MAX_INFLIGHT=2`, separate request IDs, correctly paired outputs, no worker restart, no OOM, and no cross-request artifact mixing.

These measurements describe the documented qualification environment; they are not universal performance guarantees. Translation quality is also not presented as universally solved: one retained TranslateGemma result contains mixed English/Vietnamese output and is documented as a real model-quality limitation.

See [Benchmarks and acceptance evidence](docs/BENCHMARKS.md) for detailed methodology, timings, and caveats.

## Production showcase

[`notebooks/kaggle-production-showcase.ipynb`](notebooks/kaggle-production-showcase.ipynb) is the interactive demonstration of the complete system. It covers attached-input validation, runtime qualification checks, staged model startup, the public API paths, six bilingual scenarios, bounded benchmarking, and cleanup.

People who do not write code can still use the notebook to understand the architecture, inspect scenarios, and listen to generated audio. Developers and researchers can use the same source notebook to reproduce or extend the system.

## Getting started

Detailed setup, Kaggle inputs, runtime bootstrap, API examples, acceptance runs, benchmark commands, optional tunnel use, and local quality checks are intentionally kept outside this README:

- [Getting started — English](docs/GETTING_STARTED.md)
- [Hướng dẫn bắt đầu — Tiếng Việt](docs/GETTING_STARTED.vi.md)

## Documentation

| Topic | English | Tiếng Việt |
| --- | --- | --- |
| Getting started | [GETTING_STARTED.md](docs/GETTING_STARTED.md) | [GETTING_STARTED.vi.md](docs/GETTING_STARTED.vi.md) |
| Architecture | [ARCHITECTURE.md](docs/ARCHITECTURE.md) | [ARCHITECTURE.vi.md](docs/ARCHITECTURE.vi.md) |
| Public API | [API.md](docs/API.md) | [API.vi.md](docs/API.vi.md) |
| Kaggle operations | [KAGGLE.md](docs/KAGGLE.md) | [KAGGLE.vi.md](docs/KAGGLE.vi.md) |
| Reproducibility | [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) | [REPRODUCIBILITY.vi.md](docs/REPRODUCIBILITY.vi.md) |
| Benchmarks | [BENCHMARKS.md](docs/BENCHMARKS.md) | [BENCHMARKS.vi.md](docs/BENCHMARKS.vi.md) |
| Security | [SECURITY.md](docs/SECURITY.md) | [SECURITY.vi.md](docs/SECURITY.vi.md) |
| Troubleshooting | [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | [TROUBLESHOOTING.vi.md](docs/TROUBLESHOOTING.vi.md) |

## Models and licensing

The repository's original integration code is released under the [MIT License](LICENSE). Attached model weights keep their own upstream terms: TranslateGemma is governed by the Gemma terms, Whisper by MIT, and the retained VoxCPM2 artifact by Apache-2.0.

See [MODEL_LICENSES.md](MODEL_LICENSES.md), [LICENSE-NOTES.md](LICENSE-NOTES.md), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before redistribution or deployment.

## Release

**v1.0.0** is the first public qualified release of this research project. Release notes and integrity information are available on the GitHub Releases page and in [RELEASE_NOTES_v1.0.0.md](RELEASE_NOTES_v1.0.0.md).
