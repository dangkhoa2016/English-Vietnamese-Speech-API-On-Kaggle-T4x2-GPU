# Thông báo thành phần bên thứ ba

> 🌐 Language / Ngôn ngữ: [English](THIRD_PARTY_NOTICES.md) | **Tiếng Việt**

Tài liệu này là danh mục thông tin, không thay thế văn bản giấy phép hoặc điều khoản do từng upstream cung cấp.

## Mô hình

| Thành phần | Vai trò | Giấy phép / điều khoản upstream |
|---|---|---|
| TranslateGemma 4B IT | Dịch EN ↔ VI | Gemma Terms of Use |
| Whisper Large V3 Turbo | Nhận dạng tiếng Anh/Việt | MIT |
| VoxCPM2 | Tổng hợp giọng nói EN/VI | Apache-2.0 |

Repository không phân phối lại và **không tái cấp phép** các trọng số mô hình này dưới MIT của mã nguồn dự án.

VoxCPM2 runtime dùng package phát hành `voxcpm==2.0.3`, với source release upstream tại commit `19b6bf7590025418821a86dcb817504e0ad7e5df`.

## Thư viện runtime

FastAPI, Uvicorn, JAX, Keras, KerasHub, PyTorch, Transformers, librosa, soundfile và các dependency khác vẫn chịu giấy phép upstream riêng.

## Nền tảng bên ngoài

Kaggle, GitHub Actions và Cloudflare Quick Tunnel chịu điều khoản dịch vụ tương ứng của nhà cung cấp.
