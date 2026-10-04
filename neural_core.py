from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

"""
Forge Neural Core
-----------------
Optional local open-weight language-model runtime.

The model is NOT committed to GitHub. Put a GGUF model on the machine and set:
    FORGE_LOCAL_MODEL_PATH=/absolute/path/to/model.gguf

If llama-cpp-python is available, Quantum Forge can run the model locally with no
LLM API call. If it is not available, callers should use the built-in cognitive
core fallback. This keeps the current Render deployment safe while providing a
real path to a much stronger self-hosted AI.
"""

_MODEL = None
_MODEL_PATH = None
_LOAD_ERROR = None


def status() -> dict[str, Any]:
    path = os.getenv("FORGE_LOCAL_MODEL_PATH", "").strip()
    return {
        "enabled": bool(path),
        "model_path_configured": bool(path),
        "model_exists": bool(path and Path(path).exists()),
        "runtime": "llama.cpp" if _MODEL is not None else "not_loaded",
        "load_error": _LOAD_ERROR,
        "mode": "LOCAL_NEURAL_MODEL" if _MODEL is not None else "BUILT_IN_COGNITIVE_CORE",
    }


def _load():
    global _MODEL, _MODEL_PATH, _LOAD_ERROR
    path = os.getenv("FORGE_LOCAL_MODEL_PATH", "").strip()
    if not path:
        return None
    if _MODEL is not None and _MODEL_PATH == path:
        return _MODEL
    if not Path(path).exists():
        _LOAD_ERROR = f"Model file not found: {path}"
        return None
    try:
        from llama_cpp import Llama
        _MODEL = Llama(
            model_path=path,
            n_ctx=int(os.getenv("FORGE_LOCAL_CONTEXT", "8192")),
            n_threads=max(1, int(os.getenv("FORGE_LOCAL_THREADS", str(os.cpu_count() or 2)))),
            n_gpu_layers=int(os.getenv("FORGE_LOCAL_GPU_LAYERS", "0")),
            verbose=False,
        )
        _MODEL_PATH = path
        _LOAD_ERROR = None
        return _MODEL
    except Exception as exc:
        _LOAD_ERROR = f"{type(exc).__name__}: {exc}"
        return None


def generate(system: str, user: str, temperature: float = 0.2, max_tokens: int = 900) -> str:
    model = _load()
    if model is None:
        return ""
    try:
        result = model.create_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        global _LOAD_ERROR
        _LOAD_ERROR = f"{type(exc).__name__}: {exc}"
        return ""


def configured() -> bool:
    return _load() is not None
