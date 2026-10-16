# Khả năng tái lập

> 🌐 Language / Ngôn ngữ: [English](REPRODUCIBILITY.md) | **Tiếng Việt**

Repository tách ba lớp evidence: source contract test được trên CPU, real Kaggle T4x2 acceptance và fresh executed production evidence được tạo riêng trên Kaggle. Một claim chỉ hợp lệ cho đúng lớp evidence thực sự tạo ra nó.

## Environment authority

`constraints-kaggle-tested.txt` ghi package version của runtime đã qualification. `scripts/bootstrap_kaggle.sh` tạo riêng translation/JAX environment và speech/PyTorch environment để tránh mơ hồ dependency hoặc CUDA ownership. Public Kaggle Dataset `dangkhoa2016/english-vietnamese-speech-api-qualified-runtime` cache các Python 3.12 wheel public/open-source cùng SHA-256 và license inventory; NVIDIA/vendor wheels được chủ động loại khỏi dataset và tải đúng pinned version từ official indexes.

## Runtime authority

`bash scripts/preflight.sh` kiểm tra accelerator/model path bắt buộc. `bash scripts/acceptance_pipeline.sh` là đường real-model qualification; GitHub Actions cố ý không giả vờ tái lập GPU inference.

## Lưu giữ evidence

Repository chỉ commit source template `notebooks/kaggle-production-showcase.ipynb`. Fresh executed production-demo notebook/evidence artifact được tạo riêng từ một lần chạy Kaggle T4 x2 thật và không commit, nhờ đó editable source và runtime evidence luôn tách biệt rõ ràng.

## Độ biến thiên đã biết

Lần chạy TranslateGemma/JAX đầu tiên có thể bao gồm XLA compile đáng kể. Latency VoxCPM2 cũng biến thiên theo độ dài audio và hành vi model. Benchmark docs báo cáo các hiệu ứng này thay vì loại bỏ.
