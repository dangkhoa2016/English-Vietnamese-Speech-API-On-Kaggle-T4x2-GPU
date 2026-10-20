# English–Vietnamese Speech API on Kaggle T4x2 — v1.0.0

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](RELEASE_NOTES_v1.0.0.vi.md)

**v1.0.0** is the first public release of a reproducible multi-model speech API designed to run **Whisper Large V3 Turbo, TranslateGemma 4B IT, and VoxCPM2 together in a single Kaggle Tesla T4 x2 session**.

The project demonstrates how a constrained dual-T4 environment can host speech recognition, bidirectional English↔Vietnamese translation, and bilingual speech synthesis as persistent services behind one REST API—without loading and unloading models for every request.

## What this release provides

| Endpoint | Capability |
|---|---|
| `POST /v1/audio/transcriptions` | English or Vietnamese audio → transcript in the source language |
| `POST /v1/audio/speech` | English or Vietnamese text → WAV audio |
| `POST /v1/audio/translate-and-speak` | English↔Vietnamese audio → transcript → translation → synthesized speech |

The end-to-end `translate-and-speak` endpoint accepts `source_language` and `target_language` for either `en→vi` (default) or `vi→en`. It returns four ZIP members: `transcript.<source>.txt`, `translation.<target>.txt`, `speech.<target>.wav`, and `metadata.json`. The default path uses `transcript.en.txt`, `translation.vi.txt`, and `speech.vi.wav`. These are generated response members rather than standalone repository files.

Every public API response also carries an `X-Request-ID` for request-level tracing. Full contracts are documented in [`docs/API.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/API.md).

## Three AI models, two T4 GPUs

The main engineering goal is to keep all three models resident at the same time while respecting the memory limits of Kaggle's two 16 GB Tesla T4 GPUs.

```text
Client
  |
  v
FastAPI Coordinator — CPU
  |
  |-------------------------------|
  |                               |
  v                               v
GPU 0                             GPU 1
TranslateGemma 4B IT              Whisper Large V3 Turbo
Keras 3 / KerasHub / JAX          VoxCPM2
                                  PyTorch
```

Validated placement:

- **GPU 0** — TranslateGemma 4B IT for bidirectional English↔Vietnamese translation.
- **GPU 1** — Whisper Large V3 Turbo and VoxCPM2 in one persistent speech worker.
- **CPU** — FastAPI coordinator for validation, routing, request tracing, admission control, health aggregation, and response packaging.

Model startup is deliberately staged: `translation ready → speech ready → coordinator ready`.

The complete process topology and GPU ownership contract are documented in [`docs/ARCHITECTURE.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/ARCHITECTURE.md).

## Validated on Kaggle Tesla T4 x2

The project was exercised with real model inference in a Kaggle T4 x2 environment rather than relying only on mocked services or CPU tests.

| Device | Model residency at readiness |
|---|---:|
| GPU 0 — TranslateGemma | **13,865 MiB** |
| GPU 1 — Whisper + VoxCPM2 | **6,871 MiB** |

The acceptance workflow verified all three models resident together, English ASR, English→Vietnamese translation, English/Vietnamese TTS, the complete English-speech→Vietnamese-speech pipeline, two distinct in-flight requests with `PUBLIC_MAX_INFLIGHT=2`, distinct request IDs, correctly paired outputs, and clean shutdown without observed OOM, worker restart, deadlock, or cross-request artifact mixing.

The retained three-request warm end-to-end benchmark measured a mean server pipeline time of **21,762.6 ms**. These figures are qualification evidence for the documented Kaggle configuration, not general performance guarantees.

Detailed evidence:

- [`docs/BENCHMARKS.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/BENCHMARKS.md)
- [`docs/RELEASE-EVIDENCE-v1.0.0.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/RELEASE-EVIDENCE-v1.0.0.md)

## Kaggle production showcase

The interactive [`notebooks/kaggle-production-showcase.ipynb`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/notebooks/kaggle-production-showcase.ipynb) demonstrates the full lifecycle:

`runtime validation → GPU preflight → staged model startup → transcription API → bilingual TTS API → bidirectional speech pipeline → six scenario demonstrations → benchmark evidence → cleanup`

Six production-style scenarios use the same public API path: three English→Vietnamese (**Customer Support**, **Business Update**, **Travel Reservation**) and three Vietnamese→English (**Healthcare**, **Banking**, **Education**). Six prior showcase audio outputs were heard and approved by the project owner. That earlier approval does not establish translation quality after removing scenario-specific guidance; the current notebook requires independent fresh GPU execution and listening review.

For setup and execution, see [`docs/GETTING_STARTED.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/GETTING_STARTED.md). Kaggle-specific model inputs, mounts, and runtime details are documented in [`docs/KAGGLE.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/KAGGLE.md).

## Reproducible runtime

The project intentionally separates TranslateGemma's **Keras 3 / KerasHub / JAX** stack from the **PyTorch** stack used by Whisper and VoxCPM2.

Supporting material:

- Qualified runtime Dataset: [`dangkhoa2016/english-vietnamese-speech-api-qualified-runtime`](https://www.kaggle.com/datasets/dangkhoa2016/english-vietnamese-speech-api-qualified-runtime), Version 1
- [`constraints-kaggle-tested.txt`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/constraints-kaggle-tested.txt)
- [`docs/REPRODUCIBILITY.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/REPRODUCIBILITY.md)
- [`SECURITY.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/SECURITY.md)
- [`docs/TROUBLESHOOTING.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/TROUBLESHOOTING.md)
- [`MODEL_LICENSES.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/MODEL_LICENSES.md)

## Scope and known limitation

This release qualifies the **runtime architecture, API integration, GPU placement, model coexistence, and reproducibility workflow**. It does **not** claim universal translation-quality performance.

One retained TranslateGemma test produced partially mixed English/Vietnamese output. That result remains documented intentionally so runtime qualification is not confused with a model-quality benchmark. Applications with domain-specific translation requirements should evaluate translation quality separately.

## Release assets

The final notebook and checksum manifest are published as GitHub Release assets. Their SHA-256 values must be calculated from the actual final attachments after the release commit and tag are finalized. Do not reuse hashes of previous assets.

## Verification & release integrity

- **Release tag:** [`v1.0.0`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/tree/v1.0.0)
- **GitHub Release:** [`v1.0.0 — English–Vietnamese Speech API on Kaggle T4x2`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/releases/tag/v1.0.0)
- **CI workflow definition:** [`.github/workflows/ci.yml`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/.github/workflows/ci.yml)
- **Repository Audit workflow definition:** [`.github/workflows/repository-audit.yml`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/.github/workflows/repository-audit.yml)
- **Source notebook:** [`notebooks/kaggle-production-showcase.ipynb`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/notebooks/kaggle-production-showcase.ipynb)
- **Release evidence:** [`docs/RELEASE-EVIDENCE-v1.0.0.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/RELEASE-EVIDENCE-v1.0.0.md)

The GitHub Release body links the exact final release commit and the successful hosted CI and Repository Audit runs, which are only known after the immutable release history has been finalized.

---

**v1.0.0 establishes the baseline: three complementary speech and translation models, two Tesla T4 GPUs, one reproducible API stack, and a complete Kaggle demonstration that can be inspected from startup through inference to cleanup.**
