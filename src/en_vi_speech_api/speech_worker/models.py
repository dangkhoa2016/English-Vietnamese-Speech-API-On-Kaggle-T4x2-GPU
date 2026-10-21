from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

VOXCPM_MODEL_BASE = Path("/kaggle/input/models/dangkhoa2016/openbmb-voxcpm2/pytorch/default")
WHISPER_MODEL_BASE = Path(
    "/kaggle/input/models/dangkhoa2016/openai-whisper-large-v3-turbo/transformers/default"
)


def discover_versioned_model(base: Path | str, *, required: tuple[str, ...]) -> Path:
    root = Path(base)
    if not root.is_dir():
        raise FileNotFoundError(f"Model base directory not found: {root}")
    versions = sorted(
        (path for path in root.iterdir() if path.is_dir()),
        key=lambda path: (int(path.name) if path.name.isdigit() else -1, path.name),
        reverse=True,
    )
    for candidate in versions:
        if all((candidate / relative).is_file() for relative in required):
            return candidate
    raise FileNotFoundError(f"No complete model version found under {root}")


def _import_torch() -> Any:
    import torch

    return torch


def assert_single_logical_cuda_device() -> Any:
    torch = _import_torch()
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError(
            "Speech worker must see exactly one logical CUDA device after CUDA visibility isolation."
        )
    return torch


def load_voxcpm_real(model_path: Path | str | None = None) -> Any:
    torch = assert_single_logical_cuda_device()
    del torch
    imported = time.perf_counter()
    from voxcpm import VoxCPM

    print(f"SPEECH_PROFILE voxcpm_import_seconds={time.perf_counter() - imported:.3f}", flush=True)

    path = (
        Path(model_path)
        if model_path is not None
        else discover_versioned_model(
            VOXCPM_MODEL_BASE,
            required=("config.json", "model.safetensors", "audiovae.pth"),
        )
    )
    loading = time.perf_counter()
    model = VoxCPM.from_pretrained(
        str(path),
        load_denoiser=False,
        local_files_only=True,
        optimize=False,
        device="cuda:0",
    )
    print(
        f"SPEECH_PROFILE voxcpm_from_pretrained_seconds={time.perf_counter() - loading:.3f}",
        flush=True,
    )
    return model


def load_whisper_real(model_path: Path | str | None = None) -> Any:
    torch = assert_single_logical_cuda_device()
    importing = time.perf_counter()
    from transformers import AutoModelForSpeechSeq2Seq

    print(
        f"SPEECH_PROFILE whisper_import_seconds={time.perf_counter() - importing:.3f}", flush=True
    )

    path = (
        Path(model_path)
        if model_path is not None
        else discover_versioned_model(
            WHISPER_MODEL_BASE,
            required=("config.json", "model.safetensors", "preprocessor_config.json"),
        )
    )
    loading = time.perf_counter()
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        str(path),
        dtype=torch.float16,
        local_files_only=True,
    )
    print(
        f"SPEECH_PROFILE whisper_from_pretrained_seconds={time.perf_counter() - loading:.3f}",
        flush=True,
    )
    moving = time.perf_counter()
    model = model.to("cuda:0")
    print(
        f"SPEECH_PROFILE whisper_cuda_transfer_seconds={time.perf_counter() - moving:.3f}",
        flush=True,
    )
    return model


class SpeechModels:
    def __init__(
        self,
        *,
        voxcpm_loader: Callable[[], Any],
        whisper_loader: Callable[[], Any],
        stage_hook: Callable[[str], None] | None = None,
    ) -> None:
        self._voxcpm_loader = voxcpm_loader
        self._whisper_loader = whisper_loader
        self._stage_hook = stage_hook
        self.voxcpm: Any = None
        self.whisper: Any = None
        self.gpu_semaphore = asyncio.Semaphore(1)
        self.load_metadata: dict[str, Any] = {}

    @property
    def ready(self) -> bool:
        return self.voxcpm is not None and self.whisper is not None

    def load(self) -> dict[str, Any]:
        started = time.perf_counter()
        voxcpm_started = time.perf_counter()
        if self._stage_hook is not None:
            self._stage_hook("SPEECH_LOAD_STAGE=voxcpm_start")
        self.voxcpm = self._voxcpm_loader()
        voxcpm_seconds = time.perf_counter() - voxcpm_started
        if self._stage_hook is not None:
            self._stage_hook(f"SPEECH_LOAD_STAGE=voxcpm_ready seconds={voxcpm_seconds:.3f}")

        whisper_started = time.perf_counter()
        if self._stage_hook is not None:
            self._stage_hook("SPEECH_LOAD_STAGE=whisper_start")
        self.whisper = self._whisper_loader()
        whisper_seconds = time.perf_counter() - whisper_started
        if self._stage_hook is not None:
            self._stage_hook(f"SPEECH_LOAD_STAGE=whisper_ready seconds={whisper_seconds:.3f}")

        torch_version: str | None = None
        cuda_runtime: str | None = None
        logical_gpu_count: int | None = None
        try:
            torch = _import_torch()
        except ImportError:
            torch = None
        if torch is not None:
            torch_version = str(torch.__version__)
            cuda_runtime = str(torch.version.cuda)
            logical_gpu_count = int(torch.cuda.device_count())

        total_load_seconds = time.perf_counter() - started
        self.load_metadata = {
            "ready": self.ready,
            "voxcpm_load_seconds": round(voxcpm_seconds, 3),
            "whisper_load_seconds": round(whisper_seconds, 3),
            "total_load_seconds": round(total_load_seconds, 3),
            "torch_version": torch_version,
            "cuda_runtime": cuda_runtime,
            "logical_gpu_count": logical_gpu_count,
            "visible_devices": os.getenv("CUDA_VISIBLE_DEVICES"),
        }
        if self._stage_hook is not None:
            self._stage_hook(f"SPEECH_LOAD_STAGE=ready total_seconds={total_load_seconds:.3f}")
        return dict(self.load_metadata)


def build_real_speech_models(*, stage_hook: Callable[[str], None] | None = None) -> SpeechModels:
    assert_single_logical_cuda_device()
    return SpeechModels(
        voxcpm_loader=load_voxcpm_real,
        whisper_loader=load_whisper_real,
        stage_hook=stage_hook,
    )


class StubSpeechModels:
    ready = True

    def __init__(self) -> None:
        self.gpu_semaphore = asyncio.Semaphore(1)
        self.load_metadata = {"ready": True, "mode": "stub"}
