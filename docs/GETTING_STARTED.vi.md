# Hướng dẫn bắt đầu

Tài liệu này hướng dẫn cách thiết lập và chạy English–Vietnamese Speech API trên Kaggle T4 x2. Nội dung bao gồm Kaggle inputs, bootstrap runtime, khởi động service, smoke test API, real-model acceptance, benchmark, public tunnel tùy chọn và CPU quality gate.

## 1. Chuẩn bị Kaggle notebook T4x2

Chọn **Accelerator → GPU T4 x2** và giữ **Internet = On**.

Trong panel **Input** của Kaggle, chọn **Add Input → Models** và attach các model input sau:

| Model | Kaggle resource | Framework | Variation | Version | Read-only mount dự kiến |
| --- | --- | --- | --- | --- | --- |
| TranslateGemma 4B IT | `keras/translategemma` | Keras | `translategemma_4b_it` | `1` | `/kaggle/input/models/keras/translategemma/keras/translategemma_4b_it/1` |
| Whisper Large V3 Turbo | `dangkhoa2016/openai-whisper-large-v3-turbo` | Transformers | `default` | `1` | `/kaggle/input/models/dangkhoa2016/openai-whisper-large-v3-turbo/transformers/default/1` |
| VoxCPM2 | `dangkhoa2016/openbmb-voxcpm2` | PyTorch | `default` | `1` | `/kaggle/input/models/dangkhoa2016/openbmb-voxcpm2/pytorch/default/1` |

Đồng thời attach Dataset `dangkhoa2016/english-vietnamese-speech-api-qualified-runtime`, Version 1. Dataset cung cấp payload bất biến `envi-speech-runtime-v1.bundle` dùng cho qualified bootstrap path.

Kaggle input là read-only. Repository checkout và output cần lưu bền nằm dưới `/kaggle/working`; extracted package, virtual environment và cache nằm dưới `/tmp`.

Xem [KAGGLE.vi.md](KAGGLE.vi.md) để biết đầy đủ mount behavior và hướng dẫn khôi phục.

## 2. Bootstrap runtime đã qualification

```bash
bash scripts/bootstrap_kaggle.sh
```

Bootstrap tạo riêng translation/JAX environment và speech/PyTorch environment. Trên Kaggle, script ưu tiên package manager `uv` có sẵn, không thay đổi system bằng `apt`, giải nén qualified runtime archive dưới `/tmp`, cài public package từ wheelhouse đã attach và chỉ tải exact-pinned NVIDIA/vendor wheel từ official index.

Các marker hữu ích trong output:

```text
BOOTSTRAP_VENV_BACKEND=uv
RUNTIME_SOURCE=KAGGLE_SINGLE_ARCHIVE
TMP_RUNTIME_LAYOUT=PASS
RUNTIME_ARCHIVE_EXTRACT_SECONDS=...
TRANSLATION_INSTALL_SECONDS=...
SPEECH_VENDOR_INSTALL_SECONDS=...
SPEECH_PUBLIC_INSTALL_SECONDS=...
BOOTSTRAP_TOTAL_SECONDS=...
BOOTSTRAP_KAGGLE=PASS
```

## 3. Chạy preflight và khởi động service

```bash
bash scripts/preflight.sh
bash scripts/start.sh
```

Startup được stage có chủ đích:

```text
translation ready → speech ready → coordinator ready
```

Public coordinator lắng nghe tại `127.0.0.1:8090`. Hai worker nội bộ dùng port `8091` và `8092`.

## 4. Thử public API

### Transcription tiếng Anh

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/transcriptions \
  -F 'file=@data/fixtures/english-short.wav' \
  -F 'language=en'
```

### Speech tiếng Việt

```bash
printf 'Xin chào từ Kaggle T4x2.' > /tmp/speech.txt
curl -sS -X POST http://127.0.0.1:8090/v1/audio/speech \
  -F 'file=@/tmp/speech.txt;type=text/plain' \
  -F 'language=vi' \
  -o /tmp/speech.vi.wav
```

### Audio tiếng Anh → speech tiếng Việt

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/translate-and-speak \
  -F 'file=@data/fixtures/english-short.wav' \
  -o /tmp/translate-and-speak.zip
```

Xem [API.vi.md](API.vi.md) để biết đầy đủ request/response contract.

## 5. Chạy real-model acceptance và benchmark

Trên một Kaggle T4x2 session sạch với đầy đủ input đã attach:

```bash
bash scripts/acceptance_pipeline.sh
```

Nếu qualified stack đã chạy:

```bash
bash scripts/benchmark_pipeline.sh
```

Acceptance kiểm tra GPU ownership, worker survival, các path ASR/translation/TTS độc lập, flagship ZIP structure, concurrency với input khác nhau và cleanup. Các số liệu được lưu giữ cùng quality caveat nằm trong [BENCHMARKS.vi.md](BENCHMARKS.vi.md).

## 6. Cloudflare tunnel có authentication, tùy chọn

Local/private notebook không cần public authentication. Không expose chế độ đó trực tiếp ra Internet.

Để tạo public Quick Tunnel:

```bash
export API_AUTH_REQUIRED=true
export ENABLE_CLOUDFLARE_TUNNEL=true
bash scripts/start.sh
bash scripts/run_tunnel.sh
```

Bearer key nằm trong `runtime/api_key.txt`. Không commit hoặc in key vào public notebook output. Xem [SECURITY.vi.md](SECURITY.vi.md).

## 7. CPU quality gate

CPU-testable gate của repository:

```bash
ruff check .
ruff format --check src tests
pytest -q
for file in scripts/*.sh; do bash -n "$file"; done
python -m compileall -q src tests
git diff --check
```

GitHub Actions xác minh CPU contract này. GPU model qualification vẫn là workflow chạy trên Kaggle T4x2.

## 8. Cleanup

Luôn dừng service sau mỗi lần chạy:

```bash
bash scripts/stop.sh
```

Xác nhận port đã được giải phóng và GPU model residency trở về baseline. Xem [KAGGLE.vi.md](KAGGLE.vi.md) và [TROUBLESHOOTING.vi.md](TROUBLESHOOTING.vi.md) để biết chi tiết vận hành.
