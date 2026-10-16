# Contributing

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](CONTRIBUTING.vi.md)

Before opening a change, reproduce it against the current `main` branch and keep the repository's explicit device contract intact unless the change intentionally revises that contract.

## Quality gate

Run:

```bash
ruff check .
ruff format --check src tests
pytest -q
for file in scripts/*.sh; do bash -n "$file"; done
python -m compileall -q src tests
git diff --check
```

Changes affecting real-model behavior should include Kaggle T4x2 evidence. Documentation changes must update the English/Vietnamese counterpart in the same change. Do not commit model weights, credentials, tunnel state, runtime logs, or generated API keys.
