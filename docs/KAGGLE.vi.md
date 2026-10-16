# Quy trình production trên Kaggle

> 🌐 Language / Ngôn ngữ: [English](KAGGLE.md) | **Tiếng Việt**

## Accelerator và model input

Dùng Kaggle **Tesla T4 x2**. Gắn TranslateGemma 4B IT Keras preset, Whisper Large V3 Turbo Transformers checkpoint và VoxCPM2 PyTorch checkpoint đã qualification trước khi chạy production showcase.

Notebook chuẩn: `notebooks/kaggle-production-showcase.ipynb`.

## Trình tự đã qualification

```bash
bash scripts/bootstrap_kaggle.sh
bash scripts/preflight.sh
bash scripts/start.sh
bash scripts/status.sh
```

Startup chờ translation ready trước khi bắt đầu speech stack và chỉ khởi động coordinator sau khi cả hai model worker ready. Trình tự này là có chủ đích vì parallel cold read đã gây attached-model storage contention nghiêm trọng trong qualification.

## Public demo

Coordinator local là `127.0.0.1:8090`. Quick Tunnel là tùy chọn và phải dùng cùng `API_AUTH_REQUIRED=true`. Không expose worker port 8091 hoặc 8092.

## Cleanup

Mọi reviewer-facing run cần kết thúc bằng `bash scripts/stop.sh`, sau đó xác nhận port được giải phóng và GPU model residency trở về zero.
