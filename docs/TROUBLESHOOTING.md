# Troubleshooting

> 🌐 Language / Ngôn ngữ: **English** | [Tiếng Việt](TROUBLESHOOTING.vi.md)

## Startup readiness times out

Check whether both workers were started simultaneously. The qualified path is staged: translation first, speech second, coordinator last. Parallel cold loading can become storage-I/O-bound even when GPU memory is sufficient.

## Physical GPU 1 appears as `cuda:0`

This is expected inside the speech worker because it runs with `CUDA_VISIBLE_DEVICES=1`. The process-local logical device is `cuda:0`, while the physical owner remains GPU 1.

## First translation is much slower

JAX/XLA compilation may dominate the first request. Use warm measurements for steady-state latency and keep cold-start behavior separately documented.

## Tunnel script refuses to run

Set `API_AUTH_REQUIRED=true` before enabling the public tunnel. This refusal is a security feature, not a startup bug.

## Mixed-language translation output

The retained acceptance includes an example where TranslateGemma did not fully translate an English sentence. Treat technical pipeline success and translation quality as separate dimensions.
