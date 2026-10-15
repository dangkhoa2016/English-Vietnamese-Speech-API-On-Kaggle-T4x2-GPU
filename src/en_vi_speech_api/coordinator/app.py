from fastapi import FastAPI

app = FastAPI(title="English-Vietnamese Speech API", docs_url=None, redoc_url=None)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "alive"}
