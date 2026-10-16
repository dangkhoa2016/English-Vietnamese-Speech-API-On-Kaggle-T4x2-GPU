# Reproducibility

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](REPRODUCIBILITY.vi.md)

The repository separates three evidence layers: CPU-testable source contracts, real Kaggle T4x2 acceptance, and fresh executed production evidence generated separately on Kaggle. A claim is valid only for the layer that actually produced it.

## Environment authority

`constraints-kaggle-tested.txt` records the package versions retained from the qualified runtime. `scripts/bootstrap_kaggle.sh` creates separate translation/JAX and speech/PyTorch environments to avoid dependency and CUDA ownership ambiguity.

## Runtime authority

`bash scripts/preflight.sh` validates the required accelerator/model paths. `bash scripts/acceptance_pipeline.sh` is the real-model qualification path; GitHub Actions intentionally does not pretend to reproduce GPU inference.

## Evidence retention

The repository commits only the source template `notebooks/kaggle-production-showcase.ipynb`. A fresh executed production-demo notebook/evidence artifact is generated separately from a real Kaggle T4 x2 run and is not committed, so editable source and runtime evidence remain clearly separated.

## Known variance

First JAX translation execution may include substantial XLA compilation. VoxCPM2 synthesis latency also varies by generated speech duration and model behavior. Benchmark documentation reports these effects rather than filtering them out.
