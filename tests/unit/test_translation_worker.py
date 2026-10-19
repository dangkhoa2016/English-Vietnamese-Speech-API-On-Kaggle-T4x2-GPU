from fastapi.testclient import TestClient


class FakeTranslator:
    def __init__(self, *, ready: bool = True, fail: bool = False) -> None:
        self.ready = ready
        self.fail = fail

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        if self.fail:
            raise RuntimeError("synthetic inference failure")
        assert source_language == "en"
        assert target_language == "vi"
        return "Xin chào thế giới."


def test_translate_en_to_vi_with_fake_translator() -> None:
    from en_vi_speech_api.translation_worker.app import create_app

    client = TestClient(create_app(FakeTranslator()))
    response = client.post(
        "/internal/translate",
        json={"text": "Hello world.", "source_language": "en", "target_language": "vi"},
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Xin chào thế giới."
    assert response.json()["source_language"] == "en"
    assert response.json()["target_language"] == "vi"


def test_translate_rejects_empty_input() -> None:
    from en_vi_speech_api.translation_worker.app import create_app

    client = TestClient(create_app(FakeTranslator()))
    response = client.post(
        "/internal/translate",
        json={"text": "   \n", "source_language": "en", "target_language": "vi"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "empty_text"


def test_translate_rejects_excessive_input() -> None:
    from en_vi_speech_api.translation_worker.app import create_app

    client = TestClient(create_app(FakeTranslator()))
    response = client.post(
        "/internal/translate",
        json={"text": "x" * (100 * 1024 + 1), "source_language": "en", "target_language": "vi"},
    )
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "text_too_large"


def test_translate_worker_not_ready_fails_closed() -> None:
    from en_vi_speech_api.translation_worker.app import create_app

    client = TestClient(create_app(FakeTranslator(ready=False)))
    ready = client.get("/internal/ready")
    response = client.post(
        "/internal/translate",
        json={"text": "Hello", "source_language": "en", "target_language": "vi"},
    )
    assert ready.status_code == 503
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "worker_unavailable"


def test_translate_inference_exception_is_structured() -> None:
    from en_vi_speech_api.translation_worker.app import create_app

    client = TestClient(create_app(FakeTranslator(fail=True)))
    response = client.post(
        "/internal/translate",
        json={"text": "Hello", "source_language": "en", "target_language": "vi"},
    )
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "inference_failed"


def test_translate_model_discovers_latest_complete_kaggle_version(tmp_path) -> None:
    from en_vi_speech_api.translation_worker.model import discover_model_path

    base = tmp_path / "translategemma_4b_it"
    incomplete = base / "3"
    complete = base / "2"
    incomplete.mkdir(parents=True)
    complete.mkdir(parents=True)
    (incomplete / "config.json").write_text("{}", encoding="utf-8")
    for relative in (
        "config.json",
        "preprocessor.json",
        "model.weights.h5",
        "assets/tokenizer/vocabulary.spm",
    ):
        path = complete / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")

    assert discover_model_path(base_dir=base) == complete


def test_translate_ready_exposes_safe_backend_metadata() -> None:
    from en_vi_speech_api.translation_worker.app import create_app

    translator = FakeTranslator()
    translator.model_id = "test/translator"
    translator.load_metadata = {"devices": ["CudaDevice(id=0)"], "load_seconds": 1.25}
    client = TestClient(create_app(translator))

    response = client.get("/internal/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "test/translator"
    assert payload["metadata"]["devices"] == ["CudaDevice(id=0)"]
    assert "model_path" not in str(payload)


def test_long_translation_splits_by_sentence_and_preserves_order() -> None:
    from en_vi_speech_api.translation_worker.model import split_long_translation_text

    text = " ".join(
        f"Sentence {i} describes the status of a payment and service system." for i in range(10)
    )
    chunks = split_long_translation_text(text)
    assert len(chunks) >= 2
    assert " ".join(chunks) == text
    assert all(chunk.endswith(".") for chunk in chunks)


def test_short_translation_remains_single_request() -> None:
    from en_vi_speech_api.translation_worker.model import split_long_translation_text

    assert split_long_translation_text("Hello world. The system is healthy.") == [
        "Hello world. The system is healthy."
    ]


def test_incomplete_translation_fails_closed() -> None:
    from en_vi_speech_api.translation_worker.model import translation_appears_unfinished

    assert translation_appears_unfinished("Chúng tôi sẽ triển khai vào ngày mai và")
    assert not translation_appears_unfinished("Chúng tôi sẽ triển khai vào ngày mai.")


def test_long_translation_uses_separate_generate_calls() -> None:
    from en_vi_speech_api.translation_worker.model import TranslateGemmaTranslator

    class FakeTokenizer:
        def __call__(self, prompt):
            return [1] * len(prompt.split())

    class FakePreprocessor:
        tokenizer = FakeTokenizer()

    class FakeModel:
        def __init__(self):
            self.prompts = []

        def generate(self, prompt, **kwargs):
            self.prompts.append(prompt)
            return "Bản dịch hoàn chỉnh."

    translator = TranslateGemmaTranslator()
    translator.model = FakeModel()
    translator.preprocessor = FakePreprocessor()
    translator.ready = True
    text = " ".join(f"Sentence {i} describes a normal service operation." for i in range(12))
    result = translator.translate_result(text)
    assert len(translator.model.prompts) >= 2
    assert result.text.count("Bản dịch hoàn chỉnh.") == len(translator.model.prompts)


def test_translation_prompt_preserves_speaker_and_forbids_chatty_preface() -> None:
    from en_vi_speech_api.translation_worker.model import TranslateGemmaTranslator

    text = "Tôi đã đặt phòng cho hai người vào thứ sáu tuần tới. Xin xác nhận giờ nhận phòng."
    prompt = TranslateGemmaTranslator._prompt(text, "vi", "en")
    assert text in prompt
    assert "Vietnamese to English" in prompt
    assert "Return only the translation" in prompt
    assert "Preserve meaning, tone, speaker" in prompt
    assert "without explanation or commentary" in prompt


def test_translation_prompt_is_scenario_neutral_and_single_pass() -> None:
    from en_vi_speech_api.translation_worker.model import TranslateGemmaTranslator

    for source in (
        "The package was delivered, but I have not received it.",
        "I already booked a hotel room.",
        "The application crashed after an update.",
    ):
        prompt = TranslateGemmaTranslator._prompt(source, "en", "vi")
        assert source in prompt
        assert "đã giao" not in prompt
        assert "kiện hàng" not in prompt
        assert "đã đặt phòng" not in prompt
    assert not hasattr(TranslateGemmaTranslator, "_fidelity_guidance")
