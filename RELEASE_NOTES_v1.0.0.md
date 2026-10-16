# English–Vietnamese Speech API on Kaggle T4x2 — v1.0.0

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](RELEASE_NOTES_v1.0.0.vi.md)

`v1.0.0` is the first public release of a production-style English→Vietnamese speech pipeline qualified on a single Kaggle Tesla T4 x2 session. It combines TranslateGemma 4B IT, Whisper Large V3 Turbo, and VoxCPM2 behind one REST API while keeping GPU workloads isolated, observable, and reproducible.

## Release links

- Repository: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU
- Release: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/releases/tag/v1.0.0
- Tag: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/tree/v1.0.0
- Canonical source notebook: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/notebooks/kaggle-production-showcase.ipynb
- CI workflow: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/ci.yml
- Repository Audit workflow: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/repository-audit.yml

## Highlights

- Run **TranslateGemma 4B IT**, **Whisper Large V3 Turbo**, and **VoxCPM2** together on Kaggle T4 x2.
- Pin translation to physical GPU 0 and ASR/TTS to physical GPU 1 through isolated worker processes.
- Expose transcription, bilingual speech synthesis, and an end-to-end English-audio→Vietnamese-audio pipeline through a FastAPI coordinator.
- Add deterministic `X-Request-ID` tracing and a strict four-member ZIP artifact contract for the flagship pipeline.
- Use staged startup and bounded admission control to avoid unsafe concurrent cold loading on two 16 GB T4 GPUs.
- Include a bilingual Kaggle production showcase with realistic reviewer-facing orchestration scenarios.
- Ship CI, repository audit, provenance, licensing, security, reproducibility, operations, and troubleshooting documentation.

## Runtime architecture

| Component | Placement | Runtime | Responsibility |
|---|---|---|---|
| TranslateGemma 4B IT | Physical GPU 0 | Keras 3 / KerasHub / JAX CUDA | English→Vietnamese translation |
| Whisper Large V3 Turbo | Physical GPU 1 | PyTorch / Transformers | English ASR |
| VoxCPM2 | Physical GPU 1 | PyTorch | English and Vietnamese TTS |
| FastAPI coordinator | CPU | Python 3.12 | Validation, routing, admission control, tracing, health, ZIP packaging |

Startup is deliberately staged:

`translation ready → speech ready → coordinator ready`

This avoids simultaneous model initialization competing for GPU memory.

Documentation: [Architecture](docs/ARCHITECTURE.md) · [Architecture — Tiếng Việt](docs/ARCHITECTURE.vi.md)

## Public API contract

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health/live` | Process liveness |
| `GET` | `/health/ready` | Aggregated worker readiness |
| `POST` | `/v1/audio/transcriptions` | English audio → English text |
| `POST` | `/v1/audio/speech` | English/Vietnamese text → WAV |
| `POST` | `/v1/audio/translate-and-speak` | English audio → transcript → Vietnamese translation → Vietnamese WAV |

Every public response includes `X-Request-ID`. The flagship ZIP contains exactly `transcript.en.txt`, `translation.vi.txt`, `speech.vi.wav`, and `metadata.json`.

Documentation: [API](docs/API.md) · [API — Tiếng Việt](docs/API.vi.md)
## Qualified dependency matrix

The release was re-qualified on Kaggle after upgrading the dependency set that triggered Dependabot update requests.

| Dependency | Qualified version |
|---|---:|
| Python | `3.12` |
| pytest | `9.1.1` |
| JAX | `0.11.2` |
| jaxlib | `0.11.2` |
| Keras | `3.15.1` |
| KerasHub | `0.32.0` |
| PyTorch | `2.11.0+cu128` |
| Torchaudio | `2.11.0+cu128` |
| Transformers | `5.19.0` |
| VoxCPM | `2.0.3` |
| SoundFile | `0.14.0` |
| Librosa | `1.0.0` |

The tested lock is [constraints-kaggle-tested.txt](constraints-kaggle-tested.txt). Translation and speech dependencies remain isolated in separate virtual environments.

## Kaggle inputs

Before **Run All**, attach these read-only Kaggle Models:

- TranslateGemma 4B IT: https://www.kaggle.com/models/keras/translategemma — Keras variation `translategemma_4b_it`, Version 1.
- Whisper Large V3 Turbo: https://www.kaggle.com/models/dangkhoa2016/openai-whisper-large-v3-turbo — Transformers variation `default`, Version 1.
- VoxCPM2: https://www.kaggle.com/models/dangkhoa2016/openbmb-voxcpm2 — PyTorch variation `default`, Version 1.

Also attach the public runtime Dataset `dangkhoa2016/english-vietnamese-speech-api-qualified-runtime`, Version 1. It provides a flat, checksum-audited cache of the qualified public/open-source Python 3.12 wheels. Exact NVIDIA/vendor wheels are intentionally not redistributed in the Dataset and remain fetched from official package indexes.

All Kaggle inputs stay read-only under `/kaggle/input`; source checkout, environments, logs, generated WAV/ZIP artifacts, and runtime state belong under `/kaggle/working`.

Documentation: [Kaggle guide](docs/KAGGLE.md) · [Kaggle guide — Tiếng Việt](docs/KAGGLE.vi.md)

## Production showcase

The canonical source notebook is [notebooks/kaggle-production-showcase.ipynb](notebooks/kaggle-production-showcase.ipynb).

It covers attached-model verification, hardware preflight, hybrid local-first bootstrap, quality gates, staged real-model startup, public transcription and bilingual TTS, the flagship translate-and-speak ZIP flow, optional authenticated Cloudflare exposure, and explicit cleanup. TTS now uses fixed synthetic English/Vietnamese reference voices and post-generation loudness normalization (target about `-20 dBFS` RMS with a `-1 dBFS` peak ceiling) so reviewer audio remains consistent across scenarios.

The four-case **Production Scenario Gallery** covers customer support, technical incident response, travel/hospitality, and business updates. Each scenario follows the public coordinator path:

`English text → VoxCPM2 English WAV → Whisper ASR → TranslateGemma EN→VI → VoxCPM2 Vietnamese WAV`

The self-generated gallery audio demonstrates orchestration and API integration; it is not presented as an independent ASR benchmark. The bundled `english-short.wav` fixture remains the static transcription acceptance input.
## Kaggle T4x2 qualification evidence

Fresh bootstrap, staged cold startup, real-model inference, public endpoint smoke tests, and clean teardown were executed after the dependency refresh.

| Device | Model residency at production readiness |
|---|---:|
| GPU 0 — TranslateGemma | **13,865 MiB** |
| GPU 1 — Whisper + VoxCPM2 | **6,871 MiB** |

Real-model acceptance:

- TranslateGemma reached readiness with JAX `0.11.2`, Keras `3.15.1`, and KerasHub `0.32.0`.
- Standalone translation returned valid Vietnamese Unicode output.
- Whisper transcribed the bundled English fixture successfully across three in-process requests.
- VoxCPM2 `2.0.3` generated valid 48 kHz PCM WAV for English and Vietnamese text.
- Generated English TTS audio was transcribed back through Whisper successfully.
- `/v1/audio/translate-and-speak` returned HTTP 200 with the exact four-member ZIP contract.
- Final cleanup returned project GPU residency to `0 MiB` on both devices.

Detailed evidence: [Release evidence](docs/RELEASE-EVIDENCE-v1.0.0.md) · [Bằng chứng phát hành](docs/RELEASE-EVIDENCE-v1.0.0.vi.md)

## Retained performance evidence

The original warm benchmark remains historical performance evidence; it is intentionally not relabeled as a new post-upgrade benchmark.

| Metric | Retained result |
|---|---:|
| Warm flagship mean, 3 requests | **21,762.6 ms** |
| ASR stage mean | **242.2 ms** |
| Translation stage mean | **3,644.0 ms** |
| TTS stage mean | **17,605.1 ms** |
| Distinct-input concurrency | **PASS**, `PUBLIC_MAX_INFLIGHT=2` |

No retained qualification run showed an OOM, worker restart, deadlock, or cross-request artifact mix-up.

Documentation: [Benchmarks](docs/BENCHMARKS.md) · [Benchmarks — Tiếng Việt](docs/BENCHMARKS.vi.md)

## Reproducibility, security, and provenance

Editable source and executed runtime evidence are deliberately separated. The source notebook is versioned in Git and attached to the release; executed Kaggle evidence is generated from a real T4x2 session and is intentionally not committed as editable source.

When Cloudflare exposure is enabled, public access is designed to require authentication. Runtime credentials live under `runtime/` and must not be committed or printed into notebook output.

- Reproducibility: [English](docs/REPRODUCIBILITY.md) · [Tiếng Việt](docs/REPRODUCIBILITY.vi.md)
- Security: [English](SECURITY.md) · [Tiếng Việt](SECURITY.vi.md)
- Troubleshooting: [English](docs/TROUBLESHOOTING.md) · [Tiếng Việt](docs/TROUBLESHOOTING.vi.md)
- Model licenses: [English](MODEL_LICENSES.md) · [Tiếng Việt](MODEL_LICENSES.vi.md)
- Third-party notices: [English](THIRD_PARTY_NOTICES.md) · [Tiếng Việt](THIRD_PARTY_NOTICES.vi.md)

Project-authored source and documentation are MIT licensed. TranslateGemma weights retain Gemma Terms of Use, Whisper remains upstream MIT, and VoxCPM2 remains upstream Apache-2.0. Runtime VoxCPM package `2.0.3` maps to upstream release source commit `19b6bf7590025418821a86dcb817504e0ad7e5df`.

## Known limitation

Runtime/API qualification is intentionally separated from universal translation-quality claims. One retained standalone TranslateGemma sample produced partially mixed English/Vietnamese output. The result remains visible in benchmark evidence; domain-specific translation quality should be evaluated independently.

## Release assets and SHA-256

### `kaggle-production-showcase.ipynb`

- Download: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/releases/download/v1.0.0/kaggle-production-showcase.ipynb
- SHA-256: `f6fefd97c8f44d51e042af27485110343272c9db35c8459a23d72cc4e27ea061`

### `English-Vietnamese-Speech-API-v1.0.0-SHA256SUMS.txt`

- Download: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/releases/download/v1.0.0/English-Vietnamese-Speech-API-v1.0.0-SHA256SUMS.txt
- File SHA-256: `d430545e980f63156f7604b118df3bc0ce6f0bafea393962671457ac6635f8e2`

Verify with:

```bash
sha256sum -c English-Vietnamese-Speech-API-v1.0.0-SHA256SUMS.txt
```

## Documentation map

[README](README.md) · [README Tiếng Việt](README.vi.md) · [Architecture](docs/ARCHITECTURE.md) · [API](docs/API.md) · [Kaggle](docs/KAGGLE.md) · [Reproducibility](docs/REPRODUCIBILITY.md) · [Benchmarks](docs/BENCHMARKS.md) · [Release evidence](docs/RELEASE-EVIDENCE-v1.0.0.md)
