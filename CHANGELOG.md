# Changelog

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](CHANGELOG.vi.md)

All notable public changes are recorded here. The project uses release tags for immutable public milestones and keeps real-model qualification evidence separate from CPU CI claims.

## v1.0.0 — 2026-10-16

### Added
- FastAPI coordinator with liveness/readiness, bounded admission control, request IDs, and optional authenticated Cloudflare Quick Tunnel.
- TranslateGemma 4B IT worker isolated on physical GPU 0 through Keras 3 / KerasHub / JAX CUDA.
- Persistent Whisper Large V3 Turbo + VoxCPM2 PyTorch worker isolated on physical GPU 1.
- English/Vietnamese transcription, bilingual speech synthesis, and bidirectional English ↔ Vietnamese audio-to-speech ZIP endpoints.
- Staged cold startup to avoid attached-model storage contention.
- Real Kaggle T4x2 qualification, interactive production-showcase source notebook, benchmark documentation, bilingual project documentation, model-license provenance, and repository governance.
- Concise bilingual README landing pages with operational setup, API exercises, acceptance, benchmark, tunnel, and CPU quality-gate instructions moved into dedicated `docs/GETTING_STARTED*` guides.

### Qualified evidence
- GPU 0 residency: 13,865 MiB.
- GPU 1 residency: 6,871 MiB.
- Three-request warm flagship mean server time: 21,762.6 ms.
- Distinct-input concurrency passed with `PUBLIC_MAX_INFLIGHT=2`.
