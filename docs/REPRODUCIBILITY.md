# Reproducibility

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](REPRODUCIBILITY.vi.md)

The repository separates three evidence layers: CPU-testable source contracts, real Kaggle T4x2 acceptance, and retained executed notebook evidence. A claim is valid only for the layer that actually produced it.

## Environment authority

`constraints-kaggle-tested.txt` records the package versions retained from the qualified runtime. `scripts/bootstrap_kaggle.sh` creates separate translation/JAX and speech/PyTorch environments to avoid dependency and CUDA ownership ambiguity.

## Runtime authority

`bash scripts/preflight.sh` validates the required accelerator/model paths. `bash scripts/acceptance_pipeline.sh` is the real-model qualification path; GitHub Actions intentionally does not pretend to reproduce GPU inference.

## Evidence retention

The source notebook is kept separately from `notebooks/kaggle-production-showcase-executed.ipynb`. The executed notebook is reviewer evidence and should not be retroactively rewritten to fabricate a newer runtime revision.

## Known variance

First JAX translation execution may include substantial XLA compilation. VoxCPM2 synthesis latency also varies by generated speech duration and model behavior. Benchmark documentation reports these effects rather than filtering them out.
