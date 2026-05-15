"""
Factory function canónica para generación de catálogos de civilizaciones.

Centraliza la lógica de inicialización que estaba duplicada en 6 archivos:
pipeline.py, sensibilidad.py, multiseed.py, multiseed_optimista.py,
control_multiseed.py, test_regression.py.

Uso:
    from .factory import crear_catalogo
    df = crear_catalogo(N_c, p, seed=42)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional

from ..common.config import Parametros
from .espacio import generar_posiciones
from .tiempos import generar_duraciones


def crear_catalogo(n_civs: int, p: Parametros, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Genera un catálogo inicial de civilizaciones con posiciones galácticas,
    duraciones lognormal, tiempos de nacimiento uniformes y tipos sociológicos.

    Parameters
    ----------
    n_civs : int
        Número de civilizaciones a generar.
    p : Parametros
        Configuración del modelo (Drake, GHZ, sociología, etc.).
    seed : int or None
        Semilla para reproducibilidad. Si es None, usa el estado actual de numpy.

    Returns
    -------
    pd.DataFrame
        Catálogo con columnas: id_civilizacion, posicion_x_ly, posicion_y_ly,
        posicion_z_ly, tiempo_nacimiento_yr, tiempo_muerte_yr, duracion_yr,
        tipo_sociologico, nivel_tecnologico_inicial, estado.
    """
    if seed is not None:
        np.random.seed(seed)

    pos = generar_posiciones(n_civs, p)
    dur = generar_duraciones(n_civs, p)
    nac = np.random.uniform(
        1e9, p.edad_galaxia - float(dur.max()), size=n_civs
    ).astype(np.float32)

    tipos = np.random.choice(
        ["agresivo", "defensivo", "pacifico", "curioso"],
        size=n_civs,
        p=[
            p.sociologia["probabilidad_ataque_agresivo"],
            p.sociologia["probabilidad_ataque_defensivo"],
            p.sociologia["probabilidad_pacifico"],
            p.sociologia["probabilidad_curioso"],
        ],
    )

    return pd.DataFrame({
        "id_civilizacion": np.arange(n_civs, dtype=np.int64),
        "posicion_x_ly": pos[:, 0],
        "posicion_y_ly": pos[:, 1],
        "posicion_z_ly": pos[:, 2],
        "tiempo_nacimiento_yr": nac,
        "tiempo_muerte_yr": nac + dur,
        "duracion_yr": dur,
        "tipo_sociologico": tipos,
        "nivel_tecnologico_inicial": np.random.lognormal(0.0, 1.0, size=n_civs).astype(np.float32),
        "estado": "activa",
    })
