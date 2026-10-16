# Kaggle production workflow

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](KAGGLE.vi.md)

## Before you run

Use a Kaggle **Tesla T4 x2** notebook and keep **Internet = On** for the Git checkout and optional Cloudflare Quick Tunnel.

### Attach the three required Kaggle Models and the qualified runtime Dataset

Open the notebook's **Add Input** panel, choose **Models**, and attach the exact selections below before running any code:

| Model | Kaggle owner/resource | Framework | Variation | Version | Expected mount |
| --- | --- | --- | --- | --- | --- |
| TranslateGemma 4B IT | `keras/translategemma` | Keras | `translategemma_4b_it` | `1` | `/kaggle/input/models/keras/translategemma/keras/translategemma_4b_it/1` |
| Whisper Large V3 Turbo | `dangkhoa2016/openai-whisper-large-v3-turbo` | Transformers | `default` | `1` | `/kaggle/input/models/dangkhoa2016/openai-whisper-large-v3-turbo/transformers/default/1` |
| VoxCPM2 | `dangkhoa2016/openbmb-voxcpm2` | PyTorch | `default` | `1` | `/kaggle/input/models/dangkhoa2016/openbmb-voxcpm2/pytorch/default/1` |

Search recipes:

```text
Add Input → Models
Search: keras/translategemma
Framework: Keras
Variation: translategemma_4b_it
Version: 1

Add Input → Models
Search: dangkhoa2016/openai-whisper-large-v3-turbo
Framework: Transformers
Variation: default
Version: 1

Add Input → Models
Search: dangkhoa2016/openbmb-voxcpm2
Framework: PyTorch
Variation: default
Version: 1
```

Then choose **Add Input → Datasets** and attach `dangkhoa2016/english-vietnamese-speech-api-qualified-runtime`, Version 1. The Dataset exposes one immutable file, `envi-speech-runtime-v1.bundle`, containing the audited public wheelhouse, exact manifests, SHA-256/license inventory, and preserved PyTorch/Torchaudio `+cu128` wheels. Bootstrap extracts it to `/tmp/envi-speech-runtime-v1`; NVIDIA/vendor wheels remain exact-pinned and are fetched from official package indexes. The bootstrap now prefers the `uv` package manager already available in the Kaggle image, so Python 3.12 environments can be created without `apt` or `python3.12-venv`. It prints archive extraction, translation install, speech vendor/public install, and total bootstrap timings so each Run All exposes where startup time is spent. The previous 302-second measurement belongs to the superseded multi-file layout and is not reused as a claim for the current path.

Kaggle mounts attached inputs under **`/kaggle/input` as read-only storage**. The application reads model weights directly from those mounts. Do not clone source, create virtual environments, write logs, or generate WAV/ZIP artifacts under `/kaggle/input`.

Use **`/tmp`** for extracted runtime packages, both virtual environments, and package/model caches. Use **`/kaggle/working`** only for the repository checkout and durable evidence/output such as logs, generated audio, ZIP responses, benchmark artifacts, executed notebook, and HTML export.

Canonical source notebook: `notebooks/kaggle-production-showcase.ipynb`.

The repository tracks the reusable source notebook as the project artifact. Exported executed copies, if someone chooses to share them, are optional snapshots of individual runs; they are not required to use, reproduce, or extend the project and do not replace the source notebook.

## Qualified sequence

```bash
bash scripts/bootstrap_kaggle.sh
bash scripts/preflight.sh
bash scripts/start.sh
bash scripts/status.sh
```

Startup waits for translation readiness before beginning the speech stack and starts the coordinator only after both model workers are ready. This sequence is intentional: parallel cold reads caused severe attached-model storage contention during qualification.

## Public demo

The local coordinator is `127.0.0.1:8090`. A public Quick Tunnel is optional and must be combined with `API_AUTH_REQUIRED=true`. Never expose worker ports `8091` or `8092`.

## Cleanup

Always finish production-showcase runs with `bash scripts/stop.sh` and verify ports are released and GPU model residency returns to zero.
