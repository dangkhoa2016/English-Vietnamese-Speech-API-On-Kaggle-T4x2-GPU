# English–Vietnamese Speech API trên Kaggle T4x2 — v1.0.0

> 🌐 Language / Ngôn ngữ: [English](RELEASE_NOTES_v1.0.0.md) | **Tiếng Việt**

**v1.0.0** là bản phát hành công khai đầu tiên của một speech API đa mô hình có thể tái lập, được thiết kế để chạy **Whisper Large V3 Turbo, TranslateGemma 4B IT và VoxCPM2 đồng thời trong một phiên Kaggle Tesla T4 x2**.

Dự án minh họa cách một môi trường chỉ có hai GPU T4 có thể duy trì nhận dạng giọng nói, dịch Anh→Việt và tổng hợp giọng nói song ngữ dưới dạng các service thường trú phía sau một REST API duy nhất — không cần load/unload model cho từng request.

## Bản phát hành này cung cấp gì

| Endpoint | Khả năng |
|---|---|
| `POST /v1/audio/transcriptions` | Audio tiếng Anh → transcript tiếng Anh |
| `POST /v1/audio/speech` | Văn bản tiếng Anh hoặc tiếng Việt → WAV |
| `POST /v1/audio/translate-and-speak` | Audio tiếng Anh → transcript tiếng Anh → bản dịch tiếng Việt → giọng nói tiếng Việt |

Endpoint end-to-end `translate-and-speak` trả về một ZIP artifact gồm `transcript.en.txt`, `translation.vi.txt`, `speech.vi.wav` và `metadata.json`. Đây là các file được sinh trong response, không phải các file độc lập trong repository.

Mọi response công khai đều có `X-Request-ID` để trace theo request. Contract đầy đủ được mô tả trong [`docs/API.vi.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/API.vi.md).

## Ba model AI, hai GPU T4

Mục tiêu kỹ thuật chính là giữ cả ba model cùng resident đồng thời trong giới hạn bộ nhớ của hai GPU Tesla T4 16 GB trên Kaggle.

```text
Client
  |
  v
FastAPI Coordinator — CPU
  |
  |-------------------------------|
  |                               |
  v                               v
GPU 0                             GPU 1
TranslateGemma 4B IT              Whisper Large V3 Turbo
Keras 3 / KerasHub / JAX          VoxCPM2
                                  PyTorch
```

Placement đã được xác thực:

- **GPU 0** — TranslateGemma 4B IT cho dịch Anh→Việt.
- **GPU 1** — Whisper Large V3 Turbo và VoxCPM2 trong một speech worker PyTorch thường trú.
- **CPU** — FastAPI coordinator cho validation, routing, request tracing, admission control, health aggregation và đóng gói response.

Model được khởi động theo từng giai đoạn: `translation ready → speech ready → coordinator ready`.

Topology và GPU ownership contract đầy đủ nằm trong [`docs/ARCHITECTURE.vi.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/ARCHITECTURE.vi.md).

## Đã xác thực trên Kaggle Tesla T4 x2

Dự án được chạy bằng inference thật trên Kaggle T4 x2, không chỉ dựa trên mock service hoặc CPU test.

| Thiết bị | Model residency khi ready |
|---|---:|
| GPU 0 — TranslateGemma | **13,865 MiB** |
| GPU 1 — Whisper + VoxCPM2 | **6,871 MiB** |

Acceptance workflow đã kiểm tra cả ba model cùng resident, ASR tiếng Anh, dịch Anh→Việt, TTS tiếng Anh/Việt, pipeline hoàn chỉnh từ giọng nói tiếng Anh sang giọng nói tiếng Việt, hai request khác nhau chạy đồng thời với `PUBLIC_MAX_INFLIGHT=2`, request ID tách biệt, output ghép đúng request và shutdown sạch mà không quan sát thấy OOM, worker restart, deadlock hoặc trộn artifact giữa các request.

Benchmark warm end-to-end giữ lại từ ba request có mean server pipeline time **21,762.6 ms**. Đây là bằng chứng qualification cho cấu hình Kaggle đã tài liệu hóa, không phải cam kết hiệu năng chung.

Bằng chứng chi tiết:

- [`docs/BENCHMARKS.vi.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/BENCHMARKS.vi.md)
- [`docs/RELEASE-EVIDENCE-v1.0.0.vi.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/RELEASE-EVIDENCE-v1.0.0.vi.md)

## Kaggle production showcase

Notebook tương tác [`notebooks/kaggle-production-showcase.ipynb`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/notebooks/kaggle-production-showcase.ipynb) trình bày toàn bộ vòng đời:

`runtime validation → GPU preflight → staged model startup → transcription API → bilingual TTS API → English→Vietnamese speech pipeline → scenario demonstrations → benchmark evidence → cleanup`

Bốn production-style scenario sử dụng cùng public API path: **Customer Support**, **Technical Incident**, **Travel and Hospitality** và **Business Update**.

Để thiết lập và chạy hệ thống, xem [`docs/GETTING_STARTED.vi.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/GETTING_STARTED.vi.md). Chi tiết riêng cho Kaggle về model input, mount và runtime được mô tả trong [`docs/KAGGLE.vi.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/KAGGLE.vi.md).

## Runtime có thể tái lập

Dự án chủ động tách stack **Keras 3 / KerasHub / JAX** của TranslateGemma khỏi stack **PyTorch** dùng cho Whisper và VoxCPM2.

Tài liệu hỗ trợ:

- Runtime Dataset đã qualification: [`dangkhoa2016/english-vietnamese-speech-api-qualified-runtime`](https://www.kaggle.com/datasets/dangkhoa2016/english-vietnamese-speech-api-qualified-runtime), Version 1
- [`constraints-kaggle-tested.txt`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/constraints-kaggle-tested.txt)
- [`docs/REPRODUCIBILITY.vi.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/REPRODUCIBILITY.vi.md)
- [`SECURITY.vi.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/SECURITY.vi.md)
- [`docs/TROUBLESHOOTING.vi.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/TROUBLESHOOTING.vi.md)
- [`MODEL_LICENSES.vi.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/MODEL_LICENSES.vi.md)

## Phạm vi và giới hạn đã biết

Bản phát hành này qualification **runtime architecture, API integration, GPU placement, khả năng các model cùng tồn tại và workflow tái lập**. Nó **không** tuyên bố chất lượng dịch phổ quát.

Một test TranslateGemma được giữ lại có output pha trộn một phần tiếng Anh/tiếng Việt. Kết quả này được giữ có chủ đích để không đánh đồng runtime qualification với benchmark chất lượng model. Ứng dụng có yêu cầu dịch theo domain cần đánh giá chất lượng dịch riêng.

## Release assets

- [`kaggle-production-showcase.ipynb`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/releases/download/v1.0.0/kaggle-production-showcase.ipynb) — SHA-256 `5b2572b84dc0ef6b23a2b5e2726aace2f4933af47589e96f285756458927c89a`
- [`English-Vietnamese-Speech-API-v1.0.0-SHA256SUMS.txt`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/releases/download/v1.0.0/English-Vietnamese-Speech-API-v1.0.0-SHA256SUMS.txt) — SHA-256 `2ee9f013649fe42b82426d6ebe9554d0bc2e251cbbed864f7ae74dd7749d188e`

Kiểm tra bằng `sha256sum -c English-Vietnamese-Speech-API-v1.0.0-SHA256SUMS.txt`.

## Xác minh và tính toàn vẹn của bản phát hành

- **Release tag:** [`v1.0.0`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/tree/v1.0.0)
- **GitHub Release:** [`v1.0.0 — English–Vietnamese Speech API on Kaggle T4x2`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/releases/tag/v1.0.0)
- **Định nghĩa CI workflow:** [`.github/workflows/ci.yml`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/.github/workflows/ci.yml)
- **Định nghĩa Repository Audit workflow:** [`.github/workflows/repository-audit.yml`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/.github/workflows/repository-audit.yml)
- **Source notebook:** [`notebooks/kaggle-production-showcase.ipynb`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/notebooks/kaggle-production-showcase.ipynb)
- **Release evidence:** [`docs/RELEASE-EVIDENCE-v1.0.0.vi.md`](https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/docs/RELEASE-EVIDENCE-v1.0.0.vi.md)

GitHub Release body sẽ link tới exact final release commit và các run CI/Repository Audit thành công sau khi immutable release history đã được chốt; các giá trị này chỉ được biết sau khi history cuối cùng ổn định.

---

**v1.0.0 thiết lập baseline: ba model speech/translation bổ trợ nhau, hai GPU Tesla T4, một API stack có thể tái lập và một Kaggle demonstration hoàn chỉnh có thể kiểm tra từ startup, inference đến cleanup.**
