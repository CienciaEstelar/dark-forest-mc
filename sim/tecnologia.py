"""
Evolución tecnológica de detección y probabilidad de detección en función de distancia.
"""

import math
import numpy as np
from ..common.config import Parametros

def radio_deteccion_efectivo(edad: float, nivel_tec: float, p: Parametros) -> float:
    """
    Radio efectivo de detección del 'cazador' dada su edad y nivel tecnológico.
    Sigmoide simple que converge a 'radio_max_realista' y escala por (1+nivel_tec).
    """
    tconf = p.tecnologia_deteccion
    r_max = float(tconf["radio_max_realista"])
    alpha = float(tconf["eficiencia_evolucion"])
    base = r_max / (1.0 + (r_max - 1.0) * math.exp(-alpha * max(0.0, edad)))
    return base * (1.0 + max(0.0, nivel_tec))

def prob_deteccion(dist: float, edad_cazador: float, nivel_tec: float, p: Parametros) -> float:
    """
    Probabilidad de detección decreciente con la distancia, saturada en [0,1].
    Perfil lorentziano: 1/(1+(d/d₀)²) con d₀ desde config.

    P_det → 0 cuando d → ∞: los falsos positivos (p_fp) NO participan del
    canal de detección de blancos reales — un falso positivo apunta a cielo
    vacío, no a una civilización existente. Antes del fix 2026-07-11, p_fp
    actuaba como piso a cualquier distancia y generaba >96 % de las
    destrucciones con mediana ~32 000 al.
    """
    r_eff = radio_deteccion_efectivo(edad_cazador, nivel_tec, p)
    # Atenuación lorentziana con distancia (d₀ desde config)
    d0 = float(p.tecnologia_deteccion.get("d0_atenuacion", 100.0))
    atenuacion = 1.0 / (1.0 + (dist / d0) ** 2)
    pr = min(1.0, r_eff / p.tecnologia_deteccion["radio_max_realista"]) * atenuacion
    # Falsos negativos (señal real perdida por ruido del sistema)
    pr = pr * (1.0 - p.tecnologia_deteccion["probabilidad_falsos_negativos"])
    return min(1.0, max(0.0, pr))


def prob_deteccion_batch(dists: np.ndarray, edad_cazador: float, nivel_tec: float,
                         p: Parametros) -> np.ndarray:
    """
    Versión vectorizada de prob_deteccion para arrays de distancias.

    Procesa n distancias simultáneamente con operaciones numpy,
    eliminando ~n llamadas a la función escalar y ~n operaciones math.
    Usada por paso5_bosque_oscuro para el loop interno de presas.

    Parameters
    ----------
    dists : np.ndarray (n,)
        Array de distancias en años-luz.
    edad_cazador, nivel_tec : float
        Edad y nivel tecnológico del cazador (un solo valor).
    p : Parametros
        Configuración del modelo.

    Returns
    -------
    np.ndarray (n,)
        Probabilidades de detección para cada distancia.
    """
    r_eff = radio_deteccion_efectivo(edad_cazador, nivel_tec, p)
    d0 = float(p.tecnologia_deteccion.get("d0_atenuacion", 100.0))
    rho = min(1.0, r_eff / float(p.tecnologia_deteccion["radio_max_realista"]))
    p_fn = float(p.tecnologia_deteccion["probabilidad_falsos_negativos"])

    atenuacion = 1.0 / (1.0 + (dists / d0) ** 2)
    # Sin piso p_fp: ver docstring de prob_deteccion (fix 2026-07-11)
    pr = rho * atenuacion * (1.0 - p_fn)
    return np.clip(pr, 0.0, 1.0)
