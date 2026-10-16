# Pull request

> 🌐 Language / Ngôn ngữ: [English](PULL_REQUEST_TEMPLATE.md) | **Tiếng Việt**

## Tóm tắt
Mô tả thay đổi kỹ thuật và lý do cần thay đổi.

## Tác động đến contract
- [ ] GPU ownership vẫn rõ ràng, hoặc mapping mới đã được tài liệu hóa.
- [ ] Không thêm model weights, credential, runtime log hoặc key sinh tự động.
- [ ] Tác động đến model-license/provenance đã được ghi rõ khi có liên quan.
- [ ] Tài liệu EN/VI được cập nhật đồng thời.
- [ ] Public tunnel vẫn fail-closed và bắt buộc authentication.

## Bằng chứng
Liệt kê chính xác lệnh test, Kaggle evidence khi áp dụng và measured outputs. Không dùng CPU CI để tuyên bố real-model qualification.
