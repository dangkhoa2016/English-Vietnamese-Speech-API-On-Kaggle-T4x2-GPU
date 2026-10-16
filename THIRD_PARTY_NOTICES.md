# Third-Party Notices

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](THIRD_PARTY_NOTICES.vi.md)

This file records the principal model/runtime provenance used by the retained Kaggle T4x2 acceptance. It is a practical attribution index, not legal advice and not a replacement for the upstream license text.

## TranslateGemma 4B IT

- Upstream model family: Google TranslateGemma 4B IT (`google/translategemma-4b-it`; runtime model id `keras/translategemma_4b_it`).
- Repository runtime form: Kaggle-attached Keras preset, loaded through Keras 3 / KerasHub / JAX.
- License/terms: **Gemma Terms of Use** (`license: gemma` in the upstream model card).
- Terms: https://ai.google.dev/gemma/terms
- Prohibited-use policy: https://ai.google.dev/gemma/prohibited_use_policy
- Model card: https://huggingface.co/google/translategemma-4b-it

The Gemma model terms apply independently of this repository's source-code license. Users must review and comply with those terms before using or redistributing the model weights.

## Whisper Large V3 Turbo

- Upstream: OpenAI Whisper / `openai/whisper-large-v3-turbo`.
- Repository runtime form: locally attached Transformers checkpoint.
- Model-card license metadata in the retained artifact: **MIT**.
- Upstream repository: https://github.com/openai/whisper
- Model card: https://huggingface.co/openai/whisper-large-v3-turbo

## VoxCPM2

- Upstream: OpenBMB VoxCPM2.
- Repository runtime form: locally attached model weights plus the published `voxcpm==2.0.3` Python package, whose upstream release source is commit `19b6bf7590025418821a86dcb817504e0ad7e5df`.
- Model-card license metadata in the retained artifact: **Apache-2.0**.
- Upstream repository: https://github.com/OpenBMB/VoxCPM
- Model card: https://huggingface.co/openbmb/VoxCPM2
- Apache-2.0 text: https://www.apache.org/licenses/LICENSE-2.0

## Python/runtime dependencies

FastAPI, Uvicorn, HTTPX, JAX, Keras, KerasHub, PyTorch, Transformers, SoundFile, librosa, Ruff, pytest, and their transitive dependencies retain their own upstream licenses. `constraints-kaggle-tested.txt` records versions observed in the qualified runtime; it does not alter dependency licensing.

## Redistribution

Before publishing a bundle that contains model weights, reproduce the applicable upstream license/notice obligations for that bundle. This repository intentionally keeps source integration artifacts separate from attached model inputs.
