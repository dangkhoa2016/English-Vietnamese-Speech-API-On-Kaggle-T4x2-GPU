# Vietnamese sentence-level VoxCPM2 TTS — controlled candidate

## English

This candidate follows the 18 October 2026 private Kaggle diagnostic `dangkhoa2016/envi-api-sentence-level-repeat-t4x2`. Human listening approved 3/3 joined outputs; `joined_run_02.wav` was preferred. This is a small-sample listening result, **not** a production reliability guarantee.

- Default: **disabled** to preserve the existing public API behavior.
- To evaluate: set `VOXCPM_VI_SENTENCE_STITCHING=true` in the speech-worker process environment, then start the real stack.
- Only Vietnamese text containing multiple conservatively detected sentences is split. The original text is retained, including `API`.
- Each segment is independently synthesized, waveform-normalized, and PCM-16 encoded. Segments are decoded and joined with exactly **300 ms** of silence at the returned sample rate.
- No new public request parameters; the response remains a single WAV.
- Conservative boundaries, maximum 12 segments, no known-abbreviation boundaries. Ambiguous inputs remain unsplit.
- The new diagnostic needs **real T4×2 execution**, repeat human listening, Business Update regression, and checking seams/loudness before enabling this by default or updating `v1.0.0`.
- Reference WAV `joined_run_02.wav`: 48 kHz, mono, PCM-16, 14.52 s, SHA-256 `1044cb2bc47c677576af98a5b6a560525baad376acaece771d812920a4b4e666`. Its exact waveform cannot be assumed to reproduce under stochastic inference.

## Tiếng Việt

Ứng viên này được phát triển dựa trên notebook Kaggle riêng tư ngày 18/10/2026: `dangkhoa2016/envi-api-sentence-level-repeat-t4x2`. Người dùng đã duyệt cả ba bản ghép và chọn `joined_run_02.wav` là bản tốt nhất. Đây là kết quả đánh giá nghe trên mẫu nhỏ, **không phải** cam kết độ ổn định production.

- Mặc định **tắt**, giữ nguyên hành vi API công khai hiện tại.
- Để thử nghiệm: đặt `VOXCPM_VI_SENTENCE_STITCHING=true` trong môi trường speech worker trước khi khởi chạy dịch vụ.
- Chỉ tách văn bản tiếng Việt khi phát hiện nhiều ranh giới câu đủ rõ ràng. Giữ nguyên từ `API` và nội dung dịch.
- Mỗi câu được tổng hợp, chuẩn hóa và mã hóa PCM-16 riêng. Sau đó nối với khoảng lặng **300 ms**.
- Không thay đổi hợp đồng request/response công khai.
- Giới hạn 12 đoạn và tránh tách tại một số từ viết tắt. Văn bản mơ hồ được giữ nguyên một đoạn.
- Cần chạy nghiệm thu thật trên T4×2, nghe lặp lại, kiểm tra kịch bản Business Update, các mối nối và âm lượng trước khi bật mặc định hoặc cập nhật `v1.0.0`.
- WAV tham chiếu `joined_run_02.wav`: 48 kHz, mono, PCM-16, 14,52 giây, SHA-256 `1044cb2bc47c677576af98a5b6a560525baad376acaece771d812920a4b4e666`. Không giả định rằng suy luận ngẫu nhiên có thể tái tạo chính xác waveform này.

## GPU acceptance evidence — 2026-10-18

### English

Private Kaggle notebook: `dangkhoa2016/envi-stitch-gpu-acceptance-v3-t4x2`, successful version 3. Runtime source SHA: `b794edefb238a687d05e0f5e504f2364bb454af5`. Notebook confirmed `CPU_TEST_GATE=PASS`, `STITCH_SOURCE_AND_WORKER_CONFIG=PASS`, and `GPU_STITCH_ACCEPTANCE_GENERATION_V3=PASS`. The six files were downloaded from Kaggle output and checked as valid mono 48 kHz PCM-16 WAVs.

Human listening assessment approved **all six**. Preferred selections:

- `technical_incident_joined_run_02.wav`, 14.52 s, SHA-256 `e34f29e48ddcb3e59e7cbcaeee8ff3ce9a759696869758da9bac55260c249626`
- `business_update_joined_run_03.wav`, 12.46 s, SHA-256 `ecf0db55c9a0f76abc93ae831b9b69b14d70fb4294328464141e94246d5f22d3`

Result: **human listening PASS 6/6 in this targeted round**. This is not proof of universal deterministic pronunciation. Keep the feature behind its flag for now; preserve `main` and release `v1.0.0` pending the final integration/release decision.

### Tiếng Việt

Notebook Kaggle riêng tư: `dangkhoa2016/envi-stitch-gpu-acceptance-v3-t4x2`, phiên bản 3 chạy thành công. Commit chạy thực tế: `b794edefb238a687d05e0f5e504f2364bb454af5`. Các bước CPU gate, kiểm tra cấu hình speech worker và tổng hợp GPU đều PASS. Đã tải sáu WAV gốc từ Kaggle Output và xác minh định dạng mono PCM-16, 48 kHz.

Người dùng **duyệt cả sáu WAV**; hai lựa chọn tốt nhất là `technical_incident_joined_run_02.wav` và `business_update_joined_run_03.wav`. Kết quả nghiệm thu nghe ở vòng này là **6/6 PASS**, không đồng nghĩa với việc giọng đọc luôn ổn định trong mọi lần tạo. Tiếp tục giữ feature flag và chưa thay đổi `main` hoặc tag `v1.0.0`.
