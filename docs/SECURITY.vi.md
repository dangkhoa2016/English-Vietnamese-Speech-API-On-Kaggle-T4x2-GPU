# Security và mô hình expose

> 🌐 Language / Ngôn ngữ: [English](SECURITY.md) | **Tiếng Việt**

## Biên network

Các địa chỉ bind dự kiến:

- coordinator: `127.0.0.1:8090`;
- translation worker: `127.0.0.1:8091`;
- speech worker: `127.0.0.1:8092`.

Chỉ coordinator được phép expose. Không publish 8091 hoặc 8092 vì các internal route này không có lớp authentication/admission của public API.

## Authentication

`API_AUTH_REQUIRED=false` tiện cho notebook/local test riêng tư nhưng không được xem là chế độ an toàn khi mở Internet. Với public tunnel, phải đặt `API_AUTH_REQUIRED=true` trước khi start. Coordinator tạo key entropy cao tại `runtime/api_key.txt`, cố gắng đặt mode `0600` và so sánh `Bearer` credential theo constant-time comparison.

API key là runtime state. `runtime/` và `.env` đã nằm trong Git ignore. Không chép credential vào tài liệu, committed notebook, CI log, screenshot hay release artifact.

## Quy tắc tunnel fail-closed

`scripts/run_tunnel.sh` yêu cầu đồng thời:

- `ENABLE_CLOUDFLARE_TUNNEL=true`;
- `API_AUTH_REQUIRED=true`.

Script từ chối tạo Cloudflare Quick Tunnel public nếu authentication đang tắt. Tunnel chỉ trỏ tới `127.0.0.1:8090`.

## Kiểm soát tài nguyên

Coordinator giới hạn upload size/duration và dùng admission control có giới hạn. Giá trị đã qualification là `PUBLIC_MAX_INFLIGHT=2` và `PUBLIC_MAX_PENDING=2`; GPU inference bên trong mỗi worker vẫn serialize. Các control này giúp tránh overload vô tình nhưng không thay thế production gateway, rate limiter, identity system, abuse monitoring hay nền tảng audit bền vững.

## Trust và xử lý dữ liệu

Upload được xử lý trong thư mục tạm riêng cho từng request. Dự án là stack demo/qualification trên Kaggle, không nên quảng bá như dịch vụ multi-tenant production đã harden. Người vận hành chịu trách nhiệm về quyền xử lý audio/voice, consent, retention, tuân thủ license model và yêu cầu privacy của deployment.

## Output của model

ASR, translation và TTS đều là output xác suất. Không dùng chúng như nguồn quyết định có thẩm quyền cho pháp lý, y tế, tài chính, safety-critical hoặc identity. Benchmark đã ghi lại một ví dụ dịch còn mixed-language; technical acceptance không đồng nghĩa đảm bảo chất lượng ngôn ngữ.
