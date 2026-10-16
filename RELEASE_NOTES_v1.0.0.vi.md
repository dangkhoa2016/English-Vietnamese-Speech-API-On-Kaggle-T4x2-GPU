# Ghi chú phát hành v1.0.0

> 🌐 Language / Ngôn ngữ: [English](RELEASE_NOTES_v1.0.0.md) | **Tiếng Việt**

`v1.0.0` là bản qualification public đầu tiên của English–Vietnamese Speech API trên Kaggle T4x2.

## Kiến trúc runtime

- Physical GPU 0: TranslateGemma 4B IT, Keras 3 / KerasHub / JAX CUDA.
- Physical GPU 1: Whisper Large V3 Turbo + VoxCPM2, persistent PyTorch worker.
- CPU: FastAPI coordinator, media validation, admission control, tracing, ZIP packaging và health aggregation.

Startup được staging có chủ đích: `translation ready → speech ready → coordinator ready`.

## Public API

- `GET /health/live`
- `GET /health/ready`
- `POST /v1/audio/transcriptions`
- `POST /v1/audio/speech`
- `POST /v1/audio/translate-and-speak`

Flagship ZIP chứa `transcript.en.txt`, `translation.vi.txt`, `speech.vi.wav` và `metadata.json`.

## Qualification đã lưu

- GPU 0: 13,865 MiB resident khi ready.
- GPU 1: 6,871 MiB resident khi ready.
- Warm flagship mean server time: 21,762.6 ms trên ba request đã lưu.
- Distinct-input concurrency: PASS với `PUBLIC_MAX_INFLIGHT=2`.
- Không OOM, worker restart, deadlock hoặc cross-request artifact mixing trong acceptance đã lưu.

Dự án không overclaim translation quality: một standalone translation đã lưu vẫn còn mixed-language một phần và được ghi rõ như quality caveat.

## Licensing

Mã nguồn do dự án tự viết dùng MIT của Đăng Khoa <i.am@dangkhoa.dev>. Model weights bên thứ ba giữ nguyên điều khoản upstream; xem [MODEL_LICENSES.vi.md](MODEL_LICENSES.vi.md).
