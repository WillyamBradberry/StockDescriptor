"""
VRAM Manager — manage GPU memory for ComfyUI + LM Studio lifecycle.

Used by both CLI (server.py) and Web UI (queue worker) to coordinate
VRAM between image generation (ComfyUI/flux) and LLM analysis (LM Studio/qwen).

Key functions:
    preflight(comfyui_url, timeout=5)   — free ComfyUI VRAM before LM Studio loads
    postflight(unload_all=True)         — unload models after processing
"""

import asyncio
import sys
from typing import Optional


# Ensure project root is on sys.path when imported from web_app
_PROJECT_ROOT = __import__("os").path.normpath(
    __import__("os").path.join(
        __import__("os").path.dirname(__import__("os").path.abspath(__file__)), ".."
    )
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def preflight(server_address: str = "http://127.0.0.1:8188", timeout: int = 5) -> None:
    """Free ComfyUI VRAM before LM Studio loads for analysis.

    If ComfyUI has models loaded, free them first — otherwise LM Studio
    may fail to load due to insufficient VRAM.

    Args:
        server_address: ComfyUI server URL.
        timeout: Seconds to wait for availability check.
    """
    from pipeline.comfy_client import ComfyUIClient

    comfy = ComfyUIClient(server_address=server_address)
    if not comfy.is_available(timeout=timeout):
        print(f"[~] VRAM: ComfyUI не запущен — пропускаю очистку.")
        return

    if not comfy.is_any_model_loaded(timeout=timeout):
        print("[~] VRAM: ComfyUI свободна, ничего освобождать не нужно.")
        return

    print("[~] VRAM: ComfyUI модели загружены. Освобождаю VRAM перед LM Studio...")
    try:
        comfy.free_memory()
        print("[+] VRAM: Команда на освобождение отправлена.")
    except Exception as e:
        print(f"[-] VRAM: Ошибка при освобождении: {e}")


def preflight_sync(server_address: str = "http://127.0.0.1:8188", timeout: int = 5) -> None:
    """Synchronous wrapper for preflight (for synchronous callers)."""
    preflight(server_address, timeout)


async def preflight_async(server_address: str = "http://127.0.0.1:8188", timeout: int = 5) -> None:
    """Async version of preflight — runs sync code in executor."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, preflight, server_address, timeout)


def postflight(config: dict = None) -> None:
    """Unload all models from GPU after processing.

    Args:
        config: Optional config dict for ComfyUI settings.
    """
    try:
        from pipeline.model_unloader import unload_all
        unload_all()
        print("[+] VRAM: Все модели выгружены.")
    except Exception as e:
        print(f"[-] VRAM: Ошибка при выгрузке моделей: {e}")


def postflight_sync(config: dict = None) -> None:
    """Synchronous wrapper for postflight."""
    postflight(config)
