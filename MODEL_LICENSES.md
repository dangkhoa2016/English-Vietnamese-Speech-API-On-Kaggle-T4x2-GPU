# Model licenses and provenance

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](MODEL_LICENSES.vi.md)

This repository contains integration code, tests, scripts, documentation, and notebook evidence. Its MIT License applies only to project-authored source and documentation. It **does not relicense** third-party model weights.

## Model inventory

| Runtime model | Upstream identity | Terms / license | Distribution posture |
|---|---|---|---|
| TranslateGemma 4B IT | `google/translategemma-4b-it` | Gemma Terms of Use | External/attached model; not relicensed by this repository |
| Whisper Large V3 Turbo | `openai/whisper-large-v3-turbo` | MIT | External/attached model; upstream license preserved |
| VoxCPM2 | `openbmb/VoxCPM2` | Apache-2.0 | External/attached model; upstream license preserved |

## TranslateGemma 4B IT

The translation worker uses the Keras/KerasHub TranslateGemma 4B IT checkpoint attached in Kaggle. The model is governed by the **Gemma Terms of Use**, not by this repository's MIT License. Users are responsible for obtaining and using the checkpoint under the applicable upstream terms.

## Whisper Large V3 Turbo

The speech-recognition worker uses `openai/whisper-large-v3-turbo`. The retained attached-model metadata identifies the upstream model license as **MIT**. The model remains a third-party work; the project MIT license does not claim authorship of the weights.

## VoxCPM2

The speech-synthesis worker uses `openbmb/VoxCPM2`, with upstream licensing identified as **Apache-2.0**. Runtime/source qualification for the retained implementation is anchored at upstream commit:

`f772e498a45fbb5fb8e13fbf9b9c48be9fe33e69`

## Redistribution

Before redistributing model artifacts or derived packages, verify the current upstream license/terms and preserve all notices required by the upstream owner. This repository intentionally keeps model weights outside the source tree.
