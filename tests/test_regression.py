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
# Actualizados 2026-05-10: vectorización del loop interno de paso5
# cambia la secuencia de números aleatorios (np.random.random(n) vs n×random())
# pero preserva las propiedades estadísticas del modelo.
# ---------------------------------------------------------------------------
FIXTURES = {
    42:  {"destruidas": 61,  "dist_vecino": 1874.3, "ratio": 1.4605},
    7:   {"destruidas": 67,  "dist_vecino": 1784.1, "ratio": 1.3828},
    13:  {"destruidas": 70,  "dist_vecino": 1821.6, "ratio": 1.4081},
    99:  {"destruidas": 67,  "dist_vecino": 1855.1, "ratio": 1.4378},
    256: {"destruidas": 80,  "dist_vecino": 1877.4, "ratio": 1.4381},
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
