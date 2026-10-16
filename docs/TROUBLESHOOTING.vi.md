# Xử lý sự cố

> 🌐 Language / Ngôn ngữ: [English](TROUBLESHOOTING.md) | **Tiếng Việt**

## Startup readiness bị timeout

Kiểm tra xem hai worker có bị start đồng thời hay không. Qualified path dùng staging: translation trước, speech sau, coordinator cuối. Parallel cold loading có thể bị storage-I/O-bound dù GPU memory vẫn đủ.

## Physical GPU 1 lại hiện là `cuda:0`

Đây là hành vi đúng bên trong speech worker vì process chạy với `CUDA_VISIBLE_DEVICES=1`. Logical device cục bộ của process là `cuda:0`, trong khi physical owner vẫn là GPU 1.

## Translation đầu tiên chậm hơn nhiều

JAX/XLA compilation có thể chiếm phần lớn thời gian của request đầu. Dùng warm measurements cho steady-state latency và ghi cold-start behavior riêng.

## Tunnel script từ chối chạy

Hãy đặt `API_AUTH_REQUIRED=true` trước khi bật public tunnel. Việc từ chối này là security feature, không phải startup bug.

## Translation còn mixed-language

Retained acceptance có một ví dụ TranslateGemma không dịch hoàn toàn câu tiếng Anh. Cần xem technical pipeline success và translation quality là hai chiều đánh giá riêng.
