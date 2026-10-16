# Reproducibility

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](REPRODUCIBILITY.vi.md)

The repository separates CPU-testable source contracts from real Kaggle T4x2 runtime qualification. Each benchmark, acceptance, or performance claim is scoped to the run and environment that actually produced it.

## Environment authority

`constraints-kaggle-tested.txt` records the package versions retained from the qualified runtime. `scripts/bootstrap_kaggle.sh` creates separate translation/JAX and speech/PyTorch environments to avoid dependency and CUDA ownership ambiguity. On Kaggle it prefers the preinstalled `uv` package manager for fast Python 3.12 environment creation and installation without mutating system packages through `apt`; phase timers make bootstrap cost observable. The public Kaggle Dataset `dangkhoa2016/english-vietnamese-speech-api-qualified-runtime` caches the public/open-source Python 3.12 wheels with SHA-256 and license inventory; NVIDIA/vendor wheels are intentionally excluded and fetched at their exact pinned versions from official indexes.

## Runtime authority

`bash scripts/preflight.sh` validates the required accelerator/model paths. `bash scripts/acceptance_pipeline.sh` is the real-model qualification path; GitHub Actions intentionally does not pretend to reproduce GPU inference.

## Evidence retention

The repository tracks the reusable source notebook `notebooks/kaggle-production-showcase.ipynb`. Exported executed copies, if shared, are optional snapshots of individual runs rather than project dependencies; reproducibility comes from the source, pinned runtime inputs, documented procedures, and scoped qualification results.

## Known variance

First JAX translation execution may include substantial XLA compilation. VoxCPM2 synthesis latency also varies by generated speech duration and model behavior. Benchmark documentation reports these effects rather than filtering them out.
