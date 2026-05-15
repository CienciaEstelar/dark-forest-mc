"""
Validaciones:
- Integridad de datos
- Validación externa contra benchmarks tipo Drake
"""

from typing import Dict
import numpy as np
import pandas as pd
from ..common.config import Parametros

def checks_integridad(df: pd.DataFrame) -> Dict[str, bool]:
    checks = {
        "sin_nan": (not df.isnull().any().any()),
        "tiempos_ok": (df["tiempo_muerte_yr"] >= df["tiempo_nacimiento_yr"]).all(),
        "ids_unicos": df["id_civilizacion"].is_unique,
        "estados_validos": df["estado"].isin(["activa", "destruida"]).all(),
        "duraciones_pos": (df["duracion_yr"] > 0).all(),
        "posiciones_finitas": np.isfinite(df[["posicion_x_ly","posicion_y_ly","posicion_z_ly"]]).all().all()
    }
    return checks

def calibracion_drake(N_c: float, p: Parametros) -> Dict[str, Dict[str, float]]:
    """
    Calibración cualitativa del número de civilizaciones generadas respecto a
    estimaciones clásicas de la ecuación de Drake. No es una validación formal:
    la diferencia de órdenes de magnitud entre escenarios pesimista y optimista
    es esperada y científicamente significativa por sí misma.
    """
    resultados = {}
    for name, bm in p.benchmarks.items():
        N_teo = bm["N"] * bm["fp"] * bm["ne"] * bm["fl"] * bm["fi"] * bm["fc"] * bm["L"]
        err_rel = abs(N_c - N_teo) / N_teo if N_teo > 0 else float("inf")
        resultados[name] = {
            "N_drake_referencia": float(N_teo),
            "N_simulado": float(N_c),
            "error_relativo": float(err_rel),
            "en_rango_calibracion": bool(err_rel <= bm["tolerance"])
        }
    return resultados
