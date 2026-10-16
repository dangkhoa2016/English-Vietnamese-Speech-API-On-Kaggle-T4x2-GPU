# Đóng góp

> 🌐 Language / Ngôn ngữ: [English](CONTRIBUTING.md) | **Tiếng Việt**

Trước khi mở thay đổi, hãy tái lập trên nhánh `main` hiện tại và giữ nguyên contract phân bổ thiết bị rõ ràng của repository, trừ khi thay đổi chủ động sửa contract đó.

## Quality gate

Chạy:

```bash
ruff check .
ruff format --check src tests
pytest -q
for file in scripts/*.sh; do bash -n "$file"; done
python -m compileall -q src tests
git diff --check
```

Thay đổi tác động đến hành vi model thật cần kèm evidence trên Kaggle T4x2. Mọi thay đổi tài liệu phải cập nhật bản English/Vietnamese tương ứng trong cùng change. Không commit model weights, credential, tunnel state, runtime log hoặc API key sinh tự động.
