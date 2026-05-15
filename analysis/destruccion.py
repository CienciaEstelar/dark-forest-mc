"""
Análisis de las destrucciones producidas por el Paso 5.
"""

from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ..common.io_utils import save_txt

def analizar_destrucciones(df_final: pd.DataFrame, out_dir: str | Path, dpi: int = 600) -> Tuple[Optional[Path], Dict]:
    """
    Analiza cuántas civilizaciones quedaron destruidas vs activas y su distribución espacial.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if df_final.empty or "estado" not in df_final.columns:
        return None, {}

    if "distancia_centro_2d" not in df_final.columns:
        df_final = df_final.copy()
        df_final["distancia_centro_2d"] = np.sqrt(df_final["posicion_x_ly"] ** 2 + df_final["posicion_y_ly"] ** 2)

    destruidas = df_final[df_final["estado"] == "destruida"]
    activas = df_final[df_final["estado"] == "activa"]

    stats = {
        "total": int(len(df_final)),
        "destruidas": int(len(destruidas)),
        "activas": int(len(activas)),
        "tasa_destruccion_pct": float(len(destruidas) / len(df_final) * 100.0) if len(df_final) else 0.0,
        "dist_media_destruidas": float(destruidas["distancia_centro_2d"].mean()) if not destruidas.empty else 0.0,
        "dist_media_activas": float(activas["distancia_centro_2d"].mean()) if not activas.empty else 0.0,
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # barras
    ax1.bar(["Activas", "Destruidas"], [len(activas), len(destruidas)], color=["green", "red"], alpha=0.7, edgecolor="black")
    ax1.set_title("Distribución por estado post Paso 5")
    ax1.set_ylabel("Nº de civilizaciones")
    for i, v in enumerate([len(activas), len(destruidas)]):
        ax1.text(i, v + max(1, int(len(df_final) * 0.01)), f"{v:,}", ha="center", va="bottom")

    # histo radial
    bins = np.linspace(0, 50000, 25)
    ax2.hist(activas["distancia_centro_2d"], bins=bins, alpha=0.6, label="Activas", color="green")
    ax2.hist(destruidas["distancia_centro_2d"], bins=bins, alpha=0.6, label="Destruidas", color="red")
    ax2.set_title("Distribución radial de destrucciones")
    ax2.set_xlabel("Distancia al centro galáctico (ly)")
    ax2.set_ylabel("Frecuencia")
    ax2.legend()

    out_png = out_dir / "analisis_destrucciones.png"
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

    save_txt(out_dir / "resumen_destrucciones.txt", "\n".join([f"{k}: {v}" for k, v in stats.items()]))

    return out_png, stats
