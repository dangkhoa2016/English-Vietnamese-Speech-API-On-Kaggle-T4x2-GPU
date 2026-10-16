# Kaggle production workflow

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](KAGGLE.vi.md)

## Before you run

Use a Kaggle **Tesla T4 x2** notebook and keep **Internet = On** for the Git checkout and optional Cloudflare Quick Tunnel.

### Attach the three required Kaggle Models

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

Kaggle mounts attached inputs under **`/kaggle/input` as read-only storage**. The application reads model weights directly from those mounts. Do not clone source, create virtual environments, write logs, or generate WAV/ZIP artifacts under `/kaggle/input`.

Use **`/kaggle/working`** for everything writable: repository checkout, `.venv`, `.venv-speech`, runtime state, logs, generated audio, ZIP responses, and benchmark artifacts.

Canonical source notebook: `notebooks/kaggle-production-showcase.ipynb`.

The repository intentionally does **not** commit an executed notebook. A fresh executed production-demo notebook/evidence artifact should be produced separately from a real Kaggle T4 x2 run so published evidence cannot be confused with the editable template.

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

Always finish reviewer-facing runs with `bash scripts/stop.sh` and verify ports are released and GPU model residency returns to zero.
