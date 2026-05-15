"""
Multi-seed robustness analysis — escenario optimista.

Usa filtros Drake optimistas (f_l=0.1, f_i=0.01, f_c=0.2) con cap=optimistic_cap.
Reporta media ± std de destruidas, % tasa, dist_vecino, ratio_Poisson.

Run from ~/Escritorio/:
    python -m bosque_oscuro.multiseed_optimista
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .common.config import Parametros
from .sim.sociologia import normalizar_probabilidades
from .sim.espacio import generar_posiciones
from .sim.tiempos import generar_duraciones
from .sim.dinamica import paso5_bosque_oscuro
from .analysis.vecino import analizar_vecino_mas_cercano

SEEDS = [42, 7, 13, 99, 256, 1337, 2024, 2025, 3, 17]
OUTPUT_PATH = Path(__file__).parent.parent / "output_sim" / "multiseed_optimista_results.json"


def _simular_y_analizar_opt(seed: int, p: Parametros) -> dict:
    N_hp = p.num_estrellas * p.fraccion_con_planetas * p.planetas_zona_habitable_promedio
    N_c_raw = int(N_hp * p.filtro_optimista["f_l"] * p.filtro_optimista["f_i"] * p.filtro_optimista["f_c"])
    N_c = min(N_c_raw, p.optimistic_cap)

    from .sim.factory import crear_catalogo
    catalogo = crear_catalogo(N_c, p, seed=seed)

    fin, hist = paso5_bosque_oscuro(catalogo, p)

    destruidas = int((fin["estado"] == "destruida").sum())
    activas_df = fin[fin["estado"] == "activa"].copy()

    tmp_dir = OUTPUT_PATH.parent / "multiseed_opt_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    _, stats = analizar_vecino_mas_cercano(activas_df, tmp_dir, dpi=72, p=p)

    return {
        "seed": seed,
        "N_c": N_c,
        "N_c_raw": N_c_raw,
        "destruidas": destruidas,
        "pct_destruidas": round(destruidas / N_c * 100, 2),
        "activas": N_c - destruidas,
        "dist_media_vecino_ly": round(float(stats.get("media", float("nan"))), 1),
        "ratio_obs_poisson": round(float(stats.get("ratio_obs_poisson", float("nan"))), 4),
        "ks_p_valor": float(stats.get("ks_poisson", {}).get("ks_p_valor", float("nan"))),
    }


def main() -> None:
    p = Parametros()
    normalizar_probabilidades(p)

    N_hp = p.num_estrellas * p.fraccion_con_planetas * p.planetas_zona_habitable_promedio
    N_c_raw = int(N_hp * p.filtro_optimista["f_l"] * p.filtro_optimista["f_i"] * p.filtro_optimista["f_c"])
    N_c = min(N_c_raw, p.optimistic_cap)

    print(f"Multi-seed análisis optimista — {len(SEEDS)} seeds")
    print(f"N_c raw: {N_c_raw:,}  |  cap: {p.optimistic_cap:,}  |  efectivo: {N_c:,}")
    print(f"Seeds: {SEEDS}\n")

    resultados = []
    for seed in SEEDS:
        print(f"  Seed {seed:>5} ...", end=" ", flush=True)
        r = _simular_y_analizar_opt(seed, p)
        resultados.append(r)
        print(
            f"destruidas={r['destruidas']:>6} ({r['pct_destruidas']:>5.2f}%)  "
            f"dist_vecino={r['dist_media_vecino_ly']:>7.1f} ly  "
            f"ratio={r['ratio_obs_poisson']:.3f}"
        )

    destruidas_arr = np.array([r["destruidas"] for r in resultados])
    pct_arr = np.array([r["pct_destruidas"] for r in resultados])
    dist_arr = np.array([r["dist_media_vecino_ly"] for r in resultados])
    ratio_arr = np.array([r["ratio_obs_poisson"] for r in resultados])

    summary = {
        "escenario": "optimista",
        "seeds": SEEDS,
        "n_runs": len(SEEDS),
        "N_c": N_c,
        "N_c_raw": N_c_raw,
        "optimistic_cap": p.optimistic_cap,
        "filtros": p.filtro_optimista,
        "destruidas": {
            "media": float(destruidas_arr.mean()),
            "std": float(destruidas_arr.std()),
            "min": int(destruidas_arr.min()),
            "max": int(destruidas_arr.max()),
            "cv_pct": float(destruidas_arr.std() / destruidas_arr.mean() * 100),
        },
        "pct_destruidas": {
            "media": float(pct_arr.mean()),
            "std": float(pct_arr.std()),
        },
        "dist_media_vecino_ly": {
            "media": float(dist_arr.mean()),
            "std": float(dist_arr.std()),
        },
        "ratio_obs_poisson": {
            "media": float(ratio_arr.mean()),
            "std": float(ratio_arr.std()),
        },
        "runs": resultados,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n--- Resumen optimista (media ± std) ---")
    print(f"  N civilizaciones:  {N_c:,} (cap={p.optimistic_cap:,}, raw={N_c_raw:,})")
    print(f"  Destruidas:        {summary['destruidas']['media']:.1f} ± {summary['destruidas']['std']:.1f}"
          f"  [min={summary['destruidas']['min']}, max={summary['destruidas']['max']}]"
          f"  CV={summary['destruidas']['cv_pct']:.1f}%")
    print(f"  % destruidas:      {summary['pct_destruidas']['media']:.2f}% ± {summary['pct_destruidas']['std']:.2f}%")
    print(f"  Dist. vecino:      {summary['dist_media_vecino_ly']['media']:.0f} ± {summary['dist_media_vecino_ly']['std']:.0f} ly")
    print(f"  Ratio Poisson:     {summary['ratio_obs_poisson']['media']:.3f} ± {summary['ratio_obs_poisson']['std']:.3f}")
    print(f"\nGuardado en: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
