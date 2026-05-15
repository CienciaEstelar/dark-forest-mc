"""
Carga de variables de entorno para el proyecto Bosque Oscuro.

- Si existe un .env en la raíz del proyecto, lo carga.
- Prioriza lo que ya está en el entorno (os.environ).
- Expone helpers para obtener claves de LLM (Gemini, OpenAI).
"""

from __future__ import annotations
import os
from pathlib import Path

try:
    from dotenv import load_dotenv  # pip install python-dotenv
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False


def load_env_if_present(env_path: str | Path | None = None) -> None:
    """
    Intenta cargar un archivo .env si existe.
    No rompe si no existe o no está instalado python-dotenv.
    """
    if not _HAS_DOTENV:
        return

    if env_path is None:
        # asumimos: .../bosque_oscuro/common/env_loader.py
        base = Path(__file__).resolve().parents[1]
        env_path = base / ".env"

    env_path = Path(env_path)
    if env_path.exists():
        load_dotenv(env_path)


def get_gemini_key() -> str | None:
    """
    Devuelve la API key de Gemini buscando en este orden:
    - GEMINI_API_KEY
    - GEMINI_API_KEY_PRO   ← la que tú tienes
    - GOOGLE_API_KEY       ← algunas libs la usan
    """
    return (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GEMINI_API_KEY_PRO")
        or os.getenv("GOOGLE_API_KEY")
    )


def get_openai_key() -> str | None:
    """Devuelve la API key de OpenAI si está definida."""
    return os.getenv("OPENAI_API_KEY")
