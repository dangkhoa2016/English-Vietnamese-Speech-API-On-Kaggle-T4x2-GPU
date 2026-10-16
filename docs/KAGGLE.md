# Kaggle production workflow

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](KAGGLE.vi.md)

## Accelerator and model inputs

Use a Kaggle **Tesla T4 x2** session. Attach the retained TranslateGemma 4B IT Keras preset, Whisper Large V3 Turbo Transformers checkpoint, and VoxCPM2 PyTorch checkpoint before running the production showcase.

Canonical notebook: `notebooks/kaggle-production-showcase.ipynb`.

## Qualified sequence

```bash
bash scripts/bootstrap_kaggle.sh
bash scripts/preflight.sh
bash scripts/start.sh
bash scripts/status.sh
```

Startup waits for translation readiness before beginning the speech stack and starts the coordinator only after both model workers are ready. This sequence is intentional: parallel cold reads caused severe attached-model storage contention during qualification.

## Public demo

The local coordinator is `127.0.0.1:8090`. A public Quick Tunnel is optional and must be combined with `API_AUTH_REQUIRED=true`. Never expose worker ports 8091 or 8092.

## Cleanup

Always finish reviewer-facing runs with `bash scripts/stop.sh` and verify ports are released and GPU model residency returns to zero.
