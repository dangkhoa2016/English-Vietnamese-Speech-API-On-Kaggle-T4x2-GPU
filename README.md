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
  <img alt="Kaggle" src="https://img.shields.io/badge/Kaggle-Production%20Showcase-20BEFF?logo=kaggle&logoColor=white">
  <img alt="Release" src="https://img.shields.io/badge/Release-v1.0.0-blue">
</p>

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](README.vi.md)

A reproducible, production-style speech API demonstration for a single Kaggle **T4 x2** session. It combines **Whisper Large V3 Turbo**, **TranslateGemma 4B IT**, and **VoxCPM2** behind one FastAPI coordinator with explicit GPU ownership, bounded concurrency, request tracing, real-model acceptance, and an executed Kaggle showcase notebook.

## What this project proves

The retained qualification demonstrates that the three-model pipeline can coexist on two Tesla T4 GPUs without model swapping between requests:

- **GPU 0** → TranslateGemma 4B IT via Keras 3 / KerasHub / JAX;
- **GPU 1** → Whisper Large V3 Turbo + VoxCPM2 in one persistent PyTorch worker;
- CPU → public coordinator, validation, admission control, ZIP packaging, and health aggregation.

At readiness, retained residency was **13,865 MiB** on GPU 0 and **6,871 MiB** on GPU 1. The retained three-request warm flagship benchmark measured **21,762.6 ms** mean server pipeline time; TTS showed substantial variance and is reported rather than hidden. Two distinct concurrent flagship requests passed with `PUBLIC_MAX_INFLIGHT=2`, distinct request IDs, distinct paired outputs, no worker restart, no OOM, and no cross-request artifact mixing.

These are acceptance measurements for the documented Kaggle runtime, not universal latency guarantees. Model **translation quality** is also not guaranteed: the benchmark deliberately records a mixed-language TranslateGemma output as a quality caveat.

## Public API

Only the coordinator on `127.0.0.1:8090` is a public boundary.

| Endpoint | Purpose |
| --- | --- |
| `GET /health/live` | coordinator liveness |
| `GET /health/ready` | aggregate model-worker readiness |
| `POST /v1/audio/transcriptions` | English audio → English transcript |
| `POST /v1/audio/speech` | English or Vietnamese text → WAV |
| `POST /v1/audio/translate-and-speak` | English audio → English transcript → Vietnamese text → Vietnamese speech ZIP |

The flagship ZIP contains exactly:

- `transcript.en.txt`
- `translation.vi.txt`
- `speech.vi.wav`
- `metadata.json`

Every coordinator response includes `X-Request-ID`.

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

Cold model loading is intentionally staged:

```text
translation ready → speech ready → coordinator ready
```

This avoids the severe attached-model storage contention observed when both large stacks cold-read concurrently.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full process and GPU contract.

## Kaggle quick start

### 1. Create a Kaggle GPU notebook

Use a **GPU T4 x2** accelerator and attach the three model inputs expected by the repository:

- TranslateGemma 4B IT Keras preset;
- Whisper Large V3 Turbo Transformers checkpoint;
- VoxCPM2 PyTorch checkpoint.

The first cell of `notebooks/kaggle-production-showcase.ipynb` documents the exact attached-model paths used by the retained acceptance run.

### 2. Bootstrap the qualified runtime

```bash
bash scripts/bootstrap_kaggle.sh
```

The bootstrap separates the translation/JAX environment from the speech/PyTorch environment and pins the model-runtime versions used by the accepted Kaggle run. `constraints-kaggle-tested.txt` records the retained version evidence.

### 3. Preflight and start

```bash
bash scripts/preflight.sh
bash scripts/start.sh
```

`start.sh` waits for TranslateGemma readiness before loading the speech stack, then starts the coordinator only after both workers are ready.

### 4. Exercise the API

Transcription:

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/transcriptions \
  -F 'file=@data/fixtures/english-short.wav' \
  -F 'language=en'
```

Vietnamese speech:

```bash
printf 'Xin chào từ Kaggle T4x2.' > /tmp/speech.txt
curl -sS -X POST http://127.0.0.1:8090/v1/audio/speech \
  -F 'file=@/tmp/speech.txt;type=text/plain' \
  -F 'language=vi' \
  -o /tmp/speech.vi.wav
```

Flagship English-audio → Vietnamese-speech pipeline:

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/translate-and-speak \
  -F 'file=@data/fixtures/english-short.wav' \
  -o /tmp/translate-and-speak.zip
```

See [docs/API.md](docs/API.md) for the complete request/response contract.

## Real-model acceptance and benchmarks

For a clean Kaggle T4x2 session with the model inputs attached:

```bash
bash scripts/acceptance_pipeline.sh
```

For an already-running qualified stack:

```bash
bash scripts/benchmark_pipeline.sh
```

The acceptance workflow verifies GPU ownership, worker survival, standalone ASR/translation/TTS paths, the flagship ZIP contract, distinct-input concurrency, and cleanup back to zero model residency. Detailed retained numbers, startup behavior, and quality caveats are in [docs/BENCHMARKS.md](docs/BENCHMARKS.md).

## Production showcase notebook

- Source: `notebooks/kaggle-production-showcase.ipynb`
- Retained executed evidence: `notebooks/kaggle-production-showcase-executed.ipynb`

The showcase performs runtime/version evidence, attached-model validation, preflight, CPU quality gates, real staged startup, all three public API demos, a bounded benchmark, optional authenticated tunnel flow, and final GPU/port cleanup.

## Security and optional Cloudflare tunnel

Local/private notebook use defaults to authentication disabled. Do **not** expose that mode to the Internet.

For a public Quick Tunnel, authentication is mandatory:

```bash
export API_AUTH_REQUIRED=true
export ENABLE_CLOUDFLARE_TUNNEL=true
bash scripts/start.sh
bash scripts/run_tunnel.sh
```

The generated bearer key lives in `runtime/api_key.txt` and must never be committed or printed into public notebook output. `scripts/run_tunnel.sh` refuses to create the tunnel unless `API_AUTH_REQUIRED=true`, and it exposes only coordinator port 8090.

See [docs/SECURITY.md](docs/SECURITY.md).

## CPU CI and local quality gate

GPU model acceptance is intentionally not attempted in GitHub Actions. CI validates the CPU-testable repository contract:

```bash
ruff check .
ruff format --check src tests
pytest -q
for file in scripts/*.sh; do bash -n "$file"; done
python -m compileall -q src tests
git diff --check
```

Real-model behavior remains covered by the retained Kaggle acceptance artifacts and scripts.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Public API](docs/API.md)
- [Security](docs/SECURITY.md)
- [T4x2 benchmark and acceptance evidence](docs/BENCHMARKS.md)
- [Vietnamese architecture](docs/ARCHITECTURE.vi.md)
- [Vietnamese API](docs/API.vi.md)
- [Vietnamese security](docs/SECURITY.vi.md)
- [Vietnamese benchmark evidence](docs/BENCHMARKS.vi.md)
- [Kaggle production workflow](docs/KAGGLE.md) / [Tiếng Việt](docs/KAGGLE.vi.md)
- [Reproducibility](docs/REPRODUCIBILITY.md) / [Tiếng Việt](docs/REPRODUCIBILITY.vi.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md) / [Tiếng Việt](docs/TROUBLESHOOTING.vi.md)
- [v1.0.0 release evidence](docs/RELEASE-EVIDENCE-v1.0.0.md) / [Tiếng Việt](docs/RELEASE-EVIDENCE-v1.0.0.vi.md)
- [Model licenses and provenance](MODEL_LICENSES.md) / [Tiếng Việt](MODEL_LICENSES.vi.md)

## Source license and third-party models

The repository's original source integration is released under the [MIT License](LICENSE). This does not relicense the attached model weights. TranslateGemma remains subject to the Gemma Terms of Use, while the retained Whisper and VoxCPM2 artifacts identify MIT and Apache-2.0 respectively. Review [MODEL_LICENSES.md](MODEL_LICENSES.md), [LICENSE-NOTES.md](LICENSE-NOTES.md), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before redistribution or deployment.

## Release posture

`v1.0.0` is the first public qualification release. The release contract requires hosted CI and Repository Audit to pass on the final rewritten commit before the annotated tag and release assets are repointed. Real-model claims remain anchored to the retained Kaggle T4x2 acceptance evidence rather than GitHub CPU CI.
