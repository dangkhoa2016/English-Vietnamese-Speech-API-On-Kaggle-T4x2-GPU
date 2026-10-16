# Contributing

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](CONTRIBUTING.vi.md)

Contributions are welcome when they preserve the repository's evidence-first approach. Changes should be scoped, reproducible, and explicit about their impact on API behavior, GPU ownership, model provenance, security, and retained Kaggle evidence.

## Development contract

1. Work from the current `main` revision.
2. Keep code changes reviewable; avoid unrelated refactors in the same commit.
3. Update English and Vietnamese documentation together.
4. Never add model weights, credentials, generated keys, runtime logs, or private voice data.
5. Run the CPU quality gate locally.
6. For model/runtime changes, attach real Kaggle T4x2 evidence before making qualification claims.

## Local gate

```bash
ruff check .
ruff format --check src tests
pytest -q
for file in scripts/*.sh; do bash -n "$file"; done
python -m compileall -q src tests
git diff --check
```

See [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) for pull-request expectations.
