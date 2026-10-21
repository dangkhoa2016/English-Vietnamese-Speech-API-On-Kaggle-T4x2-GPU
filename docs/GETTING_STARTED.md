# Getting Started

This guide explains how to set up and run the English–Vietnamese Speech API on Kaggle T4 x2. It covers Kaggle inputs, runtime bootstrap, service startup, API smoke tests, real-model acceptance, benchmarking, optional public tunneling, and the CPU quality gate.

## 1. Prepare a Kaggle T4x2 notebook

Select **Accelerator → GPU T4 x2** and keep **Internet = On**.

In the Kaggle **Input** panel, choose **Add Input → Models** and attach these model inputs:

| Model | Kaggle resource | Framework | Variation | Version | Expected read-only mount |
| --- | --- | --- | --- | --- | --- |
| TranslateGemma 4B IT | `keras/translategemma` | Keras | `translategemma_4b_it` | `1` | `/kaggle/input/models/keras/translategemma/keras/translategemma_4b_it/1` |
| Whisper Large V3 Turbo | `dangkhoa2016/openai-whisper-large-v3-turbo` | Transformers | `default` | `1` | `/kaggle/input/models/dangkhoa2016/openai-whisper-large-v3-turbo/transformers/default/1` |
| VoxCPM2 | `dangkhoa2016/openbmb-voxcpm2` | PyTorch | `default` | `1` | `/kaggle/input/models/dangkhoa2016/openbmb-voxcpm2/pytorch/default/1` |

Also attach Dataset `dangkhoa2016/english-vietnamese-speech-api-qualified-runtime`, Version 1. It exposes the immutable `envi-speech-runtime-v1.bundle` payload used by the qualified bootstrap path.

Kaggle inputs are read-only. Repository checkout and durable outputs belong under `/kaggle/working`; extracted package payloads, virtual environments, and caches are kept under `/tmp`.

For full mount behavior and recovery guidance, see [KAGGLE.md](KAGGLE.md).

## 2. Bootstrap the qualified runtime

```bash
bash scripts/bootstrap_kaggle.sh
```

The bootstrap creates separate translation/JAX and speech/PyTorch environments. On Kaggle it prefers the preinstalled `uv` package manager, avoids system `apt` mutation, extracts the qualified runtime archive under `/tmp`, installs public packages from the attached wheelhouses, and fetches only exact-pinned NVIDIA/vendor wheels from official indexes.

Useful output markers include:

```text
BOOTSTRAP_VENV_BACKEND=uv
RUNTIME_SOURCE=KAGGLE_SINGLE_ARCHIVE
TMP_RUNTIME_LAYOUT=PASS
RUNTIME_ARCHIVE_EXTRACT_SECONDS=...
TRANSLATION_INSTALL_SECONDS=...
SPEECH_VENDOR_INSTALL_SECONDS=...
SPEECH_PUBLIC_INSTALL_SECONDS=...
BOOTSTRAP_TOTAL_SECONDS=...
BOOTSTRAP_KAGGLE=PASS
```

## 3. Run preflight and start services

```bash
bash scripts/preflight.sh
bash scripts/start.sh
```

Startup is deliberately staged:

```text
translation ready → speech ready → coordinator ready
```

The public coordinator listens on `127.0.0.1:8090`. Internal workers use ports `8091` and `8092`.

## 4. Exercise the public API

### English transcription

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/transcriptions \
  -F 'file=@data/fixtures/english-short.wav' \
  -F 'language=en'
```

### Vietnamese speech

```bash
printf 'Xin chào từ Kaggle T4x2.' > /tmp/speech.txt
curl -sS -X POST http://127.0.0.1:8090/v1/audio/speech \
  -F 'file=@/tmp/speech.txt;type=text/plain' \
  -F 'language=vi' \
  -o /tmp/speech.vi.wav
```

### English audio → Vietnamese speech

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/translate-and-speak \
  -F 'file=@data/fixtures/english-short.wav' \
  -o /tmp/translate-and-speak.zip
```



### Vietnamese audio → English speech

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/translate-and-speak \
  -F 'file=@data/showcase/vi-healthcare.wav' \
  -F 'source_language=vi' -F 'target_language=en' \
  -o /tmp/translate-vi-to-en.zip
```

The notebook gallery runs three English-to-Vietnamese and three Vietnamese-to-English cases. Full mode is the default and runs all six scenarios plus a bounded benchmark with parallel startup. Set `ENVI_SHOWCASE_MODE=quick` for two scenarios without the extended benchmark, or `ENVI_STARTUP_MODE=sequential` for a cold-start comparison.

See [API.md](API.md) for complete request and response contracts.

## 5. Run real-model acceptance and benchmark workflows

On a clean Kaggle T4x2 session with the required inputs attached:

```bash
bash scripts/acceptance_pipeline.sh
```

For an already-running qualified stack:

```bash
bash scripts/benchmark_pipeline.sh
```

Acceptance covers GPU ownership, worker survival, standalone ASR/translation/TTS paths, flagship ZIP structure, distinct-input concurrency, and cleanup. Detailed retained numbers and quality caveats are documented in [BENCHMARKS.md](BENCHMARKS.md).

## 6. Optional authenticated Cloudflare tunnel

Local/private notebook use does not require public authentication. Do not expose that mode directly to the Internet.

For a public Quick Tunnel:

```bash
export API_AUTH_REQUIRED=true
export ENABLE_CLOUDFLARE_TUNNEL=true
bash scripts/start.sh
bash scripts/run_tunnel.sh
```

The bearer key is stored in `runtime/api_key.txt`. Never commit it or print it into public notebook output. See [SECURITY.md](SECURITY.md).

## 7. CPU quality gate

The repository's CPU-testable gate is:

```bash
ruff check .
ruff format --check src tests
pytest -q
for file in scripts/*.sh; do bash -n "$file"; done
python -m compileall -q src tests
git diff --check
```

GitHub Actions validates this CPU contract. GPU model qualification remains a Kaggle T4x2 workflow.

## 8. Cleanup

Always stop the services after a run:

```bash
bash scripts/stop.sh
```

Confirm ports are released and GPU model residency returns to baseline. See [KAGGLE.md](KAGGLE.md) and [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for operational details.
