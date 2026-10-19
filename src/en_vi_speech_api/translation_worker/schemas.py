from pydantic import BaseModel


class TranslationRequest(BaseModel):
    text: str
    source_language: str = "en"
    target_language: str = "vi"


class TranslationResponse(BaseModel):
    text: str
    source_language: str
    target_language: str
    model: str | None = None
    inference_ms: float | None = None
