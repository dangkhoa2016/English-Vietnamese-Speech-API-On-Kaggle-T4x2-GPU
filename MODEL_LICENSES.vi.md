# Giấy phép và nguồn gốc mô hình

> 🌐 Language / Ngôn ngữ: [English](MODEL_LICENSES.md) | **Tiếng Việt**

Repository này chứa mã tích hợp, test, script, tài liệu và notebook evidence. Giấy phép MIT chỉ áp dụng cho mã nguồn và tài liệu do dự án tự viết. MIT **does not relicense** / **không tái cấp phép** các trọng số mô hình của bên thứ ba.

## Danh mục mô hình

| Mô hình runtime | Định danh upstream | Điều khoản / giấy phép | Cách phân phối |
|---|---|---|---|
| TranslateGemma 4B IT | `google/translategemma-4b-it` | Gemma Terms of Use | Mô hình gắn ngoài; repository không tái cấp phép |
| Whisper Large V3 Turbo | `openai/whisper-large-v3-turbo` | MIT | Mô hình gắn ngoài; giữ nguyên giấy phép upstream |
| VoxCPM2 | `openbmb/VoxCPM2` | Apache-2.0 | Mô hình gắn ngoài; giữ nguyên giấy phép upstream |

## TranslateGemma 4B IT

Worker dịch sử dụng checkpoint TranslateGemma 4B IT thông qua Keras/KerasHub và Kaggle attached model. Trọng số chịu **Gemma Terms of Use**, không chịu MIT của repository này.

## Whisper Large V3 Turbo

Worker ASR sử dụng `openai/whisper-large-v3-turbo`. Metadata upstream của artifact đã qualification xác định giấy phép **MIT**. Repository không tuyên bố quyền tác giả đối với trọng số mô hình.

## VoxCPM2

Worker TTS sử dụng `openbmb/VoxCPM2`, với giấy phép upstream **Apache-2.0**. Source/runtime qualification được neo tại commit upstream:

`19b6bf7590025418821a86dcb817504e0ad7e5df`

## Tái phân phối

Trước khi tái phân phối model artifact hoặc gói dẫn xuất, cần kiểm tra lại giấy phép/điều khoản upstream hiện hành và giữ đầy đủ notice theo yêu cầu của chủ sở hữu. Trọng số mô hình được giữ ngoài source tree của repository này.
