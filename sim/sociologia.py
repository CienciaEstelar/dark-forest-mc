"""
Modelado sociológico:
- Normalización de probabilidades
- Regla de decisión de ataque basada en tipo y umbral de amenaza
- Estrategia de la presa: ATACAR / ESCONDERSE / COMUNICAR
"""

import numpy as np
import pandas as pd
from ..common.config import Parametros

TIPOS = ["agresivo", "defensivo", "pacifico", "curioso"]
ESTRATEGIAS = ["ATACAR", "ESCONDERSE", "COMUNICAR"]

# Radio para detectar destrucciones en la vecindad de una presa (ly)
RADIO_VECINDAD_PRESA: float = 500.0

# Probabilidades base [ATACAR, ESCONDERSE, COMUNICAR] por tipo sociológico
_PROBS_ESTRATEGIA: dict = {
    "agresivo":  [0.65, 0.10, 0.25],
    "defensivo": [0.20, 0.60, 0.20],
    "pacifico":  [0.05, 0.75, 0.20],
    "curioso":   [0.10, 0.15, 0.75],
}

# Modificadores sobre prob_deteccion según estrategia activa
# ATACAR → civ más ruidosa: +20 % detección sobre ella misma (cuando es presa)
#          y +20 % al detectar (cuando es cazadora)
# ESCONDERSE → emite al 0.1 % del normal → pr_det sobre ella *= 0.001
# COMUNICAR  → emite al 300 % del normal → pr_det sobre ella *= 3.0
MODIF_DETECCION_PRESA: dict = {
    "ATACAR":     1.20,
    "ESCONDERSE": 0.001,
    "COMUNICAR":  3.00,
    "NINGUNA":    1.00,
}
MODIF_DETECCION_CAZADOR: dict = {
    "ATACAR":  1.20,  # cazador agresivo detecta mejor
    "NINGUNA": 1.00,
    "ESCONDERSE": 1.00,
    "COMUNICAR":  1.00,
}

def normalizar_probabilidades(p: Parametros) -> None:
    keys = [k for k in p.sociologia.keys() if k.startswith("probabilidad_")]
    total = sum(p.sociologia[k] for k in keys)
    if abs(total - 1.0) > 1e-6:
        for k in keys:
            p.sociologia[k] /= total

def decision_presa(tipo: str, n_destruidas_vecindad: int, n_zonas_peligrosas: int = 0) -> str:
    """
    Elige la estrategia de una civilización como presa potencial.

    Bajo presión (destrucciones en la vecindad de 500 ly), aumenta la tendencia
    a ESCONDERSE en detrimento de ATACAR y COMUNICAR.
    Si hay zonas peligrosas en memoria (Mejora 3), COMUNICAR se reduce un 80 %.
    """
    probs = list(_PROBS_ESTRATEGIA.get(tipo, [0.33, 0.34, 0.33]))

    # Presión ambiental: destrucciones cercanas → shift hacia ESCONDERSE
    if n_destruidas_vecindad > 0:
        ajuste = min(0.40, n_destruidas_vecindad * 0.10)
        probs[0] = max(0.0, probs[0] - ajuste * 0.50)  # ATACAR baja
        probs[1] = min(1.0, probs[1] + ajuste)          # ESCONDERSE sube
        probs[2] = max(0.0, probs[2] - ajuste * 0.50)  # COMUNICAR baja
        total = sum(probs)
        probs = [v / total for v in probs]

    # Memoria de zonas peligrosas (Mejora 3): penaliza COMUNICAR un 80 %
    if n_zonas_peligrosas > 0:
        penaliz = probs[2] * 0.80
        probs[2] -= penaliz
        probs[1] += penaliz  # traslada la masa a ESCONDERSE
        total = sum(probs)
        probs = [v / total for v in probs]

    return str(np.random.choice(ESTRATEGIAS, p=probs))


def decision_ataque(cazador_row: pd.Series, presa_row: pd.Series, p: Parametros) -> bool:
    """
    Devuelve True si el cazador decide atacar a la presa.
    - Matriz de agresividad por tipo
    - Escalamiento si la presa supera umbral_amenaza relativo al cazador
    """
    matriz = {"agresivo": 0.9, "defensivo": 0.6, "pacifico": 0.1, "curioso": 0.3}
    base = matriz.get(str(cazador_row["tipo_sociologico"]), 0.1)
    umbral = float(p.sociologia["umbral_amenaza"])
    rel = float(presa_row["nivel_tecnologico_inicial"] / max(1e-9, cazador_row["nivel_tecnologico_inicial"]))
    prob = min(1.0, base * (1.5 if rel > umbral else 1.0))
    return (np.random.random() < prob)
