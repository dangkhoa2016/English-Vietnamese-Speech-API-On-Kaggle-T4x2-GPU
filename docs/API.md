# Public API

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](API.vi.md)

The public service binds to `127.0.0.1:8090`. Internal model-worker APIs on 8091/8092 are implementation details and are not public contracts.

Every coordinator response carries `X-Request-ID`. When `API_AUTH_REQUIRED=true`, all routes except `/health/live` require `Authorization: Bearer <key>`.

## Health

### `GET /health/live`

Process liveness only. It does not prove that model workers are ready.

### `GET /health/ready`

Aggregates translation and speech worker readiness. Returns HTTP 503 until both workers report ready.

## `POST /v1/audio/transcriptions`

Multipart form:

- `file`: audio upload;
- `language`: optional, defaults to `en`; v1 accepts `en` only.

The coordinator validates size/duration, normalizes to ASR WAV, and returns JSON containing the English transcript, model/timing fields from the speech worker, normalized duration, and `request_id`.

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/transcriptions \
  -F 'file=@data/fixtures/english-short.wav' \
  -F 'language=en'
```

## `POST /v1/audio/speech`

Multipart form:

- `file`: UTF-8 text file;
- `language`: required, `en` or `vi`.

Returns WAV bytes. Useful response headers include `X-Request-ID`, `X-Model`, `X-Inference-Ms`, `X-Audio-Sample-Rate`, `X-Audio-Duration-S`, and `X-Speech-Language`.

```bash
printf 'Xin chào.' > /tmp/speech.txt
curl -sS -X POST http://127.0.0.1:8090/v1/audio/speech \
  -F 'file=@/tmp/speech.txt;type=text/plain' \
  -F 'language=vi' -o /tmp/speech.wav
```

## `POST /v1/audio/translate-and-speak`

Multipart form:

- `file`: English audio upload.

Returns `application/zip`. The archive contract is exactly:

- `transcript.en.txt`
- `translation.vi.txt`
- `speech.vi.wav`
- `metadata.json`

`metadata.json` includes the request ID, source/target languages, model identities, stage timings, normalized input duration, and output-audio metadata.

```bash
curl -sS -X POST http://127.0.0.1:8090/v1/audio/translate-and-speak \
  -F 'file=@data/fixtures/english-short.wav' \
  -o /tmp/translate-and-speak.zip
```

## Authentication

With `API_AUTH_REQUIRED=true`, the generated key is stored at `runtime/api_key.txt` and requests use:

```bash
curl -H "Authorization: Bearer $(cat runtime/api_key.txt)" ...
```

Never put that key in Git, notebook output, screenshots, or release assets.

## Limits and queueing

Defaults are documented in `.env.example`: 25 MiB audio, 100 KiB text, 1800 s audio duration, `PUBLIC_MAX_INFLIGHT=2`, and `PUBLIC_MAX_PENDING=2`. A full queue returns HTTP 429; a request that times out waiting for capacity returns HTTP 504.
