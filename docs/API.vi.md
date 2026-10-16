# API public

> 🌐 Language / Ngôn ngữ: [English](API.md) | **Tiếng Việt**

Dịch vụ public bind tại `127.0.0.1:8090`. API nội bộ của model worker trên 8091/8092 chỉ là chi tiết triển khai, không phải public contract.

Mọi response từ coordinator đều có `X-Request-ID`. Khi `API_AUTH_REQUIRED=true`, tất cả route ngoại trừ `/health/live` yêu cầu `Authorization: Bearer <key>`.

## Health

### `GET /health/live`

Chỉ kiểm tra process còn sống; không chứng minh model worker đã sẵn sàng.

### `GET /health/ready`

Tổng hợp readiness của translation worker và speech worker. Trả HTTP 503 cho đến khi cả hai worker đều ready.

## `POST /v1/audio/transcriptions`

Multipart form:

- `file`: audio upload;
- `language`: tùy chọn, mặc định `en`; v1 chỉ nhận `en`.

Coordinator kiểm tra size/duration, chuẩn hóa WAV cho ASR và trả JSON gồm transcript tiếng Anh, model/timing từ speech worker, normalized duration và `request_id`.

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/transcriptions \
  -F 'file=@data/fixtures/english-short.wav' \
  -F 'language=en'
```

## `POST /v1/audio/speech`

Multipart form:

- `file`: file text UTF-8;
- `language`: bắt buộc, `en` hoặc `vi`.

Response là WAV. Các header hữu ích gồm `X-Request-ID`, `X-Model`, `X-Inference-Ms`, `X-Audio-Sample-Rate`, `X-Audio-Duration-S` và `X-Speech-Language`.

```bash
printf 'Xin chào.' > /tmp/speech.txt
curl -sS -X POST http://127.0.0.1:8090/v1/audio/speech \
  -F 'file=@/tmp/speech.txt;type=text/plain' \
  -F 'language=vi' -o /tmp/speech.wav
```

## `POST /v1/audio/translate-and-speak`

Multipart form:

- `file`: audio tiếng Anh.

Response là `application/zip` với contract chính xác:

- `transcript.en.txt`
- `translation.vi.txt`
- `speech.vi.wav`
- `metadata.json`

`metadata.json` chứa request ID, ngôn ngữ nguồn/đích, model identity, timing từng stage, normalized input duration và metadata của output audio.

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/translate-and-speak \
  -F 'file=@data/fixtures/english-short.wav' \
  -o /tmp/translate-and-speak.zip
```

## Authentication

Khi `API_AUTH_REQUIRED=true`, key sinh ra được lưu ở `runtime/api_key.txt` và request dùng:

```bash
curl -H "Authorization: Bearer $(cat runtime/api_key.txt)" ...
```

Không commit key này vào Git, không để lộ trong notebook output, screenshot hay release asset.

## Limit và queue

Giá trị mặc định nằm trong `.env.example`: audio 25 MiB, text 100 KiB, audio duration 1800 s, `PUBLIC_MAX_INFLIGHT=2` và `PUBLIC_MAX_PENDING=2`. Queue đầy trả HTTP 429; request hết thời gian chờ capacity trả HTTP 504.
