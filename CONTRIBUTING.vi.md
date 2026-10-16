# Đóng góp

> 🌐 Language / Ngôn ngữ: [English](CONTRIBUTING.md) | **Tiếng Việt**

Dự án hoan nghênh đóng góp khi vẫn giữ nguyên nguyên tắc evidence-first. Mỗi thay đổi cần có phạm vi rõ, có thể tái lập và nói rõ tác động đến API, GPU ownership, model provenance, bảo mật và Kaggle evidence đã lưu.

## Contract phát triển

1. Bắt đầu từ revision `main` hiện tại.
2. Giữ code change dễ review; không trộn refactor không liên quan vào cùng commit.
3. Cập nhật tài liệu English và Vietnamese đồng thời.
4. Không thêm model weights, credential, key sinh tự động, runtime log hoặc dữ liệu giọng nói riêng tư.
5. Chạy CPU quality gate ở local.
6. Với thay đổi model/runtime, cần có real Kaggle T4x2 evidence trước khi tuyên bố qualification.

## Local gate

```bash
ruff check .
ruff format --check src tests
pytest -q
for file in scripts/*.sh; do bash -n "$file"; done
python -m compileall -q src tests
git diff --check
```

Xem [.github/CONTRIBUTING.vi.md](.github/CONTRIBUTING.vi.md) để biết yêu cầu đối với pull request.
