"""
Simulaciones de control sin dinámica DF (P_ataque = 0).

Calcula el cociente r_obs/P de control para aislar el efecto geométrico
de la ZGH del efecto dinámico del Bosque Oscuro.

La diferencia
    Δr = r_obs/P(DF) − r_obs/P(control)
cuantifica el efecto espacial neto de la dinámica DF:
  - Δr > 0 en régimen pesimista → DF dispersa supervivientes más allá de la ZGH
  - Δr < 0 en régimen optimista → DF concentra supervivientes sobre el nivel ZGH
  - Δr ≈ 0 → la inversión observada es artefacto geométrico (ZGH, no DF)

Uso:
    source ~/anaconda3/bin/activate
    # Se ejecuta directamente como script, desde cualquier directorio.
    # Resuelve la raiz del proyecto de forma relativa a su propia
    # ubicacion (scripts/../) via un symlink puente en un directorio
    # temporal (ver _pkg_bridge.py), sin depender de como se llame la
    # carpeta contenedora del repo:

    # Control pesimista (10 semillas):
    python scripts/control_multiseed.py --outdir ./output_control \\
        --df-results ./output_analisis/multiseed_results.json

    # Control + cálculo de Δr con semillas específicas:
    python scripts/control_multiseed.py --outdir ./output_control \\
        --seeds 42 7 13 99 256 1337 2024 2025 3 17 \\
        --df-results ./output_analisis/multiseed_results.json
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from _pkg_bridge import ensure_pkg_bridge

_REPO_ROOT = Path(__file__).resolve().parent.parent
ensure_pkg_bridge(_REPO_ROOT)

from bosque_oscuro.common.config import Parametros
from bosque_oscuro.sim.sociologia import normalizar_probabilidades
from bosque_oscuro.sim.espacio import generar_posiciones
from bosque_oscuro.sim.tiempos import generar_duraciones
from bosque_oscuro.sim.dinamica import paso5_bosque_oscuro
from bosque_oscuro.analysis.vecino import analizar_vecino_mas_cercano


# Sincronizado con multiseed.py:29 — comparación apareada paper §2.6 (FIX 2.3)
_DEFAULT_SEEDS = [42, 7, 13, 99, 256, 1337, 2024, 2025, 3, 17]


def _run_seed_control(seed: int, tmp_dir: Path, p: Parametros) -> dict:
    """Ejecuta una semilla con ataques desactivados; devuelve estadísticos espaciales."""
    N_hp = (p.num_estrellas
            * p.fraccion_con_planetas
            * p.planetas_zona_habitable_promedio)
    N_c = int(N_hp
              * p.filtro_pesimista["f_l"]
              * p.filtro_pesimista["f_i"]
              * p.filtro_pesimista["f_c"])

    from bosque_oscuro.sim.factory import crear_catalogo
    catalogo = crear_catalogo(N_c, p, seed=seed)

    # disable_attacks=True → ningún evento de destrucción; mide solo geometría ZGH
    fin, _ = paso5_bosque_oscuro(catalogo, p, disable_attacks=True)
    destruidas = int((fin["estado"] == "destruida").sum())
    activas_df = fin[fin["estado"] == "activa"].copy()

    seed_dir = tmp_dir / f"seed_{seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)
    _, stats = analizar_vecino_mas_cercano(activas_df, seed_dir, dpi=72, p=p)

    return {
        "seed":             seed,
        "destruidas":       destruidas,       # debe ser 0 en control
        "n_activas":        len(activas_df),
        "dist_vecino_media": round(float(stats.get("media", float("nan"))), 1),
        "ratio_obs_poisson": round(float(stats.get("ratio_obs_poisson", float("nan"))), 4),
    }


def _load_df_ratios(df_results_path: str) -> tuple[float, float]:
    """Carga media y std del ratio DF desde multiseed_results.json."""
    with open(df_results_path) as f:
        data = json.load(f)

    # Acepta distintas estructuras de multiseed_results.json
    if "ratio_obs_poisson" in data and "ratio_obs_poisson_std" in data:
        return float(data["ratio_obs_poisson"]), float(data["ratio_obs_poisson_std"])

    if "seeds_detalle" in data:
        ratios = [
            s.get("ratio_obs_poisson", float("nan"))
            for s in data["seeds_detalle"]
        ]
        ratios = [r for r in ratios if not np.isnan(r)]
        return float(np.mean(ratios)), float(np.std(ratios))

    # Intento en estadísticos directos
    keys_media = ["ratio_media", "ratio_mean", "cociente_obs_poisson_media"]
    keys_std   = ["ratio_std",   "ratio_stdev","cociente_obs_poisson_std"]
    r_mean = next((float(data[k]) for k in keys_media if k in data), None)
    r_std  = next((float(data[k]) for k in keys_std   if k in data), float("nan"))
    if r_mean is not None:
        return r_mean, r_std

    raise KeyError(
        f"No se encontró ratio_obs_poisson en {df_results_path}. "
        "Estructura inesperada del JSON."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Control multiseed sin dinámica DF — calcula Δr_obs/P"
    )
    parser.add_argument("--outdir",     default="./output_control",
                        help="Directorio de salida (default: ./output_control)")
    parser.add_argument("--seeds",      nargs="+", type=int, default=_DEFAULT_SEEDS,
                        help="Semillas Monte Carlo (default: 10 semillas estándar)")
    parser.add_argument("--df-results", default=None,
                        help="Path a multiseed_results.json con resultados DF completos")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    p = Parametros()
    normalizar_probabilidades(p)

    print(f"[control_multiseed] {len(args.seeds)} semillas, disable_attacks=True")
    print(f"[control_multiseed] N_c = {int(p.num_estrellas * p.fraccion_con_planetas * p.planetas_zona_habitable_promedio * p.filtro_pesimista['f_l'] * p.filtro_pesimista['f_i'] * p.filtro_pesimista['f_c'])}")

    control_results = []
    for seed in args.seeds:
        print(f"  seed={seed} ...", end=" ", flush=True)
        r = _run_seed_control(seed, outdir / "tmp", p)
        control_results.append(r)
        print(f"ratio={r['ratio_obs_poisson']:.4f}  destruidas={r['destruidas']}")

    ratios_ctrl = [
        r["ratio_obs_poisson"]
        for r in control_results
        if not np.isnan(r["ratio_obs_poisson"])
    ]
    r_ctrl_media = float(np.mean(ratios_ctrl))
    r_ctrl_std   = float(np.std(ratios_ctrl))

    summary: dict = {
        "escenario":               "pesimista_control_sin_DF",
        "n_seeds":                 len(control_results),
        "seeds":                   args.seeds,
        "ratio_obs_poisson_media": round(r_ctrl_media, 4),
        "ratio_obs_poisson_std":   round(r_ctrl_std,   4),
        "seeds_detalle":           control_results,
    }

    # ── Δr si se proveen resultados DF ────────────────────────────────────────
    if args.df_results:
        try:
            r_df_media, r_df_std = _load_df_ratios(args.df_results)
            delta_r     = r_df_media - r_ctrl_media
            delta_r_std = float(np.sqrt(r_df_std**2 + r_ctrl_std**2))
            sigma_ratio = abs(delta_r) / max(delta_r_std, 1e-9)

            if delta_r > 2 * delta_r_std:
                interpretacion = (
                    f"Δr = {delta_r:+.4f} ± {delta_r_std:.4f} ({sigma_ratio:.1f}σ). "
                    "El Bosque Oscuro produce dispersión adicional significativa "
                    "más allá de la geometría ZGH (régimen pesimista confirmado)."
                )
            elif delta_r < -2 * delta_r_std:
                interpretacion = (
                    f"Δr = {delta_r:+.4f} ± {delta_r_std:.4f} ({sigma_ratio:.1f}σ). "
                    "El Bosque Oscuro produce concentración adicional por encima "
                    "del nivel ZGH (efecto DF en régimen denso confirmado)."
                )
            else:
                interpretacion = (
                    f"Δr = {delta_r:+.4f} ± {delta_r_std:.4f} ({sigma_ratio:.1f}σ). "
                    "Efecto diferencial DF no distinguible del efecto geométrico ZGH "
                    "con las semillas evaluadas. "
                    "La inversión observada puede ser atribuible principalmente al perfil ZGH."
                )

            summary["r_obs_P_DF"]          = round(r_df_media, 4)
            summary["r_obs_P_df_std"]       = round(r_df_std,   4)
            summary["r_obs_P_control"]      = round(r_ctrl_media, 4)
            summary["r_obs_P_control_std"]  = round(r_ctrl_std,   4)
            summary["delta_r"]              = round(delta_r,      4)
            summary["delta_r_std"]          = round(delta_r_std,  4)
            summary["delta_r_sigma"]        = round(sigma_ratio,  2)
            summary["interpretacion_delta_r"] = interpretacion

            print(f"\n── Efecto diferencial DF ──────────────────────────────")
            print(f"  r_obs/P (DF)      = {r_df_media:.4f} ± {r_df_std:.4f}")
            print(f"  r_obs/P (control) = {r_ctrl_media:.4f} ± {r_ctrl_std:.4f}")
            print(f"  Δr                = {delta_r:+.4f} ± {delta_r_std:.4f}  ({sigma_ratio:.1f}σ)")
            print(f"\n  {interpretacion}")

        except Exception as exc:
            print(f"\nAdvertencia: no se pudo calcular Δr: {exc}")

    out_file = outdir / "control_multiseed_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nResultados guardados en {out_file}")


if __name__ == "__main__":
    main()
