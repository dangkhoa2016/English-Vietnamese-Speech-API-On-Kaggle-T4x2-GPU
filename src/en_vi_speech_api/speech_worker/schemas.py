from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    text: str
    language: str
    chunk_count: int
    inference_ms: float
    model: str


class SpeechRequest(BaseModel):
    text: str
    language: str
