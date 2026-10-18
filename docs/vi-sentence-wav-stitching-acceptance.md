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