# Architecture

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](ARCHITECTURE.vi.md)

## Purpose

This repository runs an English/Vietnamese speech API on one Kaggle **T4 x2** session. The qualified design keeps model ownership explicit and exposes only the coordinator as the public boundary.

## Process and GPU ownership

| Process | Bind address | Accelerator | Models / responsibility |
| --- | --- | --- | --- |
| Coordinator | `127.0.0.1:8090` | CPU | public REST API, validation, request IDs, admission, artifact packaging |
| Translation worker | `127.0.0.1:8091` | physical **GPU 0** | **TranslateGemma 4B IT** through Keras 3 / **KerasHub** with the **JAX** CUDA backend |
| Speech worker | `127.0.0.1:8092` | physical **GPU 1** | **Whisper Large V3 Turbo** ASR + **VoxCPM2** TTS in one persistent PyTorch process |

`CUDA_VISIBLE_DEVICES` isolates the workers. Inside the speech worker, physical GPU 1 is intentionally exposed as logical `cuda:0`.

## Flagship request path

`POST /v1/audio/translate-and-speak` executes this fixed pipeline:

1. validate upload;
2. normalize audio for ASR;
3. Whisper: English audio → English transcript;
4. TranslateGemma: English transcript → Vietnamese text;
5. VoxCPM2: Vietnamese text → Vietnamese WAV;
6. coordinator packages transcript, translation, WAV, and metadata into one ZIP response.

Worker-local model inference is serialized. The public coordinator has a bounded admission queue; retained T4x2 evidence qualifies two simultaneous public requests without cross-request artifact mixing. See [BENCHMARKS.md](BENCHMARKS.md).

## Startup sequence

Kaggle attached-model storage showed severe cold-read contention when both model stacks loaded at once. `scripts/start.sh` therefore uses the qualified staged sequence:

`translation ready → speech ready → coordinator ready`

The coordinator starts only after both model workers are ready. This is deliberate reliability behavior, not cosmetic sequencing.

## Public and internal boundaries

Only port **8090** is a public candidate. Ports **8091** and **8092** are internal loopback services and must not be tunneled or exposed directly. Optional Cloudflare Quick Tunnel targets `127.0.0.1:8090` only and is fail-closed unless API authentication is enabled.

## Lifecycle

- `scripts/preflight.sh`: T4x2/runtime validation.
- `scripts/start.sh`: staged service startup.
- `scripts/status.sh`: process/readiness inspection.
- `scripts/stop.sh`: coordinated shutdown.
- `scripts/acceptance_pipeline.sh`: real-model T4x2 acceptance.
- `scripts/benchmark_pipeline.sh`: retained benchmark/qualification workflow.
