# Bằng chứng Acceptance và Benchmark trên T4x2

> 🌐 Language / Ngôn ngữ: [English](BENCHMARKS.md) | **Tiếng Việt**

## Phạm vi

Tài liệu này ghi lại bằng chứng đo thực tế đã được giữ lại cho pipeline giọng nói Anh→Việt trên runtime Kaggle **2× NVIDIA Tesla T4**. Đây là kết quả acceptance cho đúng runtime và fixture này, không phải cam kết hiệu năng chung cho mọi môi trường.

Phân bố model đã được qualification:

- GPU vật lý 0: TranslateGemma 4B IT (`keras/translategemma_4b_it`) qua Keras 3 / KerasHub với backend JAX/XLA CUDA;
- GPU vật lý 1: Whisper Large V3 Turbo (`openai/whisper-large-v3-turbo`) và VoxCPM2 (`openbmb/VoxCPM2`) cùng resident;
- CPU: FastAPI coordinator.

Fixture flagship dùng để đo là `data/fixtures/english-short.wav`, dài **4.64 giây**, được normalize thành PCM s16le, mono, 16 kHz trước ASR.

## Quy trình qualification

Task 12 được chạy bằng `scripts/acceptance_pipeline.sh`, gồm:

1. yêu cầu GPU baseline sạch;
2. cold-start TranslateGemma và chờ READY trước khi load speech stack để tránh tranh chấp I/O trên attached-model storage;
3. ghi PID và xác minh GPU vật lý thuộc về đúng worker;
4. chạy một flagship warmup;
5. chạy ba flagship request tuần tự để đo;
6. luân phiên transcription, translation, English TTS và Vietnamese TTS độc lập;
7. gửi đồng thời hai flagship request;
8. xác minh PID worker không thay đổi;
9. dừng service và xác minh GPU/port được giải phóng.

Bằng chứng request ở dạng machine-readable được `scripts/benchmark_pipeline.sh` ghi vào `runtime/benchmark-pipeline/results.json`.

## Bằng chứng residency

Tại thời điểm service READY:

| GPU | Vai trò | VRAM đã dùng |
| --- | --- | ---: |
| GPU 0 | TranslateGemma 4B IT | 13,865 MiB |
| GPU 1 | Whisper + VoxCPM2 | 6,871 MiB |

Sau workload benchmark:

| GPU | VRAM đã dùng |
| --- | ---: |
| GPU 0 | 13,897 MiB |
| GPU 1 | 7,839 MiB |

Translation worker luôn ở GPU vật lý 0, speech worker luôn ở GPU vật lý 1, còn CPU coordinator không sở hữu GPU. PID của các worker sống xuyên suốt benchmark. Không có OOM và không có worker restart. Sau khi shutdown, cả hai GPU trở về **0 MiB used** và các port 8090–8092 được giải phóng.

## Flagship warmup

Request đầu tiên bao gồm JAX/XLA compilation và các cold-path effect, vì vậy được báo cáo riêng, không trộn vào số steady-state.

| Metric | Warmup |
| --- | ---: |
| ASR | 1,926.2 ms |
| Translation | 62,033.4 ms |
| TTS | 9,976.0 ms |
| Tổng pipeline phía server | 74,210.8 ms |
| Tổng thời gian phía client | 74,432.9 ms |

Bản dịch warmup:

> Chào bạn. Đây là giọng nói tiếng Anh tổng hợp ngắn để kiểm tra dịch.

## Benchmark flagship tuần tự

Sau warmup, ba request warm được đo tuần tự.

| Stage | Trung bình | Nhỏ nhất | Lớn nhất |
| --- | ---: | ---: | ---: |
| ASR | 242.2 ms | 241.6 ms | 242.5 ms |
| Translation | 3,644.0 ms | 3,627.7 ms | 3,657.8 ms |
| TTS | 17,605.1 ms | 9,777.0 ms | 32,927.1 ms |
| Tổng pipeline phía server | **21,762.6 ms** | **13,959.0 ms** | **37,065.4 ms** |

Tổng thời gian phía client lần lượt là 37,274.1 ms, 14,428.6 ms và 14,114.2 ms. Cả ba request đều trả về ZIP đúng bốn file và cùng transcript tiếng Anh/bản dịch tiếng Việt mong đợi.

TTS là nguồn biến thiên latency lớn nhất trong retained run này: output TTS của phép đo đầu dài 14.88 giây, còn hai output sau dài 4.48 giây và 4.32 giây. Benchmark giữ nguyên mẫu hợp lệ chậm hơn này thay vì loại bỏ để làm đẹp số liệu.

## Luân phiên endpoint độc lập

Các worker resident tương tự tiếp tục được kiểm tra qua những đường xử lý độc lập.

| Khả năng | Kết quả đo |
| --- | ---: |
| English transcription | 641.6 ms tổng phía client; 244.9 ms model inference |
| EN→VI translation | 3,209.7 ms tổng phía client; 3,198.3 ms model inference |
| English TTS | 7,678.2 ms tổng phía client; WAV 322,604 byte |
| Vietnamese TTS | 4,769.2 ms tổng phía client; WAV 199,724 byte |

Mẫu translation độc lập trả về:

> Artificial intelligence có thể giúp mọi người giao tiếp bằng nhiều ngôn ngữ.

Đây là output tiếng Việt hợp lệ về mặt kỹ thuật nhưng cụm “Artificial intelligence” chưa được dịch. Vì vậy chất lượng dịch vẫn cần human review; technical PASS không đồng nghĩa với tuyên bố chất lượng dịch hoàn hảo.

## Qualification hai request đồng thời

Hai flagship request với **hai audio tiếng Anh khác nhau** được gửi đồng thời với `PUBLIC_MAX_INFLIGHT=2`. Request 1 dùng ASR fixture đã giữ lại; request 2 dùng English WAV được tạo ở bước standalone TTS.

| Request | Tổng phía client | Tổng phía server | Request ID | Kết quả |
| --- | ---: | ---: | --- | --- |
| concurrent-1 | 19,329.0 ms | 18,797.3 ms | `46aaf120-3320-470f-b4d7-6b98ac89c787` | PASS |
| concurrent-2 | 9,042.5 ms | 8,888.5 ms | `73224e72-634b-4f65-acf2-4a51762a4561` | PASS |

Kết quả qualification: **PASS**.

Bằng chứng:

- hai request ID khác nhau;
- hai audio input khác nhau tạo ra hai transcript/translation khác nhau và được ghép đúng vào artifact tương ứng;
- không OOM;
- không deadlock;
- không worker restart;
- không trộn artifact giữa hai request;
- PID worker sống xuyên suốt concurrent test;
- cleanup đưa cả hai GPU và cả ba port về baseline.

Dựa trên bằng chứng đã giữ lại này, mặc định v1 có thể tiếp tục dùng `PUBLIC_MAX_INFLIGHT=2` cùng `PUBLIC_MAX_PENDING=2`. Inference model trên từng GPU vẫn được serialize theo concurrency policy của worker tương ứng.

## Hành vi startup

Attached-model storage của Kaggle có độ biến thiên cold-read đáng kể. Khi TranslateGemma và speech stack cùng load đồng thời, cả hai worker bị I/O-bound đủ lâu để vượt các cửa sổ whole-stack readiness 240 giây và 360 giây trong các diagnostic run. Vì vậy production launcher đã được đổi sang staged startup: **translation ready → speech ready → coordinator ready**.

Trong successful retained run, cold read của TranslateGemma mất khoảng bốn phút trước khi READY; speech stack READY sau khoảng 45 giây kể từ lúc được launch theo pha. Đây là bằng chứng về môi trường/startup, không phải benchmark steady-state inference. Task 12 dùng timeout có thể cấu hình, mặc định 360 giây cho mỗi startup stage.

## Tái lập

```bash
bash scripts/acceptance_pipeline.sh
```

Khi stack đã chạy và READY:

```bash
bash scripts/benchmark_pipeline.sh
```

Mặc định benchmark gồm một warmup, ba phép đo flagship tuần tự, alternation các capability độc lập và qualification hai request đồng thời.
