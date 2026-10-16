# Quy trình production trên Kaggle

> 🌐 Language / Ngôn ngữ: [English](KAGGLE.md) | **Tiếng Việt**

## Trước khi chạy

Dùng Kaggle notebook **Tesla T4 x2** và giữ **Internet = On** để Git checkout và Cloudflare Quick Tunnel tùy chọn có thể hoạt động.

### Attach ba Kaggle Model bắt buộc và qualified runtime Dataset

Mở panel **Add Input** của notebook, chọn **Models** và attach chính xác các lựa chọn dưới đây trước khi chạy code:

| Model | Kaggle owner/resource | Framework | Variation | Version | Mount mong đợi |
| --- | --- | --- | --- | --- | --- |
| TranslateGemma 4B IT | `keras/translategemma` | Keras | `translategemma_4b_it` | `1` | `/kaggle/input/models/keras/translategemma/keras/translategemma_4b_it/1` |
| Whisper Large V3 Turbo | `dangkhoa2016/openai-whisper-large-v3-turbo` | Transformers | `default` | `1` | `/kaggle/input/models/dangkhoa2016/openai-whisper-large-v3-turbo/transformers/default/1` |
| VoxCPM2 | `dangkhoa2016/openbmb-voxcpm2` | PyTorch | `default` | `1` | `/kaggle/input/models/dangkhoa2016/openbmb-voxcpm2/pytorch/default/1` |

Cách tìm nhanh:

```text
Add Input → Models
Search: keras/translategemma
Framework: Keras
Variation: translategemma_4b_it
Version: 1

Add Input → Models
Search: dangkhoa2016/openai-whisper-large-v3-turbo
Framework: Transformers
Variation: default
Version: 1

Add Input → Models
Search: dangkhoa2016/openbmb-voxcpm2
Framework: PyTorch
Variation: default
Version: 1
```

Sau đó chọn **Add Input → Datasets** và attach `dangkhoa2016/english-vietnamese-speech-api-qualified-runtime`, Version 1. Dataset chỉ cung cấp một file bất biến `envi-speech-runtime-v1.bundle`, bên trong chứa public wheelhouse đã audit, exact manifests, SHA-256/license inventory và các PyTorch/Torchaudio wheel `+cu128` đã bảo toàn tên file. Bootstrap giải nén file này vào `/tmp/envi-speech-runtime-v1`; NVIDIA/vendor wheel vẫn được pin chính xác và tải từ official package indexes. Bootstrap hiện ưu tiên package manager `uv` đã có sẵn trong Kaggle image, vì vậy có thể tạo Python 3.12 environment mà không chạy `apt` hoặc cần `python3.12-venv`. Script in thời gian giải nén archive, cài translation, cài speech vendor/public và tổng thời gian bootstrap để mỗi lần Run All cho thấy rõ startup time nằm ở đâu. Số đo 302 giây trước đây thuộc layout multi-file đã bị thay thế và không được dùng làm claim cho đường chạy hiện tại.

Kaggle mount input đã attach bên dưới **`/kaggle/input` ở chế độ read-only**. Ứng dụng đọc model weight trực tiếp từ các mount này. Không clone source, tạo virtual environment, ghi log hoặc sinh WAV/ZIP artifact dưới `/kaggle/input`.

Dùng **`/tmp`** cho runtime package đã giải nén, cả hai virtual environment và package/model cache. Chỉ dùng **`/kaggle/working`** cho repository checkout và evidence/output cần lưu bền như log, audio sinh ra, ZIP response, benchmark artifact, executed notebook và HTML export.

Source notebook chuẩn: `notebooks/kaggle-production-showcase.ipynb`.

Repository theo dõi source notebook có thể tái sử dụng như một project artifact. Nếu người dùng muốn chia sẻ exported executed copy thì đó chỉ là snapshot tùy chọn của một lần chạy cụ thể; nó không bắt buộc để sử dụng, tái lập hoặc mở rộng dự án và không thay thế source notebook.

## Trình tự đã qualification

```bash
bash scripts/bootstrap_kaggle.sh
bash scripts/preflight.sh
bash scripts/start.sh
bash scripts/status.sh
```

Startup chờ translation ready trước khi bắt đầu speech stack và chỉ khởi động coordinator sau khi cả hai model worker ready. Trình tự này là có chủ đích vì parallel cold read đã gây attached-model storage contention nghiêm trọng trong qualification.

## Public demo

Coordinator local là `127.0.0.1:8090`. Quick Tunnel là tùy chọn và phải dùng cùng `API_AUTH_REQUIRED=true`. Không expose worker port `8091` hoặc `8092`.

## Cleanup

Mọi production-showcase run cần kết thúc bằng `bash scripts/stop.sh`, sau đó xác nhận port được giải phóng và GPU model residency trở về zero.
