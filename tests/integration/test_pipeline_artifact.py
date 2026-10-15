import io
import json
import zipfile


def test_pipeline_zip_has_exact_files_utf8_metadata_and_no_private_paths() -> None:
    from en_vi_speech_api.coordinator.artifacts import build_pipeline_zip

    metadata = {
        "request_id": "req-1",
        "source_language": "en",
        "target_language": "vi",
        "normalized_audio_duration_s": 4.64,
        "models": {"asr": "whisper", "translation": "gemma", "tts": "voxcpm"},
        "timings_ms": {"asr": 10.0, "translation": 20.0, "tts": 30.0, "total": 61.0},
    }
    artifact = build_pipeline_zip(
        transcript="Hello world\n",
        translation="Xin chào thế giới\n",
        speech_wav=b"RIFFfake-wav",
        metadata=metadata,
    )

    with zipfile.ZipFile(io.BytesIO(artifact)) as archive:
        assert set(archive.namelist()) == {
            "transcript.en.txt",
            "translation.vi.txt",
            "speech.vi.wav",
            "metadata.json",
        }
        assert archive.read("transcript.en.txt").decode("utf-8") == "Hello world\n"
        assert archive.read("translation.vi.txt").decode("utf-8") == "Xin chào thế giới\n"
        assert archive.read("speech.vi.wav") == b"RIFFfake-wav"
        decoded = json.loads(archive.read("metadata.json"))
        assert decoded == metadata
        serialized = json.dumps(decoded, ensure_ascii=False)
        assert "/kaggle/" not in serialized
        assert "/tmp/" not in serialized
