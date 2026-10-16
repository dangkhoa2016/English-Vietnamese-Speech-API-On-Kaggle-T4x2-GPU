# English–Vietnamese Speech API trên Kaggle T4x2 — v1.0.0

> 🌐 Language / Ngôn ngữ: [English](RELEASE_NOTES_v1.0.0.md) | **Tiếng Việt**

`v1.0.0` là bản phát hành public đầu tiên của pipeline speech English→Vietnamese theo phong cách production, được qualification trên một phiên Kaggle Tesla T4 x2. Dự án phối hợp TranslateGemma 4B IT, Whisper Large V3 Turbo và VoxCPM2 phía sau một REST API thống nhất, đồng thời giữ workload GPU được cô lập, có thể quan sát và có thể tái lập.

## Liên kết phát hành

- Repository: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU
- Release: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/releases/tag/v1.0.0
- Tag: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/tree/v1.0.0
- Notebook source chuẩn: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/blob/v1.0.0/notebooks/kaggle-production-showcase.ipynb
- CI workflow: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/ci.yml
- Repository Audit workflow: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/actions/workflows/repository-audit.yml

## Điểm nổi bật

- Chạy đồng thời **TranslateGemma 4B IT**, **Whisper Large V3 Turbo** và **VoxCPM2** trên Kaggle T4 x2.
- Giữ translation trên physical GPU 0 và ASR/TTS trên physical GPU 1 bằng các worker process được cô lập.
- Cung cấp transcription, speech synthesis song ngữ và pipeline English audio→Vietnamese audio end-to-end thông qua FastAPI coordinator.
- Mỗi public response có `X-Request-ID`; flagship pipeline trả ZIP theo contract bốn file cố định.
- Dùng staged startup và bounded admission control để tránh cold-load đồng thời gây áp lực lên hai GPU T4 16 GB.
- Có Kaggle production showcase song ngữ với các tình huống orchestration thực tế dành cho reviewer.
- Bao gồm CI, repository audit, provenance, licensing, security, reproducibility, operations và troubleshooting documentation.

## Kiến trúc runtime

| Thành phần | Vị trí | Runtime | Trách nhiệm |
|---|---|---|---|
| TranslateGemma 4B IT | Physical GPU 0 | Keras 3 / KerasHub / JAX CUDA | Dịch English→Vietnamese |
| Whisper Large V3 Turbo | Physical GPU 1 | PyTorch / Transformers | English ASR |
| VoxCPM2 | Physical GPU 1 | PyTorch | English/Vietnamese TTS |
| FastAPI coordinator | CPU | Python 3.12 | Validation, routing, admission control, tracing, health, ZIP packaging |

Startup được staging có chủ đích:

`translation ready → speech ready → coordinator ready`

Thiết kế này tránh nhiều model khởi tạo đồng thời và cạnh tranh GPU memory.

Tài liệu: [Architecture](docs/ARCHITECTURE.md) · [Kiến trúc — Tiếng Việt](docs/ARCHITECTURE.vi.md)

## Public API contract

| Method | Endpoint | Chức năng |
|---|---|---|
| `GET` | `/health/live` | Process liveness |
| `GET` | `/health/ready` | Readiness tổng hợp của workers |
| `POST` | `/v1/audio/transcriptions` | English audio → English text |
| `POST` | `/v1/audio/speech` | English/Vietnamese text → WAV |
| `POST` | `/v1/audio/translate-and-speak` | English audio → transcript → Vietnamese translation → Vietnamese WAV |

Mỗi public response có `X-Request-ID`. Flagship ZIP gồm chính xác `transcript.en.txt`, `translation.vi.txt`, `speech.vi.wav` và `metadata.json`.

Tài liệu: [API](docs/API.md) · [API — Tiếng Việt](docs/API.vi.md)
## Dependency matrix đã qualification

Release được re-qualify trên Kaggle sau khi nâng dependency set đã kích hoạt các Dependabot update requests.

| Dependency | Version đã qualification |
|---|---:|
| Python | `3.12` |
| pytest | `9.1.1` |
| JAX | `0.11.2` |
| jaxlib | `0.11.2` |
| Keras | `3.15.1` |
| KerasHub | `0.32.0` |
| PyTorch | `2.11.0+cu128` |
| Torchaudio | `2.11.0+cu128` |
| Transformers | `5.19.0` |
| VoxCPM | `2.0.3` |
| SoundFile | `0.14.0` |
| Librosa | `1.0.0` |

Evidence lock nằm tại [constraints-kaggle-tested.txt](constraints-kaggle-tested.txt). Translation và speech dependencies tiếp tục được cô lập trong hai virtual environment riêng.

## Kaggle inputs

Trước **Run All**, attach ba Kaggle Models read-only sau:

- TranslateGemma 4B IT: https://www.kaggle.com/models/keras/translategemma — Keras variation `translategemma_4b_it`, Version 1.
- Whisper Large V3 Turbo: https://www.kaggle.com/models/dangkhoa2016/openai-whisper-large-v3-turbo — Transformers variation `default`, Version 1.
- VoxCPM2: https://www.kaggle.com/models/dangkhoa2016/openbmb-voxcpm2 — PyTorch variation `default`, Version 1.

Đồng thời attach public runtime Dataset `dangkhoa2016/english-vietnamese-speech-api-qualified-runtime`, Version 1. Dataset cung cấp flat cache đã audit checksum cho các Python 3.12 wheel public/open-source đã qualification. Exact NVIDIA/vendor wheels được chủ động không redistribute trong Dataset và vẫn tải từ official package indexes.

Tất cả Kaggle inputs là read-only tại `/kaggle/input`; source checkout, environments, logs, WAV/ZIP artifacts và runtime state được ghi tại `/kaggle/working`.

Tài liệu: [Kaggle guide](docs/KAGGLE.md) · [Kaggle guide — Tiếng Việt](docs/KAGGLE.vi.md)

## Production showcase

Notebook source chuẩn là [notebooks/kaggle-production-showcase.ipynb](notebooks/kaggle-production-showcase.ipynb).

Notebook bao gồm attached-model verification, hardware preflight, hybrid local-first bootstrap, quality gates, staged real-model startup, public transcription, bilingual TTS, flagship translate-and-speak ZIP flow, optional authenticated Cloudflare exposure và explicit cleanup. TTS hiện dùng fixed synthetic English/Vietnamese reference voices cùng post-generation loudness normalization (mục tiêu khoảng `-20 dBFS` RMS với peak ceiling `-1 dBFS`) để mức âm lượng và voice identity ổn định hơn giữa các scenario.

**Production Scenario Gallery** gồm bốn case: customer support, technical incident, travel/hospitality và business update. Mỗi case đi qua public coordinator:

`English text → VoxCPM2 English WAV → Whisper ASR → TranslateGemma EN→VI → VoxCPM2 Vietnamese WAV`

Audio tự sinh trong gallery dùng để chứng minh orchestration/API integration, không được trình bày như independent ASR benchmark. Fixture tĩnh `english-short.wav` vẫn là transcription acceptance input.
## Bằng chứng qualification Kaggle T4x2

Fresh bootstrap, staged cold startup, real-model inference, public endpoint smoke tests và clean teardown đều đã được chạy lại sau dependency refresh.

| Device | Model residency tại production readiness |
|---|---:|
| GPU 0 — TranslateGemma | **13,865 MiB** |
| GPU 1 — Whisper + VoxCPM2 | **6,871 MiB** |

Real-model acceptance:

- TranslateGemma đạt readiness với JAX `0.11.2`, Keras `3.15.1` và KerasHub `0.32.0`.
- Standalone translation trả Vietnamese Unicode hợp lệ.
- Whisper transcribe fixture English thành công qua ba in-process requests.
- VoxCPM2 `2.0.3` tạo WAV PCM 48 kHz hợp lệ cho cả English và Vietnamese.
- English TTS output được đưa ngược qua Whisper và transcribe thành công.
- `/v1/audio/translate-and-speak` trả HTTP 200 cùng ZIP đúng bốn member.
- Final cleanup đưa project GPU residency của cả hai GPU về `0 MiB`.

Evidence chi tiết: [Release evidence](docs/RELEASE-EVIDENCE-v1.0.0.md) · [Bằng chứng phát hành](docs/RELEASE-EVIDENCE-v1.0.0.vi.md)

## Performance evidence đã lưu

Warm benchmark qualification ban đầu được giữ lại như historical performance evidence, không đổi nhãn thành benchmark mới sau dependency upgrade.

| Metric | Kết quả đã lưu |
|---|---:|
| Warm flagship mean, 3 requests | **21,762.6 ms** |
| ASR stage mean | **242.2 ms** |
| Translation stage mean | **3,644.0 ms** |
| TTS stage mean | **17,605.1 ms** |
| Distinct-input concurrency | **PASS**, `PUBLIC_MAX_INFLIGHT=2` |

Không có retained qualification run nào ghi nhận OOM, worker restart, deadlock hoặc cross-request artifact mixing.

Tài liệu: [Benchmarks](docs/BENCHMARKS.md) · [Benchmarks — Tiếng Việt](docs/BENCHMARKS.vi.md)

## Reproducibility, security và provenance

Release tách editable source khỏi executed runtime evidence. Source notebook được version trong Git và attach vào release; executed Kaggle evidence được sinh từ phiên T4x2 thật và không commit như editable source.

Khi bật Cloudflare exposure, public access được thiết kế để yêu cầu authentication. Runtime credentials nằm trong `runtime/` và không được commit hoặc in ra notebook output.

- Reproducibility: [English](docs/REPRODUCIBILITY.md) · [Tiếng Việt](docs/REPRODUCIBILITY.vi.md)
- Security: [English](SECURITY.md) · [Tiếng Việt](SECURITY.vi.md)
- Troubleshooting: [English](docs/TROUBLESHOOTING.md) · [Tiếng Việt](docs/TROUBLESHOOTING.vi.md)
- Model licenses: [English](MODEL_LICENSES.md) · [Tiếng Việt](MODEL_LICENSES.vi.md)
- Third-party notices: [English](THIRD_PARTY_NOTICES.md) · [Tiếng Việt](THIRD_PARTY_NOTICES.vi.md)

Source và documentation do dự án tự viết dùng MIT. TranslateGemma weights giữ Gemma Terms of Use, Whisper giữ upstream MIT, VoxCPM2 giữ upstream Apache-2.0. Runtime VoxCPM package `2.0.3` map tới upstream release source commit `19b6bf7590025418821a86dcb817504e0ad7e5df`.

## Giới hạn đã biết

Runtime/API qualification được tách rõ khỏi tuyên bố universal translation quality. Một standalone TranslateGemma sample đã lưu cho kết quả English/Vietnamese mixed một phần. Kết quả vẫn được giữ trong benchmark evidence; người dùng nên đánh giá translation quality riêng theo domain của mình.

## Release assets và SHA-256

### `kaggle-production-showcase.ipynb`

- Download: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/releases/download/v1.0.0/kaggle-production-showcase.ipynb
- SHA-256: `f6fefd97c8f44d51e042af27485110343272c9db35c8459a23d72cc4e27ea061`

### `English-Vietnamese-Speech-API-v1.0.0-SHA256SUMS.txt`

- Download: https://github.com/dangkhoa2016/English-Vietnamese-Speech-API-On-Kaggle-T4x2-GPU/releases/download/v1.0.0/English-Vietnamese-Speech-API-v1.0.0-SHA256SUMS.txt
- File SHA-256: `d430545e980f63156f7604b118df3bc0ce6f0bafea393962671457ac6635f8e2`

Verify bằng:

```bash
sha256sum -c English-Vietnamese-Speech-API-v1.0.0-SHA256SUMS.txt
```

## Bản đồ tài liệu

[README](README.md) · [README Tiếng Việt](README.vi.md) · [Architecture](docs/ARCHITECTURE.md) · [API](docs/API.md) · [Kaggle](docs/KAGGLE.md) · [Reproducibility](docs/REPRODUCIBILITY.md) · [Benchmarks](docs/BENCHMARKS.md) · [Release evidence](docs/RELEASE-EVIDENCE-v1.0.0.md)
