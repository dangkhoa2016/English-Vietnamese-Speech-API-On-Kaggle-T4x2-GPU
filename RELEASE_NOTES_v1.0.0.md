# v1.0.0 release notes

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](RELEASE_NOTES_v1.0.0.vi.md)

`v1.0.0` is the first public qualification release of the English–Vietnamese Speech API on Kaggle T4x2.

## Runtime architecture

- Physical GPU 0: TranslateGemma 4B IT, Keras 3 / KerasHub / JAX CUDA.
- Physical GPU 1: Whisper Large V3 Turbo + VoxCPM2, persistent PyTorch worker.
- CPU: FastAPI coordinator, media validation, admission control, tracing, ZIP packaging, and health aggregation.

Startup is deliberately staged: `translation ready → speech ready → coordinator ready`.

## Public API

- `GET /health/live`
- `GET /health/ready`
- `POST /v1/audio/transcriptions`
- `POST /v1/audio/speech`
- `POST /v1/audio/translate-and-speak`

The flagship ZIP contains `transcript.en.txt`, `translation.vi.txt`, `speech.vi.wav`, and `metadata.json`.

## Retained qualification

- GPU 0: 13,865 MiB resident at readiness.
- GPU 1: 6,871 MiB resident at readiness.
- Warm flagship mean server time: 21,762.6 ms over three retained requests.
- Distinct-input concurrency: PASS with `PUBLIC_MAX_INFLIGHT=2`.
- No OOM, worker restart, deadlock, or cross-request artifact mixing in retained acceptance.

Translation quality is not overclaimed: one retained standalone translation remained partially mixed-language and is documented as a quality caveat.

## Licensing

Project-authored source is MIT licensed to Đăng Khoa <i.am@dangkhoa.dev>. Third-party model weights retain their upstream terms; see [MODEL_LICENSES.md](MODEL_LICENSES.md).
