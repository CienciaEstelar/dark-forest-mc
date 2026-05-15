"""
Análisis de sensibilidad (Sobol) con SALib.

- sobol_drake(): Sobol sobre parámetros Drake (N_c como salida).
- sobol_bosque_oscuro(): Sobol sobre parámetros de la dinámica del BF
  (tasa de destrucción como salida). Mini-simulación de 100 civs por muestra.
  N=32 por defecto (config); N=512 recomendado para publicación (ver docstring).

Si SALib no está instalado, ambas funciones devuelven None limpiamente.
"""

import copy
import hashlib
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any

try:
    from SALib.sample import saltelli
    from SALib.analyze import sobol
    HAVE_SALIB = True
except Exception:
    HAVE_SALIB = False

from ..common.config import Parametros


# ---------------------------------------------------------------------------
# Sobol sobre ecuación Drake (función original)
# ---------------------------------------------------------------------------

def sobol_drake(p: Parametros) -> Optional[Dict[str, Any]]:
    """Sobol sobre f_l, f_i, f_c de la ecuación Drake → N_c como salida."""
    if not HAVE_SALIB:
        return None

    problem = {
        "num_vars": 3,
        "names": ["f_l", "f_i", "f_c"],
        "bounds": [[1e-5, 1e-1], [1e-5, 1e-1], [1e-3, 0.5]]
    }
    N = int(p.sensibilidad.get("N", 32))
    param_values = saltelli.sample(problem, N, calc_second_order=True)

    def eval_model(vals):
        f_l, f_i, f_c = vals
        return p.num_estrellas * p.fraccion_con_planetas * p.planetas_zona_habitable_promedio * f_l * f_i * f_c

    Y = np.array([eval_model(v) for v in param_values], dtype=float)
    return sobol.analyze(problem, Y, print_to_console=False)


# ---------------------------------------------------------------------------
# Sobol sobre dinámica del Bosque Oscuro
# ---------------------------------------------------------------------------

def sobol_bosque_oscuro(p: Parametros) -> Optional[Dict[str, Any]]:
    """
    Análisis de Sobol sobre la TASA DE DESTRUCCIÓN del Bosque Oscuro.

    Parámetros variados:
        - umbral_amenaza          : [0.30, 0.90]
        - eficiencia_evolucion    : [0.001, 0.10]
        - prob_agresivo           : [0.10, 0.50]
        - radio_max_realista      : [50, 500] ly
        - d0_atenuacion           : [25, 500] ly

    Cada evaluación corre una mini-simulación de 100 civs y devuelve la
    tasa de destrucción (%) como salida escalar.

    N configurado en p.sensibilidad["N"] (32 por defecto).
    Para publicación se recomienda N=512 (~50 seg con 100 civs/muestra).
    Reporta índices de primer orden (S1) y total (ST).
    """
    if not HAVE_SALIB:
        return None

    # Importaciones dentro de la función para evitar circularidad en módulo
    from .espacio import generar_posiciones
    from .tiempos import generar_duraciones
    from .dinamica import paso5_bosque_oscuro
    from .sociologia import normalizar_probabilidades

    problem = {
        "num_vars": 5,
        "names": ["umbral_amenaza", "eficiencia_evolucion", "prob_agresivo", "radio_max_realista", "d0_atenuacion"],
        "bounds": [
            [0.30, 0.90],
            [0.001, 0.10],
            [0.10, 0.50],
            [50.0, 500.0],
            [25.0, 500.0],
        ],
    }
    N = int(p.sensibilidad.get("N", 32))
    param_values = saltelli.sample(problem, N, calc_second_order=True)

    def eval_bf(vals: np.ndarray) -> float:
        # Semilla determinista derivada del hash de parámetros para reproducibilidad
        seed = int(hashlib.md5(vals.astype(np.float64).tobytes()).hexdigest()[:8], 16) % (2**31)
        np.random.seed(seed)

        umbral, efic_evol, prob_agr, radio_max, d0 = float(vals[0]), float(vals[1]), float(vals[2]), float(vals[3]), float(vals[4])

        p_sim = copy.deepcopy(p)
        p_sim.sociologia["umbral_amenaza"] = umbral
        p_sim.tecnologia_deteccion["eficiencia_evolucion"] = efic_evol
        p_sim.tecnologia_deteccion["radio_max_realista"] = radio_max
        p_sim.tecnologia_deteccion["d0_atenuacion"] = d0

        # Redistribuir probabilidades sociológicas manteniendo ratio defensivo/pacifico/curioso
        resto_original = (
            p.sociologia["probabilidad_ataque_defensivo"]
            + p.sociologia["probabilidad_pacifico"]
            + p.sociologia["probabilidad_curioso"]
        )
        resto_nuevo = 1.0 - prob_agr
        if resto_original > 0.0:
            escala = resto_nuevo / resto_original
        else:
            escala = 1.0
        p_sim.sociologia["probabilidad_ataque_agresivo"] = prob_agr
        p_sim.sociologia["probabilidad_ataque_defensivo"] = (
            p.sociologia["probabilidad_ataque_defensivo"] * escala
        )
        p_sim.sociologia["probabilidad_pacifico"] = p.sociologia["probabilidad_pacifico"] * escala
        p_sim.sociologia["probabilidad_curioso"] = p.sociologia["probabilidad_curioso"] * escala
        normalizar_probabilidades(p_sim)

        # Mini-simulación con 100 civs
        n = 100
        from .factory import crear_catalogo
        df_mini = crear_catalogo(n, p_sim)

        fin, _ = paso5_bosque_oscuro(df_mini, p_sim)
        return float((fin["estado"] == "destruida").sum() / n * 100.0)

    Y = np.array([eval_bf(v) for v in param_values], dtype=float)
    si = sobol.analyze(problem, Y, print_to_console=False, calc_second_order=True)

    return {
        "S1":  si["S1"].tolist(),
        "S1_conf": si["S1_conf"].tolist(),
        "ST":  si["ST"].tolist(),
        "ST_conf": si["ST_conf"].tolist(),
        "nombres": problem["names"],
        "Y_media": float(Y.mean()),
        "Y_std":   float(Y.std()),
        "n_evaluaciones": len(Y),
    }
