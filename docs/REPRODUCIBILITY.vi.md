# Khả năng tái lập

> 🌐 Language / Ngôn ngữ: [English](REPRODUCIBILITY.md) | **Tiếng Việt**

Repository tách ba lớp evidence: source contract test được trên CPU, real Kaggle T4x2 acceptance và executed notebook evidence đã lưu. Một claim chỉ hợp lệ cho đúng lớp evidence thực sự tạo ra nó.

## Environment authority

`constraints-kaggle-tested.txt` ghi package version của runtime đã qualification. `scripts/bootstrap_kaggle.sh` tạo riêng translation/JAX environment và speech/PyTorch environment để tránh mơ hồ dependency hoặc CUDA ownership.

## Runtime authority

`bash scripts/preflight.sh` kiểm tra accelerator/model path bắt buộc. `bash scripts/acceptance_pipeline.sh` là đường real-model qualification; GitHub Actions cố ý không giả vờ tái lập GPU inference.

## Lưu giữ evidence

Source notebook được giữ riêng với `notebooks/kaggle-production-showcase-executed.ipynb`. Executed notebook là reviewer evidence và không được sửa hồi tố để tạo cảm giác nó được sinh từ runtime revision mới hơn.

## Độ biến thiên đã biết

Lần chạy TranslateGemma/JAX đầu tiên có thể bao gồm XLA compile đáng kể. Latency VoxCPM2 cũng biến thiên theo độ dài audio và hành vi model. Benchmark docs báo cáo các hiệu ứng này thay vì loại bỏ.
