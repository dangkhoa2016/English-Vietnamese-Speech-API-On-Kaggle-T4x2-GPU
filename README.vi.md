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
  <img alt="Kaggle" src="https://img.shields.io/badge/Kaggle-Production%20Showcase-20BEFF?logo=kaggle&logoColor=white">
  <img alt="Release" src="https://img.shields.io/badge/Release-v1.0.0-blue">
</p>

> 🌐 Language / Ngôn ngữ: [English](README.md) | **Tiếng Việt**

Đây là dự án demo API giọng nói theo hướng production, có thể tái lập trên một phiên Kaggle **T4 x2**. Hệ thống kết hợp **Whisper Large V3 Turbo**, **TranslateGemma 4B IT** và **VoxCPM2** phía sau một FastAPI coordinator, với quyền sở hữu GPU tường minh, bounded concurrency, request tracing, real-model acceptance và notebook Kaggle đã thực thi để làm evidence.

## Dự án chứng minh điều gì

Qualification đã lưu giữ cho thấy ba model có thể cùng tồn tại trên hai Tesla T4 mà không phải hoán đổi model giữa các request:

- **GPU 0** → TranslateGemma 4B IT qua Keras 3 / KerasHub / JAX;
- **GPU 1** → Whisper Large V3 Turbo + VoxCPM2 trong cùng một PyTorch worker thường trú;
- CPU → public coordinator, validation, admission control, đóng gói ZIP và tổng hợp health.

Khi các service ready, residency đã lưu là **13,865 MiB** trên GPU 0 và **6,871 MiB** trên GPU 1. Benchmark flagship gồm ba warm request có mean server pipeline **21,762.6 ms**; độ biến thiên lớn của TTS được giữ nguyên trong báo cáo thay vì loại bỏ. Hai flagship request khác input chạy đồng thời đã PASS với `PUBLIC_MAX_INFLIGHT=2`, request ID khác nhau, output ghép đúng theo từng request, không worker restart, không OOM và không trộn artifact chéo request.

Đây là số liệu acceptance cho đúng Kaggle runtime đã mô tả, không phải cam kết latency áp dụng cho mọi môi trường. **translation quality** cũng không được bảo đảm: benchmark cố ý ghi lại một output TranslateGemma còn mixed-language để thể hiện caveat chất lượng thật.

## Public API

Chỉ coordinator tại `127.0.0.1:8090` là public boundary.

| Endpoint | Mục đích |
| --- | --- |
| `GET /health/live` | kiểm tra coordinator còn sống |
| `GET /health/ready` | tổng hợp readiness của model worker |
| `POST /v1/audio/transcriptions` | audio tiếng Anh → transcript tiếng Anh |
| `POST /v1/audio/speech` | text tiếng Anh hoặc tiếng Việt → WAV |
| `POST /v1/audio/translate-and-speak` | audio tiếng Anh → transcript tiếng Anh → text tiếng Việt → ZIP speech tiếng Việt |

Flagship ZIP luôn chứa đúng bốn file:

- `transcript.en.txt`
- `translation.vi.txt`
- `speech.vi.wav`
- `metadata.json`

Mọi response từ coordinator đều có `X-Request-ID`.

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

Cold model load được stage có chủ đích:

```text
translation ready → speech ready → coordinator ready
```

Cách này tránh hiện tượng attached-model storage bị nghẽn nặng từng xảy ra khi hai model stack cold-read đồng thời.

Xem [docs/ARCHITECTURE.vi.md](docs/ARCHITECTURE.vi.md) để biết đầy đủ process/GPU contract.

## Khởi động nhanh trên Kaggle

### 1. Tạo Kaggle GPU notebook

Chọn accelerator **GPU T4 x2** và attach ba model input mà repository yêu cầu:

- TranslateGemma 4B IT Keras preset;
- Whisper Large V3 Turbo Transformers checkpoint;
- VoxCPM2 PyTorch checkpoint.

Cell đầu tiên của `notebooks/kaggle-production-showcase.ipynb` ghi rõ các attached-model path đã dùng cho acceptance run được lưu giữ.

### 2. Bootstrap runtime đã qualification

```bash
bash scripts/bootstrap_kaggle.sh
```

Bootstrap tách translation/JAX environment khỏi speech/PyTorch environment và pin các model-runtime version đã dùng trong Kaggle run được duyệt. `constraints-kaggle-tested.txt` ghi lại version evidence.

### 3. Preflight và start

```bash
bash scripts/preflight.sh
bash scripts/start.sh
```

`start.sh` chờ TranslateGemma ready trước khi load speech stack, sau đó chỉ start coordinator khi cả hai worker đã sẵn sàng.

### 4. Gọi API

Transcription:

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/transcriptions \
  -F 'file=@data/fixtures/english-short.wav' \
  -F 'language=en'
```

Vietnamese speech:

```bash
printf 'Xin chào từ Kaggle T4x2.' > /tmp/speech.txt
curl -sS -X POST http://127.0.0.1:8090/v1/audio/speech \
  -F 'file=@/tmp/speech.txt;type=text/plain' \
  -F 'language=vi' \
  -o /tmp/speech.vi.wav
```

Flagship pipeline audio tiếng Anh → speech tiếng Việt:

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/translate-and-speak \
  -F 'file=@data/fixtures/english-short.wav' \
  -o /tmp/translate-and-speak.zip
```

Xem [docs/API.vi.md](docs/API.vi.md) cho request/response contract đầy đủ.

## Real-model acceptance và benchmark

Trên Kaggle T4x2 sạch với model inputs đã attach:

```bash
bash scripts/acceptance_pipeline.sh
```

Nếu stack đã chạy và ready:

```bash
bash scripts/benchmark_pipeline.sh
```

Acceptance kiểm tra GPU ownership, worker survival, các path ASR/translation/TTS độc lập, flagship ZIP contract, concurrency với input khác nhau và cleanup GPU/port về baseline. Số liệu, startup behavior và quality caveat được ghi chi tiết trong [docs/BENCHMARKS.vi.md](docs/BENCHMARKS.vi.md).

## Production showcase notebook

- Source: `notebooks/kaggle-production-showcase.ipynb`
- Executed evidence đã lưu: `notebooks/kaggle-production-showcase-executed.ipynb`

Notebook thực hiện runtime/version evidence, kiểm tra attached model, preflight, CPU quality gate, staged startup bằng model thật, demo cả ba public API, bounded benchmark, optional authenticated tunnel và cleanup GPU/port cuối cùng.

## Security và Cloudflare tunnel tùy chọn

Local/private notebook mặc định tắt authentication. Không được expose chế độ này trực tiếp ra Internet.

Khi tạo public Quick Tunnel, authentication là bắt buộc:

```bash
export API_AUTH_REQUIRED=true
export ENABLE_CLOUDFLARE_TUNNEL=true
bash scripts/start.sh
bash scripts/run_tunnel.sh
```

Bearer key được sinh trong `runtime/api_key.txt` và không được commit hoặc in vào public notebook output. `scripts/run_tunnel.sh` sẽ từ chối chạy nếu chưa có `API_AUTH_REQUIRED=true`, và chỉ expose coordinator port 8090.

Xem [docs/SECURITY.vi.md](docs/SECURITY.vi.md).

## CPU CI và local quality gate

GitHub Actions không cố chạy GPU model acceptance. CI chỉ kiểm các contract có thể xác minh trên CPU:

```bash
ruff check .
ruff format --check src tests
pytest -q
for file in scripts/*.sh; do bash -n "$file"; done
python -m compileall -q src tests
git diff --check
```

Real-model behavior vẫn được chứng minh bằng Kaggle acceptance scripts và retained evidence.

## Tài liệu

- [Kiến trúc](docs/ARCHITECTURE.vi.md)
- [Public API](docs/API.vi.md)
- [Security](docs/SECURITY.vi.md)
- [T4x2 benchmark và acceptance evidence](docs/BENCHMARKS.vi.md)
- [Architecture English](docs/ARCHITECTURE.md)
- [API English](docs/API.md)
- [Security English](docs/SECURITY.md)
- [Benchmark English](docs/BENCHMARKS.md)

## Source license và model bên thứ ba

Phần source integration gốc của repository được phát hành theo [MIT License](LICENSE). License này không tái cấp phép model weights đã attach. TranslateGemma vẫn chịu Gemma Terms of Use; retained Whisper artifact ghi MIT và VoxCPM2 artifact ghi Apache-2.0. Hãy đọc [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) trước khi redistribute hoặc deploy.

## Trạng thái release readiness hiện tại

Repository hiện có CPU CI rõ ràng, tài liệu vận hành song ngữ, executed Kaggle evidence đã lưu, provenance model bên thứ ba và version evidence cho runtime đã acceptance. Việc publish/tag là release step riêng và chỉ nên thực hiện sau khi CI trên hosted repository PASS và final release audit hoàn tất.
