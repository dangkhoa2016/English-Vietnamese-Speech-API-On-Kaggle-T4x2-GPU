# T4x2 Acceptance and Benchmark Evidence

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](BENCHMARKS.vi.md)

## Scope

This document records retained, measured evidence for the English→Vietnamese speech pipeline on a Kaggle **2× NVIDIA Tesla T4** runtime. It is an acceptance result for this exact runtime and fixture, not a general performance guarantee.

Qualified model placement:

- physical GPU 0: TranslateGemma 4B IT (`keras/translategemma_4b_it`) through Keras 3 / KerasHub with the JAX/XLA CUDA backend;
- physical GPU 1: Whisper Large V3 Turbo (`openai/whisper-large-v3-turbo`) and VoxCPM2 (`openbmb/VoxCPM2`) resident together;
- CPU: FastAPI coordinator.

The measured flagship fixture is `data/fixtures/english-short.wav`, **4.64 s**, normalized to PCM s16le, mono, 16 kHz before ASR.

## Qualification procedure

The retained Task 12 run used `scripts/acceptance_pipeline.sh`, which:

1. required a clean GPU baseline;
2. cold-started TranslateGemma and waited for readiness before loading the speech stack, avoiding attached-model storage I/O contention;
3. captured worker PIDs and verified physical GPU ownership;
4. ran one flagship warmup request;
5. ran three measured sequential flagship requests;
6. alternated standalone transcription, translation, English TTS, and Vietnamese TTS requests;
7. submitted two flagship requests simultaneously;
8. verified worker PID survival;
9. stopped the services and verified GPU/port cleanup.

Machine-readable request evidence is written to `runtime/benchmark-pipeline/results.json` by `scripts/benchmark_pipeline.sh`.

## Residency evidence

At service readiness:

| GPU | Role | Used VRAM |
| --- | --- | ---: |
| GPU 0 | TranslateGemma 4B IT | 13,865 MiB |
| GPU 1 | Whisper + VoxCPM2 | 6,871 MiB |

After the benchmark workload:

| GPU | Used VRAM |
| --- | ---: |
| GPU 0 | 13,897 MiB |
| GPU 1 | 7,839 MiB |

The translation worker stayed on physical GPU 0, the speech worker stayed on physical GPU 1, and the CPU coordinator did not own a GPU. Worker PIDs survived the full benchmark. No OOM or worker restart occurred. After shutdown, both GPUs returned to **0 MiB used** and ports 8090–8092 were released.

## Flagship warmup

The first request includes JAX/XLA compilation and other cold-path effects and is therefore reported separately from steady-state measurements.

| Metric | Warmup |
| --- | ---: |
| ASR | 1,926.2 ms |
| Translation | 62,033.4 ms |
| TTS | 9,976.0 ms |
| Server pipeline total | 74,210.8 ms |
| Client-observed total | 74,432.9 ms |

Warmup translation:

> Chào bạn. Đây là giọng nói tiếng Anh tổng hợp ngắn để kiểm tra dịch.

## Sequential flagship benchmark

Three measured warm requests were run after the warmup.

| Stage | Mean | Min | Max |
| --- | ---: | ---: | ---: |
| ASR | 242.2 ms | 241.6 ms | 242.5 ms |
| Translation | 3,644.0 ms | 3,627.7 ms | 3,657.8 ms |
| TTS | 17,605.1 ms | 9,777.0 ms | 32,927.1 ms |
| Server pipeline total | **21,762.6 ms** | **13,959.0 ms** | **37,065.4 ms** |

Per-request client totals were 37,274.1 ms, 14,428.6 ms, and 14,114.2 ms. All three requests returned the expected four-member ZIP artifact and the same English transcript and Vietnamese translation.

TTS latency was the dominant source of variance in this retained run: the first measured TTS output was 14.88 s long, while the next two were 4.48 s and 4.32 s. The benchmark reports this variability rather than discarding the slower valid sample.

## Standalone alternation

The same resident workers were then exercised with the standalone paths.

| Capability | Measurement |
| --- | ---: |
| English transcription | 641.6 ms client total; 244.9 ms model inference |
| EN→VI translation | 3,209.7 ms client total; 3,198.3 ms model inference |
| English TTS | 7,678.2 ms client total; 322,604-byte WAV |
| Vietnamese TTS | 4,769.2 ms client total; 199,724-byte WAV |

The standalone translation sample returned:

> Artificial intelligence có thể giúp mọi người giao tiếp bằng nhiều ngôn ngữ.

This is technically valid Vietnamese output but leaves “Artificial intelligence” untranslated. Translation quality therefore remains a human-review concern; the technical PASS is not a claim of perfect translation quality.

## Two-request concurrency qualification

Two flagship requests with **different English audio inputs** were submitted simultaneously with `PUBLIC_MAX_INFLIGHT=2`. Request 1 used the retained ASR fixture; request 2 used the English WAV synthesized during the standalone TTS step.

| Request | Client total | Server total | Request ID | Result |
| --- | ---: | ---: | --- | --- |
| concurrent-1 | 19,329.0 ms | 18,797.3 ms | `46aaf120-3320-470f-b4d7-6b98ac89c787` | PASS |
| concurrent-2 | 9,042.5 ms | 8,888.5 ms | `73224e72-634b-4f65-acf2-4a51762a4561` | PASS |

Qualification result: **PASS**.

Evidence:

- two distinct request IDs;
- distinct input audio produced distinct, correctly paired transcript/translation artifacts for both requests;
- no OOM;
- no deadlock;
- no worker restart;
- no cross-request artifact mixing;
- worker PIDs survived the concurrent test;
- cleanup returned both GPUs and all three ports to baseline.

Based on this retained evidence, the v1 default may remain `PUBLIC_MAX_INFLIGHT=2` with `PUBLIC_MAX_PENDING=2`. GPU-local model inference remains serialized by each worker's concurrency policy.

## Startup behavior

Kaggle attached-model storage showed substantial cold-read variability. Loading TranslateGemma and the speech stack concurrently caused both workers to remain I/O-bound long enough to exceed 240 s and 360 s whole-stack readiness windows in diagnostic runs. The production launcher was therefore changed to staged startup: **translation ready → speech ready → coordinator ready**.

In the successful retained run, TranslateGemma's cold read took about four minutes before readiness, while the speech stack became ready about 45 seconds after its staged launch. These observations are environment/startup evidence, not steady-state inference benchmarks. The acceptance timeout is configurable and defaults to 360 s per startup stage for Task 12.

## Reproduction

```bash
bash scripts/acceptance_pipeline.sh
```

For a stack that is already running and ready:

```bash
bash scripts/benchmark_pipeline.sh
```

The benchmark script defaults to one warmup, three sequential flagship measurements, standalone alternation, and two-request concurrency qualification.
