# Khả năng tái lập

> 🌐 Language / Ngôn ngữ: [English](REPRODUCIBILITY.md) | **Tiếng Việt**

Repository tách source contract có thể test trên CPU khỏi runtime qualification thực tế trên Kaggle T4x2. Mỗi benchmark, acceptance hoặc performance claim chỉ áp dụng cho đúng lần chạy và môi trường đã thực sự tạo ra kết quả đó.

## Environment authority

`constraints-kaggle-tested.txt` ghi package version của runtime đã qualification. `scripts/bootstrap_kaggle.sh` tạo riêng translation/JAX environment và speech/PyTorch environment để tránh mơ hồ dependency hoặc CUDA ownership. Trên Kaggle, script ưu tiên package manager `uv` có sẵn để tạo/cài Python 3.12 environment nhanh hơn mà không thay đổi system package bằng `apt`; các phase timer giúp quan sát chi phí bootstrap. Public Kaggle Dataset `dangkhoa2016/english-vietnamese-speech-api-qualified-runtime` cache các Python 3.12 wheel public/open-source cùng SHA-256 và license inventory; NVIDIA/vendor wheels được chủ động loại khỏi dataset và tải đúng pinned version từ official indexes.

## Runtime authority

`bash scripts/preflight.sh` kiểm tra accelerator/model path bắt buộc. `bash scripts/acceptance_pipeline.sh` là đường real-model qualification; GitHub Actions cố ý không giả vờ tái lập GPU inference.

## Lưu giữ evidence

Repository theo dõi source notebook có thể tái sử dụng `notebooks/kaggle-production-showcase.ipynb`. Nếu exported executed copy được chia sẻ thì đó chỉ là snapshot tùy chọn của từng lần chạy, không phải dependency của dự án; khả năng tái lập đến từ source, runtime input được pin, quy trình được tài liệu hóa và các kết quả qualification có phạm vi rõ ràng.

## Độ biến thiên đã biết

Lần chạy TranslateGemma/JAX đầu tiên có thể bao gồm XLA compile đáng kể. Latency VoxCPM2 cũng biến thiên theo độ dài audio và hành vi model. Benchmark docs báo cáo các hiệu ứng này thay vì loại bỏ.
