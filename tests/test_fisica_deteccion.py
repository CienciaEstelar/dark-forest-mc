"""
Tests de física del canal de detección letal (fix 2026-07-11).

Dos propiedades que el modelo debe cumplir:

1. Sin piso de falsos positivos: P_det → 0 cuando d → ∞.
   Un falso positivo (detectar una señal donde no hay nada) no puede
   producir la detección efectiva de una civilización real a distancia
   arbitraria. Antes del fix, P_det(d→∞) → p_fp = 0.01, lo que generaba
   el ~96-99 % de las destrucciones con mediana de ~32 000 al.

2. Causalidad: una civilización solo puede ser detectada si su señal
   tuvo tiempo de llegar al cazador: d ≤ c · (t − t_nac_presa).
   Antes del fix, el 30 % de los kills eran acausales.

Run from ~/Escritorio/:
    python -m pytest bosque_oscuro/tests/test_fisica_deteccion.py -v
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bosque_oscuro.common.config import Parametros
from bosque_oscuro.sim.sociologia import normalizar_probabilidades
from bosque_oscuro.sim.tecnologia import prob_deteccion, prob_deteccion_batch
from bosque_oscuro.sim.factory import crear_catalogo
from bosque_oscuro.sim.dinamica import paso5_bosque_oscuro


@pytest.fixture
def params():
    p = Parametros()
    normalizar_probabilidades(p)
    return p


def test_prob_deteccion_sin_piso_a_gran_distancia(params):
    """P_det a distancia galáctica debe ser ~0, no el piso p_fp=0.01."""
    edad_madura = 5e7
    for d in [10_000.0, 25_000.0, 50_000.0]:
        pr = prob_deteccion(d, edad_madura, 1.0, params)
        assert pr < 1e-3, (
            f"P_det(d={d}) = {pr:.5f}: el piso de falsos positivos sigue "
            "actuando como canal de detección letal a distancia galáctica"
        )


def test_prob_deteccion_batch_sin_piso(params):
    """La versión vectorizada debe coincidir: sin piso a gran distancia."""
    dists = np.array([10_000.0, 25_000.0, 50_000.0])
    pr = prob_deteccion_batch(dists, 5e7, 1.0, params)
    assert (pr < 1e-3).all(), f"batch con piso residual: {pr}"


def test_batch_consistente_con_escalar(params):
    """prob_deteccion_batch debe dar lo mismo que prob_deteccion punto a punto."""
    dists = np.array([10.0, 100.0, 500.0, 1_000.0, 5_000.0])
    esperado = np.array([prob_deteccion(float(d), 1e6, 0.5, params) for d in dists])
    obtenido = prob_deteccion_batch(dists, 1e6, 0.5, params)
    np.testing.assert_allclose(obtenido, esperado, rtol=1e-12)


def test_no_kills_acausales(params):
    """Ningún kill puede ocurrir antes de que la señal de la presa llegue al cazador."""
    cat = crear_catalogo(440, params, seed=42)
    nac = dict(zip(cat["id_civilizacion"].astype(int), cat["tiempo_nacimiento_yr"].astype(float)))
    _, hist = paso5_bosque_oscuro(cat, params)

    v_luz = float(params.propagacion["velocidad_luz"])
    for r in hist.itertuples(index=False):
        edad_presa = float(r.tiempo_evento_yr) - nac[int(r.presa_id)]
        assert r.distancia_ly <= edad_presa * v_luz + 1e-6, (
            f"Kill acausal: presa {int(r.presa_id)} destruida a {r.distancia_ly:.0f} al "
            f"cuando su señal solo pudo viajar {edad_presa * v_luz:.0f} al"
        )
