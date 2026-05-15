"""
Generación de duraciones y análisis simple de coexistencia temporal.
"""

import numpy as np
import pandas as pd
from scipy.stats import lognorm
from ..common.config import Parametros
from typing import Tuple

def generar_duraciones(n_civs: int, p: Parametros) -> np.ndarray:
    """
    Genera duraciones de civilización (años) usando distribución lognormal acotada.
    """
    dconf = p.distribucion_L
    dur = lognorm(s=dconf["sigma"], scale=dconf["media"]).rvs(n_civs)
    return np.clip(dur, dconf["min"], dconf["max"]).astype(np.float32)

def analizar_coexistencia(df: pd.DataFrame, p: Parametros) -> Tuple[int, int]:
    """
    Calcula:
    - Número máximo de civilizaciones coexistiendo en cualquier momento
    - Número de civilizaciones activas 'hoy' (a la edad de la galaxia)
    """
    if df.empty:
        return 0, 0
    eventos = []
    for r in df.itertuples(index=False):
        eventos.append((r.tiempo_nacimiento_yr, 1))
        eventos.append((r.tiempo_muerte_yr, -1))
    eventos.sort(key=lambda x: x[0])

    max_coex = 0
    actual = 0
    for _, inc in eventos:
        actual += inc
        if actual > max_coex:
            max_coex = actual

    t_hoy = p.edad_galaxia
    activas_hoy = int(((df.tiempo_nacimiento_yr <= t_hoy) & (df.tiempo_muerte_yr >= t_hoy)).sum())
    return max_coex, activas_hoy
