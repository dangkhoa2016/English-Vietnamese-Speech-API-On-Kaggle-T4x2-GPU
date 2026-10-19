import asyncio
from pathlib import Path


def test_pipeline_stage_order_is_normalize_transcribe_translate_synthesize_package(
    tmp_path: Path,
) -> None:
    from en_vi_speech_api.coordinator.routes.translate_and_speak import run_pipeline
    from en_vi_speech_api.coordinator.worker_client import WorkerAudio

    order: list[str] = []
    source = tmp_path / "source.wav"
    source.write_bytes(b"source")

    class Normalized:
        path = tmp_path / "normalized.wav"
        duration_s = 1.25

    def normalize(_input: Path, *, output_dir: Path):
        order.append("normalize")
        Normalized.path.write_bytes(b"normalized")
        return Normalized()

    class Speech:
        async def transcribe(self, wav_path: Path, *, language: str):
            order.append("transcribe")
            assert wav_path == Normalized.path
            assert language == "en"
            return {
                "text": "Hello world",
                "language": "en",
                "chunk_count": 1,
                "inference_ms": 10.0,
                "model": "whisper-test",
            }

        async def speak(self, text: str, *, language: str):
            order.append("synthesize")
            assert text == "Xin chào thế giới"
            assert language == "vi"
            return WorkerAudio(
                content=b"RIFFfake",
                media_type="audio/wav",
                model="voxcpm-test",
                inference_ms=30.0,
                sample_rate_hz=48000,
                duration_s=2.0,
                language="vi",
            )

    class Translation:
        async def translate(self, text: str, *, source_language: str, target_language: str):
            order.append("translate")
            assert text == "Hello world"
            return {
                "text": "Xin chào thế giới",
                "source_language": source_language,
                "target_language": target_language,
                "model": "translation-test",
                "inference_ms": 20.0,
            }

    def package(*, transcript: str, translation: str, speech_wav: bytes, metadata: dict):
        order.append("package")
        assert transcript == "Hello world"
        assert translation == "Xin chào thế giới"
        assert speech_wav == b"RIFFfake"
        assert metadata["request_id"] == "req-123"
        return b"ZIPfake"

    artifact = asyncio.run(
        run_pipeline(
            source,
            request_dir=tmp_path,
            request_id="req-123",
            speech_client=Speech(),
            translation_client=Translation(),
            normalizer=normalize,
            packager=package,
        )
    )

    assert artifact == b"ZIPfake"
    assert order == ["normalize", "transcribe", "translate", "synthesize", "package"]


def test_pipeline_stops_before_tts_when_translation_fails(tmp_path: Path) -> None:
    from en_vi_speech_api.coordinator.routes.translate_and_speak import run_pipeline
    from en_vi_speech_api.errors import ApiError

    source = tmp_path / "source.wav"
    source.write_bytes(b"source")
    calls: list[str] = []

    class Normalized:
        path = source
        duration_s = 1.0

    def normalize(_input: Path, *, output_dir: Path):
        calls.append("normalize")
        return Normalized()

    class Speech:
        async def transcribe(self, wav_path: Path, *, language: str):
            calls.append("transcribe")
            return {"text": "Hello", "model": "whisper", "inference_ms": 1.0, "chunk_count": 1}

        async def speak(self, text: str, *, language: str):
            calls.append("synthesize")
            raise AssertionError("TTS must not be called")

    class Translation:
        async def translate(self, text: str, *, source_language: str, target_language: str):
            calls.append("translate")
            raise ApiError("inference_failed", "translation failed", 502)

    try:
        asyncio.run(
            run_pipeline(
                source,
                request_dir=tmp_path,
                request_id="req-fail",
                speech_client=Speech(),
                translation_client=Translation(),
                normalizer=normalize,
            )
        )
    except ApiError as exc:
        assert exc.code == "inference_failed"
    else:
        raise AssertionError("expected ApiError")

    assert calls == ["normalize", "transcribe", "translate"]


def test_public_translate_and_speak_returns_zip(tmp_path: Path) -> None:
    import io
    import wave
    import zipfile

    from fastapi.testclient import TestClient

    from en_vi_speech_api.coordinator.worker_client import WorkerAudio

    class Speech:
        async def transcribe(self, wav_path: Path, *, language: str):
            return {
                "text": "Hello world",
                "language": "en",
                "chunk_count": 1,
                "inference_ms": 10.0,
                "model": "whisper-test",
            }

        async def speak(self, text: str, *, language: str):
            return WorkerAudio(
                content=b"RIFFfake",
                media_type="audio/wav",
                model="voxcpm-test",
                inference_ms=30.0,
                sample_rate_hz=48000,
                duration_s=2.0,
                language="vi",
            )

    class Translation:
        async def translate(self, text: str, *, source_language: str, target_language: str):
            return {
                "text": "Xin chào thế giới",
                "source_language": "en",
                "target_language": "vi",
                "model": "translation-test",
                "inference_ms": 20.0,
            }

    audio = io.BytesIO()
    with wave.open(audio, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 1600)

    from en_vi_speech_api.coordinator.app import create_app

    client = TestClient(
        create_app(
            speech_client=Speech(),
            translation_client=Translation(),
            request_temp_base=tmp_path,
        )
    )
    response = client.post(
        "/v1/audio/translate-and-speak",
        files={"file": ("english.wav", audio.getvalue(), "audio/wav")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["x-request-id"]
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert set(archive.namelist()) == {
            "transcript.en.txt",
            "translation.vi.txt",
            "speech.vi.wav",
            "metadata.json",
        }
    assert list(tmp_path.iterdir()) == []


def test_reverse_vietnamese_to_english_pipeline_contract(tmp_path: Path) -> None:
    import io
    import wave
    import zipfile

    from fastapi.testclient import TestClient

    from en_vi_speech_api.coordinator.app import create_app
    from en_vi_speech_api.coordinator.worker_client import WorkerAudio

    class Speech:
        async def transcribe(self, wav_path, *, language):
            assert language == "vi"
            return {"text": "Xin chào mọi người.", "model": "whisper", "inference_ms": 1.0}

        async def speak(self, text, *, language):
            assert language == "en"
            assert text == "Hello everyone."
            return WorkerAudio(b"RIFFfake", "audio/wav", "voxcpm", 2.0, 48000, 1.0, "en")

    class Translation:
        async def translate(self, text, *, source_language, target_language):
            assert (source_language, target_language) == ("vi", "en")
            return {"text": "Hello everyone.", "model": "translategemma", "inference_ms": 3.0}

    audio = io.BytesIO()
    with wave.open(audio, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 1600)

    client = TestClient(
        create_app(
            speech_client=Speech(), translation_client=Translation(), request_temp_base=tmp_path
        )
    )
    resp = client.post(
        "/v1/audio/translate-and-speak",
        files={"file": ("vietnamese.wav", audio.getvalue(), "audio/wav")},
        data={"source_language": "vi", "target_language": "en"},
    )
    assert resp.status_code == 200, resp.text
    with zipfile.ZipFile(io.BytesIO(resp.content)) as archive:
        assert set(archive.namelist()) == {
            "transcript.vi.txt",
            "translation.en.txt",
            "speech.en.wav",
            "metadata.json",
        }
