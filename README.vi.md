# English–Vietnamese Speech API trên Kaggle T4x2

<p align="center">
  <a href="https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/repository-audit.yml"><img alt="Repository Audit" src="https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/repository-audit.yml/badge.svg?branch=main"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
  <a href="MODEL_LICENSES.md"><img alt="TranslateGemma terms" src="https://img.shields.io/badge/TranslateGemma-Gemma%20Terms-orange.svg"></a>
  <a href="MODEL_LICENSES.md"><img alt="Whisper upstream license" src="https://img.shields.io/badge/Whisper-MIT-green.svg"></a>
  <a href="MODEL_LICENSES.md"><img alt="VoxCPM2 upstream license" src="https://img.shields.io/badge/VoxCPM2-Apache--2.0-orange.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
  <img alt="GPU" src="https://img.shields.io/badge/GPU-Tesla%20T4%20x2-76B900?logo=nvidia&logoColor=white">
  <img alt="Release" src="https://img.shields.io/badge/Release-v1.0.0-blue">
</p>

> 🌐 Language / Ngôn ngữ: [English](README.md) | **Tiếng Việt**

Đây là dự án nghiên cứu có thể tái lập và demo theo hướng production cho pipeline **audio tiếng Anh → transcript tiếng Anh → text tiếng Việt → speech tiếng Việt** trên một phiên Kaggle **Tesla T4 x2**.

Hệ thống kết hợp **Whisper Large V3 Turbo**, **TranslateGemma 4B IT** và **VoxCPM2** phía sau một FastAPI coordinator, đồng thời phân chia rõ quyền sở hữu model giữa hai GPU. Trọng tâm của repository là khả năng các model cùng tồn tại, cô lập runtime, khả năng tái lập, concurrency có giới hạn, request flow có thể quan sát và việc công khai minh bạch cả ưu điểm lẫn giới hạn.

## Trọng tâm nghiên cứu

Dự án khảo sát cách ba model speech/translation bổ trợ nhau có thể cùng chạy trên hai GPU Tesla T4 16 GB phổ biến mà không phải hoán đổi model theo từng request.

- **GPU 0** — TranslateGemma 4B IT qua Keras 3 / KerasHub / JAX.
- **GPU 1** — Whisper Large V3 Turbo và VoxCPM2 trong một PyTorch worker thường trú.
- **CPU** — FastAPI coordinator, validation, bounded admission control, health aggregation và đóng gói ZIP.

Kiến trúc chủ đích tách runtime JAX khỏi PyTorch và stage quá trình cold-load model để giảm tranh chấp storage/GPU.

## Hệ thống cung cấp gì

| Khả năng | Public endpoint |
| --- | --- |
| Nhận dạng giọng nói tiếng Anh | `POST /v1/audio/transcriptions` |
| Text-to-speech tiếng Anh hoặc tiếng Việt | `POST /v1/audio/speech` |
| Audio tiếng Anh → speech tiếng Việt | `POST /v1/audio/translate-and-speak` |
| Liveness và readiness | `GET /health/live`, `GET /health/ready` |

Pipeline chính trả về ZIP gồm `transcript.en.txt`, `translation.vi.txt`, `speech.vi.wav` và `metadata.json`. Response từ coordinator có `X-Request-ID` để truy vết.

## Kiến trúc

```text
Client
  |
  v
Coordinator :8090 (CPU)
  |------------------------------|
  v                              v
Translation worker :8091         Speech worker :8092
GPU 0                            GPU 1
TranslateGemma 4B IT             Whisper Large V3 Turbo
KerasHub / JAX                   VoxCPM2
                                 PyTorch
```

Cold startup được stage theo thứ tự:

```text
translation ready → speech ready → coordinator ready
```

Xem [Kiến trúc](docs/ARCHITECTURE.vi.md) để biết đầy đủ process, GPU và service contract.

## Kết quả đã qualification

Bằng chứng acceptance được giữ lại trên Kaggle T4x2 ghi nhận:

- **13,865 MiB** model residency trên GPU 0.
- **6,871 MiB** model residency trên GPU 1.
- Mean server-pipeline **21,762.6 ms** trong benchmark warm flagship gồm ba request được lưu giữ.
- Hai flagship request khác input chạy đồng thời đã PASS với `PUBLIC_MAX_INFLIGHT=2`, request ID tách biệt, output ghép đúng theo từng request, không worker restart, không OOM và không trộn artifact giữa các request.

Các số liệu này mô tả đúng môi trường qualification đã tài liệu hóa, không phải cam kết performance cho mọi môi trường. Chất lượng dịch cũng không được trình bày như một vấn đề đã giải quyết hoàn toàn: một kết quả TranslateGemma được giữ lại có output pha trộn tiếng Anh/tiếng Việt và được công khai như một giới hạn chất lượng thực tế của model.

Xem [Benchmark và acceptance evidence](docs/BENCHMARKS.vi.md) để biết methodology, timing và caveat chi tiết.

## Production showcase

[`notebooks/kaggle-production-showcase.ipynb`](notebooks/kaggle-production-showcase.ipynb) là demo tương tác của toàn bộ hệ thống. Notebook bao gồm kiểm tra input đã attach, runtime qualification, staged model startup, các public API path, scenario demonstration, bounded benchmark và cleanup.

Người không viết code vẫn có thể dùng notebook để hiểu kiến trúc, xem các scenario và nghe audio được tạo ra. Developer và researcher có thể dùng chính source notebook này để tái lập hoặc mở rộng hệ thống.

## Bắt đầu sử dụng

Để thiết lập và chạy hệ thống, xem hướng dẫn bắt đầu với Kaggle inputs, runtime bootstrap, ví dụ gọi API, acceptance, benchmark, public tunnel tùy chọn và local quality checks:

- [Hướng dẫn bắt đầu — Tiếng Việt](docs/GETTING_STARTED.vi.md)
- [Getting started — English](docs/GETTING_STARTED.md)

## Tài liệu

| Chủ đề | Tiếng Việt | English |
| --- | --- | --- |
| Bắt đầu sử dụng | [GETTING_STARTED.vi.md](docs/GETTING_STARTED.vi.md) | [GETTING_STARTED.md](docs/GETTING_STARTED.md) |
| Kiến trúc | [ARCHITECTURE.vi.md](docs/ARCHITECTURE.vi.md) | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Public API | [API.vi.md](docs/API.vi.md) | [API.md](docs/API.md) |
| Vận hành Kaggle | [KAGGLE.vi.md](docs/KAGGLE.vi.md) | [KAGGLE.md](docs/KAGGLE.md) |
| Khả năng tái lập | [REPRODUCIBILITY.vi.md](docs/REPRODUCIBILITY.vi.md) | [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) |
| Benchmark | [BENCHMARKS.vi.md](docs/BENCHMARKS.vi.md) | [BENCHMARKS.md](docs/BENCHMARKS.md) |
| Security | [SECURITY.vi.md](docs/SECURITY.vi.md) | [SECURITY.md](docs/SECURITY.md) |
| Troubleshooting | [TROUBLESHOOTING.vi.md](docs/TROUBLESHOOTING.vi.md) | [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |

## Model và license

Phần integration code gốc của repository được phát hành theo [MIT License](LICENSE). Các model weight được attach vẫn giữ điều khoản upstream riêng: TranslateGemma chịu Gemma terms, Whisper theo MIT và artifact VoxCPM2 được giữ lại theo Apache-2.0.

Xem [MODEL_LICENSES.vi.md](MODEL_LICENSES.vi.md), [LICENSE-NOTES.vi.md](LICENSE-NOTES.vi.md) và [THIRD_PARTY_NOTICES.vi.md](THIRD_PARTY_NOTICES.vi.md) trước khi redistribute hoặc deploy.

## Bản phát hành

**v1.0.0** là bản phát hành public đầu tiên đã được qualification của dự án nghiên cứu này. Release notes và thông tin integrity có trên trang GitHub Releases và trong [RELEASE_NOTES_v1.0.0.vi.md](RELEASE_NOTES_v1.0.0.vi.md).
