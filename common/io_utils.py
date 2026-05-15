"""
Utilidades de entrada/salida, logging simple y helpers de guardado.

Design:
- Logger minimalista que imprime por pantalla y escribe a archivo
- Helpers para asegurar estructura de directorios y escribir CSV/TXT/JSON
- Conversión segura de tipos numpy → tipos Python nativos
"""

from typing import Dict, Any
import os
import json
import pandas as pd
from datetime import datetime
import numpy as np  # para detectar tipos numpy


class Logger:
    """Logger minimalista con timestamp; escribe en consola y en un archivo plano."""
    def __init__(self, log_path: str):
        self.log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write("=== SCIENTIFIC DARK FOREST SIMULATION LOG ===\n")
            f.write(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n")

    def log(self, msg: str, level: str = "INFO"):
        line = f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}][{level}] {msg}"
        print(f"📝 {line}")
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def ensure_structure(outdir: str) -> Dict[str, str]:
    """Crea la estructura de carpetas necesaria y devuelve un dict de rutas."""
    subdirs = {
        "base": outdir,
        "catalogos": os.path.join(outdir, "catalogos"),
        "visualizaciones": os.path.join(outdir, "visualizaciones"),
        "analisis": os.path.join(outdir, "analisis"),
        "animaciones": os.path.join(outdir, "animaciones"),
        "logs": os.path.join(outdir, "logs_detallados"),
        "validacion": os.path.join(outdir, "validacion"),
        "sensibilidad": os.path.join(outdir, "sensibilidad"),
        "reportes": os.path.join(outdir, "reportes"),
    }
    for p in subdirs.values():
        os.makedirs(p, exist_ok=True)
    return subdirs


def _to_serializable(obj: Any) -> Any:
    """
    Convierte objetos numpy a tipos Python nativos para que json.dump no falle.
    """
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    return obj


def save_txt(path: str, content: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def save_json(path: str, content: Dict[str, Any]) -> str:
    """
    Guarda un JSON convirtiendo previamente tipos numpy → Python.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)

    def convert(d):
        if isinstance(d, dict):
            return {k: convert(v) for k, v in d.items()}
        if isinstance(d, list):
            return [convert(x) for x in d]
        return _to_serializable(d)

    safe_content = convert(content)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(safe_content, f, indent=2, ensure_ascii=False)
    return path


def save_csv(path: str, df: pd.DataFrame) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return path
