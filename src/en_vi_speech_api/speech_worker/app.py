from fastapi import FastAPI

app = FastAPI(title="Speech Worker", docs_url=None, redoc_url=None)


@app.get("/internal/health")
def health() -> dict[str, str]:
    return {"status": "ok", "worker": "speech"}


@app.get("/internal/ready")
def ready() -> dict[str, object]:
    return {"ready": True, "mode": "stub", "worker": "speech"}
