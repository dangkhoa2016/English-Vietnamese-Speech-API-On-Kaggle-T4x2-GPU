# Bằng chứng phát hành — v1.0.0

> 🌐 Language / Ngôn ngữ: [English](RELEASE-EVIDENCE-v1.0.0.md) | **Tiếng Việt**

## Topology đã qualification

- GPU 0: TranslateGemma 4B IT qua Keras 3 / KerasHub / JAX.
- GPU 1: Whisper Large V3 Turbo + VoxCPM2 qua persistent PyTorch worker.
- CPU: chỉ coordinator.

## Residency khi ready

| Thiết bị | Residency đã lưu |
|---|---:|
| GPU 0 | 13,865 MiB |
| GPU 1 | 6,871 MiB |

## Warm flagship benchmark

Ba warm request tuần tự đã lưu có mean server pipeline **21,762.6 ms**. Stage mean: ASR 242.2 ms, translation 3,644.0 ms và TTS 17,605.1 ms.

## Concurrency evidence

Hai distinct-input request hoàn tất với `PUBLIC_MAX_INFLIGHT=2`, request ID khác nhau, output ghép đúng và không OOM, deadlock, worker restart hoặc cross-request mixing.

## Notebook evidence

- Source: `notebooks/kaggle-production-showcase.ipynb`
- Executed production evidence: được tạo/publish riêng từ một lần chạy Kaggle T4 x2 thật và chủ đích không commit vào Git.
- Qualified acceptance marker: `KAGGLE_PRODUCTION_SHOWCASE=PASS`

## Caveat

Standalone translation `Artificial intelligence can help people communicate across languages.` cho output còn mixed-language một phần. Evidence này được giữ có chủ đích để release không đánh đồng API/runtime qualification với bảo đảm translation quality phổ quát.
