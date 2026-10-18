import asyncio
import io

import numpy as np
import pytest
import soundfile as sf

from en_vi_speech_api.speech_worker.sentence_stitching import (
    join_pcm_wav_segments,
    split_vietnamese_sentences,
)
from en_vi_speech_api.speech_worker.tts import TTSService

PARAGRAPH = (
    "Chúng tôi đang điều tra về độ trễ API cao trong môi trường sản xuất. "
    "Cơ sở dữ liệu hoạt động tốt, nhưng các yêu cầu thông qua dịch vụ thanh toán "
    "đang bị timeout. "
    "Lưu lượng truy cập đã được giảm xuống trong khi nhóm đang xác minh kế hoạch phục hồi."
)


def test_exact_approved_sentence_split():
    items = split_vietnamese_sentences(PARAGRAPH)
    assert len(items) == 3
    assert "API" in items[0]
    assert "timeout" in items[1]
    assert " ".join(items) == PARAGRAPH


@pytest.mark.parametrize("text", ["API", "Một câu.", "Tiến sĩ Dr. Smith trả lời.", ""])
def test_conservative_split(text):
    assert len(split_vietnamese_sentences(text)) <= 1


def wav(values, rate=48000):
    result = io.BytesIO()
    sf.write(result, np.asarray(values, dtype=np.float32), rate, format="WAV", subtype="PCM_16")
    return result.getvalue()


def test_pcm_stitch_pause_and_exact_samples():
    a = wav([0.125, -0.125], 1000)
    b = wav([0.25, -0.25], 1000)
    result, rate = join_pcm_wav_segments([a, b], pause_ms=300)
    assert rate == 1000
    assert result.size == 304
    assert np.array_equal(result[2:302], np.zeros(300, dtype=np.float32))
    assert result[0] == pytest.approx(0.125)
    assert result[-1] == pytest.approx(-0.25)


def test_pcm_rejects_bad_inputs():
    with pytest.raises(ValueError):
        join_pcm_wav_segments([])
    with pytest.raises(ValueError, match="sample rates"):
        join_pcm_wav_segments([wav([0.1], 1000), wav([0.1], 2000)])
    with pytest.raises(ValueError, match="Invalid or empty"):
        join_pcm_wav_segments([wav([])])


class Models:
    ready = True

    def __init__(self):
        self.gpu_semaphore = asyncio.Semaphore(1)


@pytest.mark.asyncio
async def test_live_service_stitching_contract_without_model():
    calls = []
    models = Models()

    def infer(text, language):
        assert models.gpu_semaphore.locked()
        calls.append((text, language))
        return np.array([0.1, -0.1] * 1000, dtype=np.float32), 48000

    service = TTSService(models=models, infer=infer, stitch_vi_sentences=True)
    response = await service.synthesize(PARAGRAPH, "vi")
    assert len(calls) == 3
    assert [x[0] for x in calls] == split_vietnamese_sentences(PARAGRAPH)
    with sf.SoundFile(io.BytesIO(response.wav_bytes)) as output:
        assert output.samplerate == 48000
        assert output.channels == 1
        assert output.subtype == "PCM_16"
        assert output.frames == 3 * 2000 + 2 * 14400
    assert response.duration_s == pytest.approx(0.725)


@pytest.mark.asyncio
async def test_disabled_and_english_paths_remain_unsplit():
    for flag, language in ((False, "vi"), (True, "en")):
        calls = []

        def infer(text, lang, calls=calls):
            calls.append((text, lang))
            return np.array([0.2, -0.2], dtype=np.float32), 48000

        service = TTSService(models=Models(), infer=infer, stitch_vi_sentences=flag)
        await service.synthesize(PARAGRAPH, language)
        assert calls == [(PARAGRAPH, language)]