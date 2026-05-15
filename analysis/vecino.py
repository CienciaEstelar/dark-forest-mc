"""
Análisis de distancia al vecino más cercano usando KDTree 3D.
Incluye comparación contra distribución Poisson homogénea en el mismo volumen.
"""

from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial import KDTree
from scipy.special import gamma
from scipy.stats import ks_1samp

from ..common.io_utils import save_txt
from ..common.tipos import DataFrame
from ..common.config import Parametros


def _poisson_nn_esperado(n: int, p: Parametros) -> float:
    """
    Distancia esperada al vecino más cercano bajo un proceso Poisson 3D homogéneo
    con la misma densidad de puntos que la simulación.

    Para n puntos en volumen V, la distancia esperada es:
        E[d_NN] = Γ(4/3) * (3 / (4π * ρ))^(1/3)
    donde ρ = n / V_eff.

    V_eff se aproxima como un disco galáctico:
        V_eff = π * R_gal² * 2 * H_eff
    con H_eff = 2 * escala_altura_disco (cubre ~86 % de la distribución exponencial).
    """
    R = float(p.radio_galaxia)
    H_eff = 2.0 * float(p.escala_altura_disco)
    V_eff = np.pi * R**2 * H_eff
    rho = n / V_eff
    return float(gamma(4.0 / 3.0) * (3.0 / (4.0 * np.pi * rho)) ** (1.0 / 3.0))


def comparar_con_poisson(dvc: np.ndarray, p: Parametros) -> Dict:
    """
    Compara la distribución observada de distancias al vecino más cercano
    con la distribución teórica esperada bajo un proceso Poisson 3D homogéneo.

    Métricas calculadas:
    - Densidad esperada ρ = N / V_eff
    - Distancia media esperada: d_esp = 0.5538 * (V/N)^(1/3)
      (Chandrasekhar 1943; Donnelly & Varian 1973)
    - Test de Kolmogorov-Smirnov unilateral contra la CDF Poisson:
        F(d) = 1 − exp(−4π/3 · ρ · d³)
    - p-valor del KS: p < 0.05 indica clustering significativo inconsistente
      con distribución aleatoria homogénea.

    V_eff se aproxima como disco galáctico: π · R² · 2 · H_eff
    con H_eff = 2 · escala_altura_disco.
    """
    n = len(dvc)
    R = float(p.radio_galaxia)
    H_eff = 2.0 * float(p.escala_altura_disco)
    V_eff = np.pi * R**2 * H_eff
    rho = n / V_eff

    d_esperada = 0.5538 * (V_eff / n) ** (1.0 / 3.0)

    def cdf_poisson_3d(d: np.ndarray) -> np.ndarray:
        return 1.0 - np.exp(-(4.0 * np.pi / 3.0) * rho * d**3)

    ks_stat, p_valor = ks_1samp(dvc, cdf_poisson_3d, alternative='greater')

    return {
        "rho_esperado_civs_ly3": float(rho),
        "V_efectivo_ly3": float(V_eff),
        "d_esperada_poisson_ly": float(d_esperada),
        "ks_estadistico": float(ks_stat),
        "ks_p_valor": float(p_valor),
        "clustering_significativo": bool(p_valor < 0.05),
        "interpretacion": (
            "Distribución espacial significativamente diferente de Poisson homogéneo "
            f"(KS={ks_stat:.3f}, p={p_valor:.4f})" if p_valor < 0.05
            else f"No se rechaza hipótesis Poisson homogéneo (KS={ks_stat:.3f}, p={p_valor:.4f})"
        ),
    }


def analizar_vecino_mas_cercano(
    df: DataFrame,
    out_dir: str | Path,
    dpi: int = 600,
    p: Optional[Parametros] = None,
) -> Tuple[Optional[Path], Dict]:
    """
    Calcula la distancia al vecino más cercano en 3D y guarda un histograma.

    Returns
    -------
    (ruta_png, stats_dict)
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if df.empty or len(df) < 2:
        return None, {}

    pts = df[["posicion_x_ly", "posicion_y_ly", "posicion_z_ly"]].to_numpy()
    kdt = KDTree(pts)
    # k=2 → el primer valor es 0 (la misma civ), el segundo es el vecino
    distancias, _ = kdt.query(pts, k=2)
    dvc = distancias[:, 1]

    poisson_esperado = _poisson_nn_esperado(len(dvc), p) if p is not None else None

    stats = {
        "media": float(dvc.mean()),
        "mediana": float(np.median(dvc)),
        "min": float(dvc.min()),
        "max": float(dvc.max()),
        "std": float(dvc.std()),
        "q25": float(np.quantile(dvc, 0.25)),
        "q75": float(np.quantile(dvc, 0.75)),
        "n": int(len(dvc)),
    }
    if poisson_esperado is not None:
        stats["poisson_esperado_ly"] = poisson_esperado
        stats["ratio_obs_poisson"] = float(dvc.mean() / poisson_esperado)
        ks_result = comparar_con_poisson(dvc, p)
        stats["ks_poisson"] = ks_result

    # gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(dvc, bins=50, color="skyblue", edgecolor="black", alpha=0.8)
    ax.axvline(stats["media"], color="red", ls="--", lw=2, label=f"Media obs.: {stats['media']:.0f} ly")
    ax.axvline(stats["mediana"], color="orange", ls="--", lw=2, label=f"Mediana obs.: {stats['mediana']:.0f} ly")
    if poisson_esperado is not None:
        ax.axvline(poisson_esperado, color="green", ls="-.", lw=2,
                   label=f"Poisson esperado: {poisson_esperado:.0f} ly")
    ax.set_title("Distancia al Vecino Más Cercano (3D) vs. Poisson Homogéneo")
    ax.set_xlabel("Distancia (años luz)")
    ax.set_ylabel("Frecuencia")
    ax.grid(alpha=0.3)
    ax.legend()

    out_png = out_dir / "distribucion_vecino_mas_cercano.png"
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    # guardar también texto resumen
    save_txt(out_dir / "resumen_vecino_mas_cercano.txt", "\n".join([f"{k}: {v}" for k, v in stats.items()]))

    return out_png, stats
