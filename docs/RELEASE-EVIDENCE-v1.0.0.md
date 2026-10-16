# Release evidence — v1.0.0

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](RELEASE-EVIDENCE-v1.0.0.vi.md)

## Qualified topology

- GPU 0: TranslateGemma 4B IT via Keras 3 / KerasHub / JAX.
- GPU 1: Whisper Large V3 Turbo + VoxCPM2 via persistent PyTorch worker.
- CPU: coordinator only.

## Readiness residency

| Device | Retained residency |
|---|---:|
| GPU 0 | 13,865 MiB |
| GPU 1 | 6,871 MiB |

## Warm flagship benchmark

Three retained sequential warm requests produced a mean server pipeline time of **21,762.6 ms**. Stage means were ASR 242.2 ms, translation 3,644.0 ms, and TTS 17,605.1 ms.

## Concurrency evidence

Two distinct-input requests completed with `PUBLIC_MAX_INFLIGHT=2`, distinct request IDs, correctly paired outputs, and no OOM, deadlock, worker restart, or cross-request mixing.

## Notebook evidence

- Source: `notebooks/kaggle-production-showcase.ipynb`
- Executed evidence: `notebooks/kaggle-production-showcase-executed.ipynb`
- Final marker retained: `KAGGLE_PRODUCTION_SHOWCASE=PASS`

## Caveat

The standalone translation case `Artificial intelligence can help people communicate across languages.` produced a partially mixed-language output. This is retained deliberately so the release does not confuse API/runtime qualification with universal translation-quality guarantees.
