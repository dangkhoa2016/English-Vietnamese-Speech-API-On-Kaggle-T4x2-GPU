# Quy trình production trên Kaggle

> 🌐 Language / Ngôn ngữ: [English](KAGGLE.md) | **Tiếng Việt**

## Trước khi chạy

Dùng Kaggle notebook **Tesla T4 x2** và giữ **Internet = On** để Git checkout và Cloudflare Quick Tunnel tùy chọn có thể hoạt động.

### Attach ba Kaggle Model bắt buộc

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

Kaggle mount input đã attach bên dưới **`/kaggle/input` ở chế độ read-only**. Ứng dụng đọc model weight trực tiếp từ các mount này. Không clone source, tạo virtual environment, ghi log hoặc sinh WAV/ZIP artifact dưới `/kaggle/input`.

Dùng **`/kaggle/working`** cho mọi dữ liệu cần ghi: repository checkout, `.venv`, `.venv-speech`, runtime state, log, audio sinh ra, ZIP response và benchmark artifact.

Source notebook chuẩn: `notebooks/kaggle-production-showcase.ipynb`.

Repository chủ đích **không commit executed notebook**. Executed production-demo notebook/evidence artifact mới cần được tạo riêng từ một lần chạy Kaggle T4 x2 thật để published evidence không bị nhầm với template có thể chỉnh sửa.

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

Mọi reviewer-facing run cần kết thúc bằng `bash scripts/stop.sh`, sau đó xác nhận port được giải phóng và GPU model residency trở về zero.
