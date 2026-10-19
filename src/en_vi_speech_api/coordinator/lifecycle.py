from __future__ import annotations

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path

KAGGLE_WORKING_DIR = Path("/kaggle/working")


@dataclass(frozen=True, slots=True)
class GpuInfo:
    index: int
    name: str
    memory_total_mib: int


@dataclass(frozen=True, slots=True)
class HardwareReport:
    gpu_count: int
    gpu_names: tuple[str, ...]
    gpu_vram_mib: tuple[int, ...]
    cuda_visible_devices: str | None
    ffmpeg_available: bool
    working_directory: Path
    working_directory_writable: bool


def parse_nvidia_smi_csv(output: str) -> tuple[GpuInfo, ...]:
    gpus: list[GpuInfo] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 3:
            raise ValueError(f"Unexpected nvidia-smi row: {raw_line!r}")
        index, name, memory_total_mib = parts
        gpus.append(GpuInfo(int(index), name, int(memory_total_mib)))
    return tuple(gpus)


def _query_nvidia_smi() -> str:
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def validate_gpu_topology(nvidia_smi_output: str | None = None) -> HardwareReport:
    output = _query_nvidia_smi() if nvidia_smi_output is None else nvidia_smi_output
    gpus = parse_nvidia_smi_csv(output)
    if len(gpus) != 2 or any(gpu.name != "Tesla T4" for gpu in gpus):
        raise RuntimeError("full profile requires exactly two Tesla T4 GPUs")

    working_dir = KAGGLE_WORKING_DIR
    return HardwareReport(
        gpu_count=len(gpus),
        gpu_names=tuple(gpu.name for gpu in gpus),
        gpu_vram_mib=tuple(gpu.memory_total_mib for gpu in gpus),
        cuda_visible_devices=os.getenv("CUDA_VISIBLE_DEVICES"),
        ffmpeg_available=shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None,
        working_directory=working_dir,
        working_directory_writable=working_dir.exists() and os.access(working_dir, os.W_OK),
    )


def ports_are_free(ports: tuple[int, ...] = (8090, 8091, 8092)) -> bool:
    sockets: list[socket.socket] = []
    try:
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sockets.append(sock)
            sock.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        for sock in sockets:
            sock.close()


def build_worker_environment(kind: str) -> dict[str, str]:
    env = os.environ.copy()
    if kind == "translation":
        env["CUDA_VISIBLE_DEVICES"] = "0"
    elif kind == "speech":
        env["CUDA_VISIBLE_DEVICES"] = "1"
    else:
        raise ValueError(f"Unknown worker kind: {kind}")
    return env
