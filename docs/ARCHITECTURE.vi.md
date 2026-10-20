# Kiến trúc

> 🌐 Language / Ngôn ngữ: [English](ARCHITECTURE.md) | **Tiếng Việt**

## Mục tiêu

Repository này chạy API giọng nói Anh/Việt trong một phiên Kaggle **T4 x2**. Thiết kế đã được kiểm chứng tách rõ quyền sở hữu model theo GPU và chỉ dùng coordinator làm biên public.

## Process và quyền sở hữu GPU

| Process | Địa chỉ bind | Accelerator | Model / trách nhiệm |
| --- | --- | --- | --- |
| Coordinator | `127.0.0.1:8090` | CPU | REST API public, validation, request ID, admission, đóng gói artifact |
| Translation worker | `127.0.0.1:8091` | **GPU 0** vật lý | **TranslateGemma 4B IT** qua Keras 3 / **KerasHub** với backend CUDA của **JAX** |
| Speech worker | `127.0.0.1:8092` | **GPU 1** vật lý | ASR **Whisper Large V3 Turbo** + TTS **VoxCPM2** trong cùng một process PyTorch thường trú |

`CUDA_VISIBLE_DEVICES` cô lập hai worker. Bên trong speech worker, GPU 1 vật lý được nhìn thấy có chủ đích dưới tên logic `cuda:0`.

## Luồng flagship

`POST /v1/audio/translate-and-speak` luôn thực hiện theo thứ tự:

1. kiểm tra upload;
2. chuẩn hóa audio cho ASR;
3. Whisper: audio tiếng Anh hoặc tiếng Việt → transcript cùng ngôn ngữ nguồn;
4. TranslateGemma: dịch Anh ↔ Việt;
5. VoxCPM2: tổng hợp WAV bằng ngôn ngữ đích;
6. coordinator đóng gói transcript, bản dịch, WAV và metadata thành một ZIP.

Inference tại từng worker được serialize. Coordinator có hàng đợi admission giới hạn; bằng chứng T4x2 đã lưu giữ xác nhận hai public request đồng thời mà không trộn artifact giữa request. Xem [BENCHMARKS.vi.md](BENCHMARKS.vi.md).

## Trình tự khởi động

Kaggle attached-model storage từng bị nghẽn cold-read nghiêm trọng khi hai model stack load đồng thời. Vì vậy `scripts/start.sh` dùng đúng trình tự đã được qualification:

`translation ready → speech ready → coordinator ready`

Coordinator chỉ khởi động sau khi cả hai model worker sẵn sàng. Đây là cơ chế reliability có chủ đích.

## Biên public và internal

Chỉ port **8090** có thể được expose. Port **8091** và **8092** là dịch vụ loopback nội bộ, không được tunnel hay expose trực tiếp. Cloudflare Quick Tunnel tùy chọn chỉ trỏ tới `127.0.0.1:8090` và fail-closed nếu chưa bật API authentication.

## Vòng đời

- `scripts/preflight.sh`: kiểm tra T4x2/runtime.
- `scripts/start.sh`: khởi động theo từng stage.
- `scripts/status.sh`: xem process/readiness.
- `scripts/stop.sh`: dừng toàn bộ stack.
- `scripts/acceptance_pipeline.sh`: acceptance bằng model thật trên T4x2.
- `scripts/benchmark_pipeline.sh`: benchmark/qualification đã lưu evidence.
