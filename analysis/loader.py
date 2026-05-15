"""
Carga estándar de resultados de simulación desde una carpeta de salida.

Este módulo asume el formato que te deja el pipeline de simulación:
bosque_oscuro_output/
  ├─ catalogos/
  │    ├─ catalogo_civilizaciones_pesimista.csv
  │    ├─ catalogo_final_paso5_pesimista.csv
  │    └─ historial_destruccion_paso5_pesimista.csv
  └─ ...

Si alguno no está, lo reporta pero no rompe.
"""

from pathlib import Path
from typing import Dict, Optional
import pandas as pd

def cargar_catalogos(base_dir: str | Path) -> Dict[str, pd.DataFrame]:
    """
    Carga todos los CSV relevantes de una simulación.

    Parameters
    ----------
    base_dir : str | Path
        Directorio raíz de la simulación (el que tiene /catalogos).

    Returns
    -------
    dict
        Diccionario con claves estándar:
        - civs_pesimista
        - civs_pesimista_p5
        - historial_p5
    """
    base = Path(base_dir)
    cat_dir = base / "catalogos"

    out: Dict[str, pd.DataFrame] = {}

    pes_path = cat_dir / "catalogo_civilizaciones_pesimista.csv"
    if pes_path.exists():
        out["civs_pesimista"] = pd.read_csv(pes_path)
    else:
        out["civs_pesimista"] = pd.DataFrame()

    pes_p5_path = cat_dir / "catalogo_final_paso5_pesimista.csv"
    if pes_p5_path.exists():
        out["civs_pesimista_p5"] = pd.read_csv(pes_p5_path)
    else:
        out["civs_pesimista_p5"] = pd.DataFrame()

    hist_p5_path = cat_dir / "historial_destruccion_paso5_pesimista.csv"
    if hist_p5_path.exists():
        out["historial_p5"] = pd.read_csv(hist_p5_path)
    else:
        out["historial_p5"] = pd.DataFrame()

    # opcional: optimista
    opt_path = cat_dir / "catalogo_civilizaciones_optimista.csv"
    if opt_path.exists():
        out["civs_optimista"] = pd.read_csv(opt_path)
    else:
        out["civs_optimista"] = pd.DataFrame()

    opt_p5_path = cat_dir / "catalogo_final_paso5_optimista.csv"
    if opt_p5_path.exists():
        out["civs_optimista_p5"] = pd.read_csv(opt_p5_path)
    else:
        out["civs_optimista_p5"] = pd.DataFrame()

    return out
