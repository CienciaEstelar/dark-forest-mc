"""
Regression tests for Dark Forest Monte Carlo.

Fixtures captured post FIX1-4, MEJORA1-5, FIXA-C, OPT1-2, MANT1-2.
A test failure means a code change altered the model's deterministic output.

Run from ~/Escritorio/:
    python -m pytest bosque_oscuro/tests/test_regression.py -v
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure the package is importable when running from ~/Escritorio/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bosque_oscuro.common.config import Parametros
from bosque_oscuro.sim.sociologia import normalizar_probabilidades
from bosque_oscuro.sim.espacio import generar_posiciones
from bosque_oscuro.sim.tiempos import generar_duraciones
from bosque_oscuro.sim.dinamica import paso5_bosque_oscuro
from bosque_oscuro.analysis.vecino import analizar_vecino_mas_cercano

# ---------------------------------------------------------------------------
# Hardcoded fixtures — DO NOT EDIT without re-running the full model
# Actualizados 2026-07-11: fix físico del canal de detección letal —
# (1) eliminado el piso de falsos positivos p_fp de prob_deteccion
#     (generaba >96 % de las destrucciones, con mediana ~32 000 al), y
# (2) check de causalidad en paso5: d ≤ c·(t − t_nac_presa)
#     (antes el 30 % de los kills eran acausales).
# Valores previos (modelo con artefacto): destruidas 61-80 por seed.
# ---------------------------------------------------------------------------
FIXTURES = {
    42:  {"destruidas": 1,  "dist_vecino": 1791.5, "ratio": 1.4660},
    7:   {"destruidas": 0,  "dist_vecino": 1638.6, "ratio": 1.3419},
    13:  {"destruidas": 3,  "dist_vecino": 1747.4, "ratio": 1.4278},
    99:  {"destruidas": 6,  "dist_vecino": 1824.9, "ratio": 1.4877},
    256: {"destruidas": 3,  "dist_vecino": 1710.3, "ratio": 1.3975},
}

DIST_TOL = 50.0   # ly
RATIO_TOL = 0.05


def _run_seed(seed: int, tmp_path: Path) -> dict:
    p = Parametros()
    normalizar_probabilidades(p)

    N_hp = p.num_estrellas * p.fraccion_con_planetas * p.planetas_zona_habitable_promedio
    N_c = int(N_hp * p.filtro_pesimista["f_l"] * p.filtro_pesimista["f_i"] * p.filtro_pesimista["f_c"])

    from bosque_oscuro.sim.factory import crear_catalogo
    catalogo = crear_catalogo(N_c, p, seed=seed)

    fin, _ = paso5_bosque_oscuro(catalogo, p)
    destruidas = int((fin["estado"] == "destruida").sum())
    activas_df = fin[fin["estado"] == "activa"].copy()

    _, stats = analizar_vecino_mas_cercano(activas_df, tmp_path, dpi=72, p=p)

    return {
        "destruidas": destruidas,
        "dist_vecino": round(float(stats.get("media", float("nan"))), 1),
        "ratio": round(float(stats.get("ratio_obs_poisson", float("nan"))), 4),
    }


@pytest.mark.parametrize("seed", sorted(FIXTURES))
def test_regression_seed(seed, tmp_path):
    expected = FIXTURES[seed]
    actual = _run_seed(seed, tmp_path)

    assert actual["destruidas"] == expected["destruidas"], (
        f"seed={seed}: destruidas {actual['destruidas']} != {expected['destruidas']}"
    )
    assert abs(actual["dist_vecino"] - expected["dist_vecino"]) <= DIST_TOL, (
        f"seed={seed}: dist_vecino {actual['dist_vecino']} ly, "
        f"expected {expected['dist_vecino']} ± {DIST_TOL} ly"
    )
    assert abs(actual["ratio"] - expected["ratio"]) <= RATIO_TOL, (
        f"seed={seed}: ratio {actual['ratio']}, "
        f"expected {expected['ratio']} ± {RATIO_TOL}"
    )
