from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_MODEL_BASE = Path("/kaggle/input/models/keras/translategemma/keras/translategemma_4b_it")
DEFAULT_MODEL_PATH = DEFAULT_MODEL_BASE / "1"
MODEL_ID = "keras/translategemma_4b_it"
LANGUAGE_NAMES = {"en": "English", "vi": "Vietnamese"}
GENERATION_BUCKETS = (256, 512, 1024, 1536, 2048)


@dataclass(frozen=True, slots=True)
class TranslationResult:
    text: str
    inference_ms: float
    model: str = MODEL_ID


def _model_complete(path: Path) -> bool:
    return all(
        (path / relative).is_file()
        for relative in (
            "config.json",
            "preprocessor.json",
            "model.weights.h5",
            "assets/tokenizer/vocabulary.spm",
        )
    )


def discover_model_path(
    configured: Path | str | None = None,
    *,
    base_dir: Path | str = DEFAULT_MODEL_BASE,
) -> Path:
    if configured is not None:
        candidate = Path(configured)
        if _model_complete(candidate):
            return candidate

    base = Path(base_dir)
    if base.is_dir():
        versions = sorted(
            (path for path in base.iterdir() if path.is_dir()),
            key=lambda path: (int(path.name) if path.name.isdigit() else -1, path.name),
            reverse=True,
        )
        for candidate in versions:
            if _model_complete(candidate):
                return candidate
    raise FileNotFoundError(f"No complete TranslateGemma preset found under {base}")


def _resolve_keras_classes() -> tuple[Any, Any, Any]:
    import keras_hub

    try:
        models = keras_hub.models
        return models.Gemma3Backbone, models.Gemma3CausalLMPreprocessor, models.Gemma3CausalLM
    except AttributeError:
        from keras_hub.src.models.gemma3.gemma3_backbone import Gemma3Backbone
        from keras_hub.src.models.gemma3.gemma3_causal_lm import Gemma3CausalLM
        from keras_hub.src.models.gemma3.gemma3_causal_lm_preprocessor import (
            Gemma3CausalLMPreprocessor,
        )

        return Gemma3Backbone, Gemma3CausalLMPreprocessor, Gemma3CausalLM


def _choose_bucket(required_length: int) -> int:
    for bucket in GENERATION_BUCKETS:
        if bucket >= required_length:
            return bucket
    step = 512
    return ((required_length + step - 1) // step) * step


def split_long_translation_text(text: str, *, max_words: int = 48) -> list[str]:
    """Keep short requests intact; split longer prose at sentence boundaries."""
    normalized = text.strip()
    if len(normalized.split()) <= max_words:
        return [normalized]
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ỹ])", normalized)
    if len(sentences) < 2:
        return [normalized]
    chunks: list[str] = []
    current: list[str] = []
    for sentence in sentences:
        if current and len((" ".join(current) + " " + sentence).split()) > max_words:
            chunks.append(" ".join(current))
            current = []
        current.append(sentence)
    if current:
        chunks.append(" ".join(current))
    return chunks


def translation_appears_unfinished(text: str) -> bool:
    """Conservative fail-closed check for unmistakably interrupted output."""
    value = text.strip()
    return not value or bool(re.search(r"\b(?:và|hoặc|and|or|but)\s*$", value, re.IGNORECASE))


class TranslateGemmaTranslator:
    model_id = MODEL_ID

    def __init__(
        self,
        model_path: Path | str = DEFAULT_MODEL_PATH,
        *,
        dtype: str = "bfloat16",
        max_output_tokens: int = 128,
    ) -> None:
        self.model_path = Path(model_path)
        self.dtype = dtype
        self.max_output_tokens = max_output_tokens
        self.ready = False
        self.model: Any = None
        self.preprocessor: Any = None
        self.load_metadata: dict[str, Any] = {}

    def _validate_model_files(self) -> None:
        required = (
            self.model_path / "config.json",
            self.model_path / "preprocessor.json",
            self.model_path / "model.weights.h5",
            self.model_path / "assets/tokenizer/vocabulary.spm",
        )
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"TranslateGemma preset is incomplete: {missing}")

    def load(self) -> dict[str, Any]:
        self.model_path = discover_model_path(self.model_path)
        self._validate_model_files()
        started = time.perf_counter()

        import jax
        import keras
        import keras_hub

        devices = jax.devices()
        if len(devices) != 1 or devices[0].platform != "gpu":
            raise RuntimeError(f"Translation worker must see exactly one GPU, got: {devices}")

        Gemma3Backbone, Gemma3CausalLMPreprocessor, Gemma3CausalLM = _resolve_keras_classes()
        backbone_doc = json.loads((self.model_path / "config.json").read_text(encoding="utf-8"))
        backbone_cfg = dict(backbone_doc["config"])
        backbone_cfg["vision_encoder"] = None
        backbone = Gemma3Backbone.from_config(backbone_cfg)
        backbone.load_weights(str(self.model_path / "model.weights.h5"), skip_mismatch=True)

        preprocessor_doc = json.loads(
            (self.model_path / "preprocessor.json").read_text(encoding="utf-8")
        )
        preprocessor_cfg = dict(preprocessor_doc["config"])
        preprocessor_cfg["image_converter"] = None
        preprocessor = Gemma3CausalLMPreprocessor.from_config(preprocessor_cfg)
        preprocessor.tokenizer.set_proto(str(self.model_path / "assets/tokenizer/vocabulary.spm"))

        self.model = Gemma3CausalLM(preprocessor, backbone, dtype=self.dtype)
        self.preprocessor = self.model.preprocessor
        self.ready = True
        self.load_metadata = {
            "model": MODEL_ID,
            "load_seconds": round(time.perf_counter() - started, 3),
            "devices": [str(device) for device in devices],
            "dtype": self.dtype,
            "keras_version": getattr(keras, "__version__", "unknown"),
            "keras_hub_version": getattr(keras_hub, "__version__", "unknown"),
            "jax_version": getattr(jax, "__version__", "unknown"),
            "vision_enabled": False,
        }
        return self.load_metadata

    @staticmethod
    def _prompt(text: str, source_language: str, target_language: str) -> str:
        source = LANGUAGE_NAMES[source_language]
        target = LANGUAGE_NAMES[target_language]
        return (
            f"user: Translate the following text from {source} to {target}. "
            "Return only the translation, without explanation or commentary. "
            "Preserve meaning, tone, speaker, numbers, and negation.\n"
            f"{text.strip()}\nmodel: "
        )

    @staticmethod
    def _clean(text: str) -> str:
        result = text.strip()
        for marker in ("<end_of_turn>", "<eos>", "</s>"):
            result = result.replace(marker, "")
        return result.strip()

    def translate_result(
        self, text: str, source_language: str = "en", target_language: str = "vi"
    ) -> TranslationResult:
        if not self.ready or self.model is None or self.preprocessor is None:
            raise RuntimeError("TranslateGemma model is not ready")
        if source_language not in LANGUAGE_NAMES or target_language not in LANGUAGE_NAMES:
            raise ValueError("Unsupported language")

        chunks = split_long_translation_text(text)
        started = time.perf_counter()
        translations: list[str] = []
        for chunk in chunks:
            prompt = self._prompt(chunk, source_language, target_language)
            prompt_tokens = len(self.preprocessor.tokenizer(prompt))
            exact_max_length = prompt_tokens + self.max_output_tokens + 8
            output = self.model.generate(
                prompt,
                max_length=_choose_bucket(exact_max_length),
                stop_token_ids="auto",
                strip_prompt=True,
            )
            cleaned = self._clean(str(output))
            if translation_appears_unfinished(cleaned):
                raise RuntimeError("TranslateGemma produced an incomplete translation")
            translations.append(cleaned)
        return TranslationResult(
            text=" ".join(translations),
            inference_ms=(time.perf_counter() - started) * 1000,
        )

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        return self.translate_result(text, source_language, target_language).text
