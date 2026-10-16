# Nhật ký thay đổi

> 🌐 Language / Ngôn ngữ: [English](CHANGELOG.md) | **Tiếng Việt**

Mọi thay đổi public đáng chú ý được ghi tại đây. Dự án dùng release tag cho các mốc public bất biến và tách rõ real-model qualification evidence khỏi các claim của CPU CI.

## v1.0.0 — 2026-10-16

### Đã bổ sung
- FastAPI coordinator với liveness/readiness, bounded admission control, request ID và Cloudflare Quick Tunnel có authentication tùy chọn.
- TranslateGemma 4B IT worker cô lập trên physical GPU 0 qua Keras 3 / KerasHub / JAX CUDA.
- Whisper Large V3 Turbo + VoxCPM2 PyTorch worker thường trú trên physical GPU 1.
- Endpoint transcription, speech synthesis và English-audio → Vietnamese-speech ZIP.
- Staged cold startup để tránh attached-model storage contention.
- Real Kaggle T4x2 qualification, interactive production-showcase source notebook, benchmark docs, tài liệu dự án song ngữ, model-license provenance và repository governance.
- README song ngữ được rút gọn thành landing page của dự án; hướng dẫn setup, thử API, acceptance, benchmark, tunnel và CPU quality gate được chuyển sang cặp tài liệu `docs/GETTING_STARTED*` riêng.

### Evidence đã qualification
- GPU 0 residency: 13,865 MiB.
- GPU 1 residency: 6,871 MiB.
- Mean server time của ba warm flagship request: 21,762.6 ms.
- Distinct-input concurrency PASS với `PUBLIC_MAX_INFLIGHT=2`.
