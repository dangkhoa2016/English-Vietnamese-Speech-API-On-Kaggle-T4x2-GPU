# Security and Exposure Model

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](SECURITY.vi.md)

## Network boundary

The intended bindings are:

- coordinator: `127.0.0.1:8090`;
- translation worker: `127.0.0.1:8091`;
- speech worker: `127.0.0.1:8092`.

Only the coordinator may be exposed. Never publish 8091 or 8092: those internal routes do not implement the public authentication/admission boundary.

## Authentication

`API_AUTH_REQUIRED=false` is convenient for local/private notebook testing but must not be treated as an Internet-safe deployment mode. For any public tunnel, set `API_AUTH_REQUIRED=true` before startup. The coordinator creates a high-entropy key in `runtime/api_key.txt`, attempts mode `0600`, and compares incoming `Bearer` credentials using a constant-time comparison.

The API key is runtime state. `runtime/` and `.env` are Git-ignored. Do not copy credentials into documentation, committed notebooks, CI logs, screenshots, or release artifacts.

## Tunnel fail-closed rule

`scripts/run_tunnel.sh` requires both:

- `ENABLE_CLOUDFLARE_TUNNEL=true`;
- `API_AUTH_REQUIRED=true`.

It refuses to create a public Cloudflare Quick Tunnel when authentication is disabled. The tunnel target is only `127.0.0.1:8090`.

## Resource controls

The coordinator limits upload size/duration and uses bounded admission controls. The qualified defaults are `PUBLIC_MAX_INFLIGHT=2` and `PUBLIC_MAX_PENDING=2`; worker-local GPU inference remains serialized. These controls reduce accidental overload but are not a substitute for a full production gateway, rate limiter, identity system, abuse monitoring, or durable audit platform.

## Trust and data handling

Uploaded content is processed in per-request temporary directories. The project is a Kaggle demonstration/qualification stack; it should not be presented as a hardened multi-tenant production service. Operators are responsible for lawful handling of voice/audio data, consent, retention policy, model-license compliance, and deployment-specific privacy requirements.

## Model outputs

ASR, translation, and TTS are probabilistic model outputs. Do not use them as an authoritative source for legal, medical, financial, safety-critical, or identity decisions. The benchmark documents a real mixed-language translation example; technical acceptance is not a guarantee of linguistic correctness.
